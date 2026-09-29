"""Plot image upload + serving (M035): the only untrusted-bytes entry.

Validation pipeline (order matters, spec §Security):
authz → size cap (read ``max+1``) → magic-byte sniff → pixel cap
(pre-decode) → ``verify()`` → write ``{uuid}.{ext}`` under
``settings.upload_dir`` → row. The client's ``Content-Type`` and
filename are never trusted: the stored type comes from the sniff and
the stored name from ``uuid4``.

Reads reuse the plot's ownership matrix (``_authorized_plot``), so an
image is exactly as visible as its plot: owner/admin/officer read,
owner/admin write, non-owner farmer → 404 (no oracle).
"""

from __future__ import annotations

import asyncio
import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel
from sqlalchemy import func, select

from src.api.deps import CurrentUserDep, SessionDep
from src.api.v1.plots import _authorized_plot
from src.core.config import get_settings
from src.core.errors import (
    ImageTooLarge,
    InvalidImage,
    NotFound,
    PayloadTooLarge,
    UnsupportedMediaType,
)
from src.models import PlotImage

router = APIRouter(prefix="/farms/{farm_id}/plots/{plot_id}/images", tags=["images"])

ALLOWED_FORMATS: dict[str, str] = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
CONTENT_TYPES: dict[str, str] = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}


class ImageRead(BaseModel):
    """One stored upload as clients see it (M049 renders ``url``)."""

    id: uuid.UUID
    plot_id: uuid.UUID
    content_type: str
    size_bytes: int
    original_name: str | None
    created_at: datetime
    url: str


class ImageList(BaseModel):
    items: list[ImageRead]
    total: int
    limit: int
    offset: int


def _to_read(row: PlotImage, farm_id: uuid.UUID, plot_id: uuid.UUID) -> ImageRead:
    return ImageRead(
        id=row.id,
        plot_id=row.plot_id,
        content_type=row.content_type,
        size_bytes=row.size_bytes,
        original_name=row.original_name,
        created_at=row.created_at,
        url=f"/api/v1/farms/{farm_id}/plots/{plot_id}/images/{row.id}",
    )


def _display_name(raw: str | None) -> str | None:
    """Basename only, capped — display text, never a path component."""
    if not raw:
        return None
    cleaned = raw.replace("\\", "/").split("/")[-1][:255].strip()
    return cleaned or None


def _decode(data: bytes) -> str:
    """Sniff → validate; returns the Pillow format name or raises."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = (image.format or "").upper()
            if image_format not in ALLOWED_FORMATS:
                raise UnsupportedMediaType("Only JPEG, PNG and WebP images are accepted.")
            width, height = image.size
            if width * height > get_settings().upload_max_pixels:
                raise ImageTooLarge(
                    f"Images must be at most {get_settings().upload_max_pixels} pixels."
                )
            try:
                image.verify()
            except (OSError, ValueError) as exc:
                raise InvalidImage("The image file is corrupt or truncated.") from exc
            return image_format
    except UnidentifiedImageError as exc:
        raise UnsupportedMediaType("The file is not a recognized image.") from exc
    except Image.DecompressionBombError as exc:
        raise ImageTooLarge("The image dimensions are too large.") from exc
    except OSError as exc:
        # header-level truncation raises OSError from Image.open itself
        raise InvalidImage("The image file is corrupt or truncated.") from exc


@router.post("", response_model=ImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUserDep,
    file: Annotated[UploadFile, File()],
) -> ImageRead:
    """Store one validated photo for the plot (owner/admin; officer → 403,
    non-owner farmer → 404 via parent-plot authz)."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=True)
    settings = get_settings()
    data = await file.read(settings.upload_max_bytes + 1)
    if len(data) > settings.upload_max_bytes:
        raise PayloadTooLarge(f"Images must be at most {settings.upload_max_bytes} bytes.")
    image_format = _decode(data)
    stored_name = f"{uuid.uuid4().hex}.{ALLOWED_FORMATS[image_format]}"
    directory = Path(settings.upload_dir)
    await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
    await asyncio.to_thread((directory / stored_name).write_bytes, data)

    row = PlotImage(
        plot_id=plot_id,
        uploaded_by=current.id,
        original_name=_display_name(file.filename),
        content_type=CONTENT_TYPES[image_format],
        size_bytes=len(data),
        stored_name=stored_name,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_read(row, farm_id, plot_id)


@router.get("", response_model=ImageList)
async def list_images(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUserDep,
) -> ImageList:
    """List the plot's images (same read authz as the plot itself)."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=False)
    total = (
        await session.scalar(
            select(func.count()).select_from(PlotImage).where(PlotImage.plot_id == plot_id)
        )
        or 0
    )
    rows = (
        (
            await session.execute(
                select(PlotImage)
                .where(PlotImage.plot_id == plot_id)
                .order_by(PlotImage.created_at, PlotImage.id)
            )
        )
        .scalars()
        .all()
    )
    return ImageList(
        items=[_to_read(row, farm_id, plot_id) for row in rows],
        total=total,
        limit=len(rows),
        offset=0,
    )


@router.get("/{image_id}", response_class=FileResponse)
async def get_image(
    farm_id: uuid.UUID,
    plot_id: uuid.UUID,
    image_id: uuid.UUID,
    session: SessionDep,
    current: CurrentUserDep,
) -> FileResponse:
    """Serve the stored bytes inline (read authz; an image from another
    plot → 404). Missing file on disk → 404 rather than a 500."""
    await _authorized_plot(session, farm_id, plot_id, current, for_write=False)
    row = await session.scalar(
        select(PlotImage).where(PlotImage.id == image_id, PlotImage.plot_id == plot_id)
    )
    if row is None:
        raise NotFound("Image not found.")
    path = Path(get_settings().upload_dir) / row.stored_name
    if not path.is_file():
        raise NotFound("Image not found.")
    return FileResponse(
        path,
        media_type=row.content_type,
        headers={"X-Content-Type-Options": "nosniff"},
    )
