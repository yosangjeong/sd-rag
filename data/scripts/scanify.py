"""Make a synthetic scan of PDF pages: what a page looks like after printing and scanning.

Each page is rendered (pypdfium2), then degraded the way office scans are: grayscale,
a slight skew, blur, sensor noise, washed-out contrast, JPEG compression. The pages
are assembled into an image-only PDF: no text layer, so parse.py flags every page
needs_ocr. The source page's text (pypdf) is written next to it as ground truth.

Everything random is drawn from random.Random(f"{seed}:{page}"), noise included, so
the same arguments give the same images.

    cd backend && uv run python ../data/scripts/scanify.py SRC.pdf OUT.pdf \\
        --pages 1-3,7 [--profile office|poor] [--seed 0]

writes OUT.pdf and OUT.truth.json ({"<page>": "<source text>"}; 1-based pages of SRC).
"""

import argparse
import io
import json
import random
import time
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageChops, ImageEnhance, ImageFilter
from pypdf import PdfReader

PROFILES = {
    # a decent office copier / scanner
    "office": {
        "dpi": 200,
        "skew": 1.0,
        "blur": (0.4, 0.9),
        "noise": 18,
        "contrast": 0.85,
        "jpeg": 55,
    },
    # a bad one: low resolution, crooked, smudged, heavily compressed
    "poor": {"dpi": 150, "skew": 2.5, "blur": (0.8, 1.3), "noise": 36, "contrast": 0.7, "jpeg": 35},
}


def parse_pages(spec: str) -> list[int]:
    pages: list[int] = []
    for part in spec.split(","):
        a, _, b = part.partition("-")
        pages += range(int(a), int(b or a) + 1)
    return pages


def degrade(img: Image.Image, rng: random.Random, p: dict) -> Image.Image:
    img = img.convert("L")
    img = img.rotate(rng.uniform(-p["skew"], p["skew"]), Image.BICUBIC, fillcolor=255)
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(*p["blur"])))
    img = ImageEnhance.Contrast(img).enhance(p["contrast"])
    # uniform noise in [-amp, amp], from rng so it is reproducible (Image.effect_noise is not)
    amp = p["noise"]
    noise = Image.frombytes("L", img.size, rng.randbytes(img.size[0] * img.size[1]))
    noise = noise.point(lambda v: 128 + (v - 128) * amp // 128)
    img = ImageChops.add(img, noise, scale=1.0, offset=-128)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=p["jpeg"])
    return Image.open(io.BytesIO(buf.getvalue()))


def scan(src: Path, out: Path, pages: list[int], profile: str = "office", seed: int = 0) -> dict:
    p = PROFILES[profile]
    pdf = pdfium.PdfDocument(src)
    reader = PdfReader(src)
    images, truth = [], {}
    for n in pages:
        img = pdf[n - 1].render(scale=p["dpi"] / 72).to_pil()
        images.append(degrade(img, random.Random(f"{seed}:{n}"), p))
        truth[str(n)] = reader.pages[n - 1].extract_text() or ""
    out.parent.mkdir(parents=True, exist_ok=True)
    fixed = time.strptime("2026-01-01", "%Y-%m-%d")  # Pillow stamps "now" otherwise
    images[0].save(
        out, "PDF", save_all=True, append_images=images[1:], resolution=p["dpi"],
        creationDate=fixed, modDate=fixed,
    )  # fmt: skip
    out.with_suffix(".truth.json").write_text(
        json.dumps(truth, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return truth


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--pages", required=True, help="1-based, e.g. 1-3,7")
    ap.add_argument("--profile", choices=PROFILES, default="office")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    scan(a.src, a.out, parse_pages(a.pages), a.profile, a.seed)
    print(f"wrote {a.out} ({a.pages}, {a.profile})")


if __name__ == "__main__":
    main()
