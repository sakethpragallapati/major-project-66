"""Load a denial letter from text, PDF or image and clean the text.

PDF pages with a text layer are read directly. Scanned pages and image files
are read with OCR (RapidOCR, an ONNX model that runs offline).
"""

import io
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif"}
MIN_TEXT_CHARS = 40     # a PDF page with less text than this is treated as scanned
SCANNED_TEXT_CHARS = 300  # ...and so is one with a little more text over a page-sized image
OCR_DPI = 300
OCR_MAX_WIDTH = 2000
OCR_TARGET_WIDTH = 2300   # scans narrower than this are enlarged before OCR
OCR_MAX_UPSCALE = 3.0
OCR_MAX_SIDE = 4000
OCR_GOOD_SCORE = 0.85     # below this mean confidence the page may be rotated
OCR_MIN_SKEW = 0.5        # degrees of tilt from which a page is levelled and read again
MERGED_RUN = 12           # a box with this many letters in a row has probably lost spaces
OCR_SPACE_PAD = 0.2       # margin, as a share of the box height, for reading such a box again


def clean_text(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("–", "-").replace("—", "-").replace("’", "'")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    # Re-join a sentence that a PDF or a scan wrapped onto the next line.
    text = re.sub(r"(?<=[a-z,;])[ ]?\n(?=[a-z(])", " ", text)
    text = re.sub(r"(?<=\w)-\n(?=\w)", "-", text)          # "BLK-\nMAX" -> "BLK-MAX"
    text = re.sub(r"(?<![A-Za-z])(Rs\.?|INR|₹) ?\n(?=\d)", r"\1 ", text)   # "Rs\n164,000"
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def repair_ocr_text(text):
    """Fix the OCR model's usual slips: words run together, "l" or "i" read for "I"
    in capitals, "o" read for "0" in numbers, and spaces lost around numbers and titles."""
    from .respace import respace

    text = re.sub(r"(?<=\b[A-Z]{2})l\b", "I", text)        # "BMl" -> "BMI"
    text = re.sub(r"(?<=[A-Z]{2})[il](?=[A-Z]{2})", "I", text)   # "GASTROENTERiTIS"
    text = re.sub(r"\b(Rs\.?|INR)(?=\d)", r"\1 ", text)     # "Rs3.95.000", "INR5,00,000"
    text = re.sub(r"\b\d[\d,.oO]*\b", lambda m: re.sub(r"[oO]", "0", m[0]), text)   # "45,0o0"
    text = re.sub(r"(?<=\d,)\s+(?=\d{2,3}\b)", "", text)    # "1, 12,000"
    text = re.sub(r"\b([a-z]{2,})(?=\d)", r"\1 ", text)    # "on19September2024"
    text = re.sub(r"(\d)(?=[a-z]{3,})", r"\1 ", text)       # "CLM-2024-70215under", "8weeks"
    text = re.sub(r"(?<=[a-z])(?=[A-Z]{2,5}[-/]\d)", " ", text)   # "ClaimCLM-2024-33410"
    text = re.sub(r"\bDear(?=[A-Z])", "Dear ", text)         # "DearMs.Anjali"
    text = re.sub(r"\b(Mrs|Mr|Ms|Dr|Smt)\.(?=[A-Z])", r"\1. ", text)
    text = re.sub(r",(?=[A-Za-z])", ", ", text)              # "Medcity,Kochi"
    return respace(text)


@lru_cache(maxsize=1)
def _ocr_engine():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError("OCR needs the rapidocr-onnxruntime package") from exc
    # The default max_side_len of 2000 shrinks the enlarged scan back down, which
    # undoes the enlargement and costs word spacing.
    return RapidOCR(max_side_len=OCR_MAX_SIDE)


def _lines_from_boxes(result):
    """Group OCR word boxes into lines by vertical position, then order left to right."""
    boxes = []
    for box, text, _score in result or []:
        ys = [p[1] for p in box]
        boxes.append(((min(ys) + max(ys)) / 2, max(ys) - min(ys), min(p[0] for p in box), text))
    return _join_lines(boxes)


def _join_lines(boxes):
    """boxes: (y centre, height, x, text). Boxes on one row become one line."""
    boxes = sorted(boxes)
    lines, current, current_y = [], [], None
    for y, h, x, text in boxes:
        if current and abs(y - current_y) > max(h, 8) * 0.6:
            lines.append(current)
            current = []
        current.append((x, text))
        current_y = y if len(current) == 1 else current_y
    if current:
        lines.append(current)
    return "\n".join(" ".join(t for _, t in sorted(line)) for line in lines)


def _open_pages(image):
    """PIL images of every page in an image file (a TIFF fax may hold several)."""
    from PIL import Image, ImageOps, ImageSequence

    img = Image.open(io.BytesIO(image) if isinstance(image, bytes) else image)
    pages = []
    for frame in ImageSequence.Iterator(img):
        frame = ImageOps.exif_transpose(frame)      # phone photos store their rotation in EXIF
        if frame.mode in ("RGBA", "LA", "P"):
            # A transparent background would turn black and hide the text.
            rgba = frame.convert("RGBA")
            white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            frame = Image.alpha_composite(white, rgba)
        pages.append(frame.convert("L"))
    return pages


def _prepare(img):
    """Enlarge low-resolution scans: on small text the OCR model tends to drop
    the spaces between words."""
    import numpy as np
    from PIL import Image

    if isinstance(img, (bytes, str, Path)):
        img = _open_pages(img)[0]
    if img.width < OCR_TARGET_WIDTH:
        scale = min(OCR_MAX_UPSCALE, OCR_TARGET_WIDTH / img.width)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    return np.array(img.convert("RGB"))


def _run_ocr(arr):
    # The text-angle classifier is off: on upright letters it flips some lines
    # (an italic subject line, a line under a table border) and they are lost.
    # Whole-page rotation is handled in _ocr_page instead. The detector settings
    # are passed every time because RapidOCR keeps the last ones it was given.
    result, _ = _ocr_engine()(arr, use_cls=False, box_thresh=0.5, unclip_ratio=1.6, text_score=0.5)
    result = _restore_spaces(arr, result or [])
    chars = sum(len(t) for _, t, _ in result)
    weight = sum(float(s) * len(t) for _, t, s in result)
    # On a page turned sideways the text boxes stand upright. RapidOCR turns each one
    # and reads it, so the words are right but the lines come out in the wrong order.
    tall = sum(len(t) for box, t, _ in result
               if (max(p[1] for p in box) - min(p[1] for p in box)) > 1.5 * (max(p[0] for p in box)
                                                                             - min(p[0] for p in box)))
    return result, weight, (weight / chars if chars else 0.0), (tall / chars if chars else 0.0)


def _restore_spaces(arr, result):
    """Read again, with a margin round it, every box that has a long run of letters
    and no space ("VASUNDHRASHAHI"): the recogniser drops word spaces on a tight crop.
    The new reading is kept only if it has the same letters plus spaces."""
    import numpy as np

    todo = [i for i, (_, text, _) in enumerate(result) if re.search(r"[A-Za-z]{%d,}" % MERGED_RUN, text)]
    if not todo:
        return result
    crops = []
    for i in todo:
        xs, ys = [p[0] for p in result[i][0]], [p[1] for p in result[i][0]]
        pad = max(4, round(OCR_SPACE_PAD * (max(ys) - min(ys))))
        y0, y1 = max(0, int(min(ys)) - pad), min(arr.shape[0], int(max(ys)) + pad)
        x0, x1 = max(0, int(min(xs)) - pad), min(arr.shape[1], int(max(xs)) + pad)
        crops.append(np.ascontiguousarray(arr[y0:y1, x0:x1]))
    reread, _ = _ocr_engine().text_rec(crops)
    out = [list(r) for r in result]
    for i, (text, score) in zip(todo, reread):
        old = out[i][1]
        if text.replace(" ", "") == old.replace(" ", "") and text.count(" ") > old.count(" "):
            out[i][1] = text
    return out


def _ocr_page(img):
    """OCR one page, turning it if it was scanned sideways or upside down."""
    import numpy as np

    from PIL import Image

    arr = _prepare(img)
    result, weight, mean, tall = _run_ocr(arr)
    sideways = tall > 0.5
    if sideways or mean < OCR_GOOD_SCORE or weight < MIN_TEXT_CHARS:
        # A sideways reading is never kept; an upside-down page reads as low-confidence text.
        best, upright = (0.0 if sideways else weight), arr
        for k in ((1, 3) if sideways else (2, 1, 3)):     # quarter turns anticlockwise
            turned_arr = np.ascontiguousarray(np.rot90(arr, k))
            turned, w, _, t = _run_ocr(turned_arr)
            if t <= 0.5 and w > best * 1.2:
                result, best, upright = turned, w, turned_arr
        arr = upright
    # A photographed page is often a little crooked, which mixes up the rows; level it.
    angle = _skew(result)
    if abs(angle) >= OCR_MIN_SKEW:
        level = Image.fromarray(arr).rotate(angle, expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)
        result = _run_ocr(np.array(level))[0]
    return _lines_from_boxes(result)


def _skew(result):
    """Median slope of the text lines in degrees, positive when they fall to the right."""
    import math

    angles = sorted(math.degrees(math.atan2(box[1][1] - box[0][1], box[1][0] - box[0][0]))
                    for box, text, _ in result
                    if len(text) >= 5 and abs(box[1][0] - box[0][0]) > 3 * abs(box[3][1] - box[0][1]))
    return angles[len(angles) // 2] if len(angles) >= 3 else 0.0


def ocr_image(image):
    """OCR an image given as a path or as encoded bytes; every page of a multi-page TIFF."""
    return "\n".join(_ocr_page(page) for page in _open_pages(image))


def _pdf_page_text(page):
    """Text of a PDF page, one line per row. Table cells are separate blocks in a
    PDF, so a label and its value would otherwise come out on different lines."""
    boxes = [((y0 + y1) / 2, y1 - y0, x0, w) for x0, y0, x1, y1, w, *_ in page.get_text("words")]
    return _join_lines(boxes)


def _image_cover(page):
    """Share of the page covered by images."""
    area = abs(page.rect.width * page.rect.height) or 1
    return sum(abs((i["bbox"][2] - i["bbox"][0]) * (i["bbox"][3] - i["bbox"][1]))
               for i in page.get_image_info()) / area


def _pdf_text(data=None, path=None):
    import fitz  # PyMuPDF

    pages, ocr_pages = [], 0
    with (fitz.open(stream=data, filetype="pdf") if data is not None else fitz.open(path)) as doc:
        for page in doc:
            text = _pdf_page_text(page)
            n = len(text.strip())
            # A scan with a stamp or a printed footer has a little text over a page-sized image.
            if n < MIN_TEXT_CHARS or (n < SCANNED_TEXT_CHARS and _image_cover(page) > 0.5):
                images = page.get_images()
                if len(images) == 1 and not page.rotation:
                    # A scanned page is one embedded image: OCR it at its own resolution,
                    # since resampling it makes the model drop the spaces between words.
                    scan = ocr_image(doc.extract_image(images[0][0])["image"])
                else:
                    zoom = min(OCR_DPI / 72, OCR_MAX_WIDTH / page.rect.width)
                    scan = ocr_image(page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).tobytes("png"))
                text = "\n".join(t for t in (text, repair_ocr_text(scan)) if t.strip()) if n else \
                    repair_ocr_text(scan)
                ocr_pages += 1
            pages.append(text)
    return "\n".join(pages), ocr_pages


def load_bytes(data, filename):
    """Text of an uploaded file. Returns (text, how it was read)."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text, ocr_pages = _pdf_text(data=data)
        method = f"pdf ({ocr_pages} page(s) by OCR)" if ocr_pages else "pdf text layer"
    elif suffix in IMAGE_SUFFIXES:
        text, method = repair_ocr_text(ocr_image(data)), "image OCR"
    else:
        text, method = data.decode("utf-8", errors="replace"), "text"
    text = clean_text(text)
    if not text:
        raise ValueError(f"no text could be read from {filename}")
    return text, method


def load_letter(path):
    path = Path(path)
    return load_bytes(path.read_bytes(), path.name)[0]
