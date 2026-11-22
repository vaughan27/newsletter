from io import BytesIO

import pytest
from PIL import Image

from app.core.config import settings
from app.core.errors import ServiceError
from app.services import covers


def _png_bytes(size: tuple[int, int], color=(200, 30, 30), mode="RGB") -> bytes:
    buf = BytesIO()
    Image.new(mode, size, color).save(buf, "PNG")
    return buf.getvalue()


@pytest.mark.parametrize("size", [(3000, 2000), (800, 1600), (1280, 720), (500, 500)])
def test_custom_image_is_cropped_to_cover_ratio(tmp_path, size):
    dest = tmp_path / "cover.jpg"
    covers.write_cover_from_image(_png_bytes(size), dest)
    with Image.open(dest) as out:
        assert out.size == settings.cover_size
        assert out.format == "JPEG"


def test_transparent_png_is_flattened_onto_white(tmp_path):
    dest = tmp_path / "cover.jpg"
    covers.write_cover_from_image(_png_bytes((400, 225), (0, 0, 0, 0), "RGBA"), dest)
    with Image.open(dest) as out:
        r, g, b = out.getpixel((10, 10))
        assert min(r, g, b) > 240


def test_non_image_is_rejected(tmp_path):
    with pytest.raises(ServiceError):
        covers.write_cover_from_image(b"definitely not an image", tmp_path / "c.jpg")


def test_unsupported_format_is_rejected(tmp_path):
    buf = BytesIO()
    Image.new("RGB", (50, 50)).save(buf, "GIF")
    with pytest.raises(ServiceError):
        covers.write_cover_from_image(buf.getvalue(), tmp_path / "c.jpg")


def test_pdf_first_slide_becomes_cover(tmp_path):
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "deck.pdf"
    doc = fitz.open()
    for label in ("Slide one", "Slide two"):
        page = doc.new_page(width=960, height=540)  # a 16:9 "slide"
        page.insert_text((60, 270), label, fontsize=48)
    doc.save(pdf)
    doc.close()

    assert covers.validate_pdf(pdf) == 2
    dest = tmp_path / "cover.jpg"
    covers.write_cover_from_pdf(pdf, dest)
    with Image.open(dest) as out:
        assert out.size == settings.cover_size


def test_corrupt_pdf_is_rejected(tmp_path):
    pytest.importorskip("fitz")
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.7\nthis is not really a pdf")
    with pytest.raises(ServiceError):
        covers.validate_pdf(bad)
