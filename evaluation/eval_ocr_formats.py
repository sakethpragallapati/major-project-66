"""Intake on the same letters delivered as different files.

The hand-written held-out letters (evaluation/heldout_letters.json, not used for
tuning) are rendered as the files people actually upload, read back through the
loader (OCR where needed) and scored against their truth:

    png_clean        200 dpi scan
    jpg_low_res      100 dpi, heavy JPEG compression
    photo_skewed     phone photo: turned 2.5 degrees, grey paper, slight blur
    sideways         page scanned at 90 degrees
    upside_down      page scanned at 180 degrees
    pdf_scanned      PDF holding only the page image
    pdf_text_layer   PDF with real text
    tiff_two_pages   fax: the letter split over two TIFF pages

    python -m evaluation.eval_ocr_formats
"""

import io
import json
import sys
import textwrap
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from denial_ai.graph import Pipeline  # noqa: E402
from denial_ai.intake.loader import load_bytes  # noqa: E402

HELDOUT = ROOT / "evaluation" / "heldout_letters.json"
OUT = ROOT / "evaluation" / "results"
FONT = "arial.ttf"   # looked up in the system font folder


def _lines(text, width=95):
    out = []
    for line in text.split("\n"):
        out += textwrap.wrap(line, width) or [""]
    return out


def _page(lines, width=1700, size=26, paper=255):
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(FONT, size)
    step = int(size * 1.5)
    img = Image.new("L", (width, 160 + step * len(lines)), paper)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((100, 80 + i * step), line, font=font, fill=0)
    return img


def _save(img, fmt, **kw):
    buf = io.BytesIO()
    img.save(buf, format=fmt, **kw)
    return buf.getvalue()


def render(text, variant):
    """(file bytes, file name) for one letter in one form."""
    from PIL import Image, ImageFilter

    lines = _lines(text)
    if variant == "png_clean":
        return _save(_page(lines), "PNG"), "letter.png"
    if variant == "jpg_low_res":
        return _save(_page(lines, width=850, size=13), "JPEG", quality=35), "letter.jpg"
    if variant == "photo_skewed":
        img = _page(lines, paper=232).rotate(2.5, expand=True, fillcolor=200, resample=Image.BICUBIC)
        return _save(img.filter(ImageFilter.GaussianBlur(0.8)), "JPEG", quality=70), "photo.jpg"
    if variant == "sideways":
        return _save(_page(lines).rotate(90, expand=True), "PNG"), "sideways.png"
    if variant == "upside_down":
        return _save(_page(lines).rotate(180), "PNG"), "upside_down.png"
    if variant == "tiff_two_pages":
        half = len(lines) // 2
        first, second = _page(lines[:half]), _page(lines[half:])
        return _save(first, "TIFF", save_all=True, append_images=[second]), "fax.tiff"

    import fitz
    doc = fitz.open()
    if variant == "pdf_scanned":
        png = _save(_page(lines), "PNG")
        page = doc.new_page()
        page.insert_image(page.rect, stream=png)
    else:                                                          # pdf_text_layer
        page = doc.new_page()
        for i, line in enumerate(lines):
            page.insert_text((50, 60 + i * 15), line, fontsize=10, fontname="helv")
    return doc.tobytes(), "letter.pdf"


VARIANTS = ["png_clean", "jpg_low_res", "photo_skewed", "sideways", "upside_down", "pdf_scanned",
            "pdf_text_layer", "tiff_two_pages"]


def main():
    letters = json.loads(HELDOUT.read_text(encoding="utf-8"))
    pipe = Pipeline(use_langgraph=False)
    report, rows = {}, []
    for variant in ["text"] + VARIANTS:
        ok = n = cat_ok = 0
        seconds = []
        for letter in letters:
            truth = {k: v for k, v in letter["truth"].items() if k != "category"}
            started = time.perf_counter()
            if variant == "text":
                text, method = letter["text"], "text"
            else:
                text, method = load_bytes(*render(letter["text"], variant))
            case = pipe.run(text=text)
            seconds.append(time.perf_counter() - started)
            errors = {k: {"gold": v, "pred": getattr(case.entities, k)} for k, v in truth.items()
                      if getattr(case.entities, k) != v}
            ok += len(truth) - len(errors)
            n += len(truth)
            cat_ok += case.triage.primary_category == letter["truth"]["category"]
            rows.append({"variant": variant, "letter": letter["id"], "read_method": method, "errors": errors})
        report[variant] = {"field_accuracy": round(ok / n, 4), "category_accuracy": round(cat_ok / len(letters), 4),
                           "mean_seconds": round(sum(seconds) / len(seconds), 1)}
        r = report[variant]
        print(f"  {variant:16s} fields {r['field_accuracy']:.3f}  category {r['category_accuracy']:.3f}"
              f"  {r['mean_seconds']:5.1f}s per letter")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ocr_formats.json").write_text(json.dumps({"summary": report, "letters": rows}, indent=2,
                                                     ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Results in {OUT / 'ocr_formats.json'}")


if __name__ == "__main__":
    main()
