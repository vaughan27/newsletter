"""Cover generation.

Both sources (first PDF page, or an uploaded image) go through the same crop so every
cover on the homepage has an identical size and aspect ratio. The ratio and width come
from settings (COVER_ASPECT_WIDTH / COVER_ASPECT_HEIGHT / COVER_WIDTH_PX).
"""

from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.core.errors import ServiceError

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
_MAX_RENDER_ZOOM = 4.0


def fit_to_cover(img: Image.Image, *, anchor_top: bool = False) -> Image.Image:
    """Scale and crop to the configured cover size (no distortion, no letterboxing).

    For a slide that already has the cover ratio nothing is lost. For anything else the
    overflow is trimmed evenly (or from the bottom when anchor_top, which suits tall pages
    whose title sits at the top).
    """
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        # Flatten transparency onto white rather than black.
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, rgba).convert("RGB")
    centering = (0.5, 0.0) if anchor_top else (0.5, 0.5)
    return ImageOps.fit(img, settings.cover_size, method=Image.Resampling.LANCZOS, centering=centering)


def _save_jpeg(img: Image.Image, dest: Path) -> None:
    img.save(dest, "JPEG", quality=88, optimize=True, progressive=True)


def validate_pdf(pdf_file: Path) -> int:
    """Return the page count, or raise ServiceError if the PDF can't be used."""
    try:
        with fitz.open(pdf_file) as doc:
            if doc.needs_pass:
                raise ServiceError("Password-protected PDFs are not supported.", 400)
            if doc.page_count < 1:
                raise ServiceError("The PDF has no pages.", 400)
            return doc.page_count
    except ServiceError:
        raise
    except Exception as exc:
        raise ServiceError("The PDF could not be read. It may be corrupted.", 400) from exc


def render_first_page(pdf_file: Path) -> Image.Image:
    target_width, _ = settings.cover_size
    try:
        with fitz.open(pdf_file) as doc:
            page = doc[0]
            zoom = min(max(target_width / page.rect.width, 1.0), _MAX_RENDER_ZOOM)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    except Exception as exc:
        raise ServiceError("Could not render the first page of the PDF.", 400) from exc


def write_cover_from_pdf(pdf_file: Path, dest: Path) -> None:
    _save_jpeg(fit_to_cover(render_first_page(pdf_file), anchor_top=True), dest)


def write_cover_from_image(data: bytes, dest: Path) -> None:
    try:
        with Image.open(BytesIO(data)) as probe:
            if probe.format not in ALLOWED_IMAGE_FORMATS:
                raise ServiceError("Cover image must be a JPEG, PNG or WebP file.", 400)
        with Image.open(BytesIO(data)) as img:
            img.load()
            cover = fit_to_cover(img)
    except ServiceError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise ServiceError("The cover image could not be read.", 400) from exc
    _save_jpeg(cover, dest)
