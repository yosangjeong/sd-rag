"""Merge a statute body HWPX and its annex (별표) HWPX files into one HWPX.

law.go.kr exports a statute as one body .hwpx plus one file per annex. To keep
"one statute = one file" for every format (PDF already bundles annexes), this
appends each annex as a new section of the body document.

Every HWPX file has its own numbered style tables in Contents/header.xml
(fonts, border fills, char/para shapes, tabs, numberings, styles, memo shapes)
and its text refers to them by number (charPrIDRef="3", ...). Annex number 3
is not body number 3, so each annex's table entries are appended to the body's
tables under new numbers and every reference in the annex is rewritten — like
relocating symbols when linking object files. Fonts and styles that already
exist in the body under the same name are reused instead of duplicated.

    uv run --no-project --python 3.12 --with lxml python data/scripts/hwpx_merge.py \
        OUT.hwpx BODY.hwpx ANNEX1.hwpx [ANNEX2.hwpx ...]
"""

import copy
import re
import sys
import zipfile
from pathlib import Path

from lxml import etree

NS = {
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
}
HH = "{%s}" % NS["hh"]

# refList children in schema order: (list element, item element, map key)
REF_LISTS = [
    ("borderFills", "borderFill", "borderFill"),
    ("charProperties", "charPr", "charPr"),
    ("tabProperties", "tabPr", "tabPr"),
    ("numberings", "numbering", "numbering"),
    ("bullets", "bullet", "bullet"),
    ("paraProperties", "paraPr", "paraPr"),
    ("styles", "style", "style"),
    ("memoProperties", "memoPr", "memoPr"),
]
REF_ORDER = (
    ["fontfaces"] + [r[0] for r in REF_LISTS] + ["trackChanges", "trackChangeAuthors"]
)

# reference attribute -> which id map it points into
ATTR_MAP = {
    "borderFillIDRef": "borderFill",
    "charPrIDRef": "charPr",
    "paraPrIDRef": "paraPr",
    "tabPrIDRef": "tabPr",
    "styleIDRef": "style",
    "nextStyleIDRef": "style",
    "outlineShapeIDRef": "numbering",
    "memoShapeIDRef": "memoPr",
}
NO_REF = {"0", "4294967295"}  # 0xFFFFFFFF is HWPX's "no reference" sentinel
FONT_LANGS = ["hangul", "latin", "hanja", "japanese", "other", "symbol", "user"]
XML_DECL = b'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'


def tostring(root) -> bytes:
    return XML_DECL + etree.tostring(root, encoding="UTF-8")


def ref_list(head, name, create=False):
    rl = head.find("hh:refList", NS)
    el = rl.find(f"hh:{name}", NS)
    if el is None and create:
        el = etree.Element(HH + name, itemCnt="0")
        # insert after the nearest preceding list that exists
        idx = 0
        for i, child in enumerate(rl):
            tag = etree.QName(child).localname
            if tag in REF_ORDER and REF_ORDER.index(tag) < REF_ORDER.index(name):
                idx = i + 1
        rl.insert(idx, el)
    return el


def next_id(items) -> int:
    return max((int(e.get("id")) for e in items), default=-1) + 1


def merge_fonts(base_head, ann_head) -> dict:
    """Return {lang: {annex_font_id: base_font_id}}, appending fonts the body lacks."""
    maps = {}
    base_ff = {
        f.get("lang"): f
        for f in ref_list(base_head, "fontfaces").findall("hh:fontface", NS)
    }
    for ff in ref_list(ann_head, "fontfaces").findall("hh:fontface", NS):
        lang = ff.get("lang")
        target = base_ff[lang]
        by_face = {f.get("face"): f.get("id") for f in target.findall("hh:font", NS)}
        m = {}
        for font in ff.findall("hh:font", NS):
            if font.get("face") in by_face:
                m[font.get("id")] = by_face[font.get("face")]
                continue
            new = copy.deepcopy(font)
            new.set("id", str(next_id(target.findall("hh:font", NS))))
            target.append(new)
            by_face[font.get("face")] = new.get("id")
            m[font.get("id")] = new.get("id")
        target.set("fontCnt", str(len(target.findall("hh:font", NS))))
        maps[lang.lower()] = m
    return maps


def remap(root, maps, font_maps, unmapped):
    """Rewrite every style reference under root using the id maps."""
    for e in root.iter():
        if not isinstance(e.tag, str):
            continue
        local = etree.QName(e).localname
        for attr, key in ATTR_MAP.items():
            v = e.get(attr)
            if v is None:
                continue
            if v in maps[key]:
                e.set(attr, maps[key][v])
            elif v not in NO_REF:
                unmapped.add(f"{attr}={v}")
        if local == "heading" and e.get("type") in ("OUTLINE", "NUMBER", "BULLET"):
            key = "bullet" if e.get("type") == "BULLET" else "numbering"
            v = e.get("idRef")
            if v in maps[key]:
                e.set("idRef", maps[key][v])
            elif v not in NO_REF:
                unmapped.add(f"heading.idRef={v}")
        if local == "fontRef":
            for lang in FONT_LANGS:
                v = e.get(lang)
                if v is not None:
                    e.set(lang, font_maps[lang].get(v, v))
        v = e.get("binaryItemIDRef")
        if v:
            if v in maps["bin"]:
                e.set("binaryItemIDRef", maps["bin"][v])
            else:
                unmapped.add(f"binaryItemIDRef={v}")


def merge_bindata(hpf: str, az: zipfile.ZipFile, prefix: str) -> tuple[str, dict, dict]:
    """Copy the annex's embedded files (images, fonts) under a unique prefix.

    Returns the updated body manifest, {old item id: new item id}, and
    {new zip path: bytes} for the files to add.
    """
    ann_hpf = az.read("Contents/content.hpf").decode("utf-8")
    bin_map, files = {}, {}
    for item in re.findall(r'<opf:item\b[^>]*\bhref="BinData/[^"]*"[^>]*/>', ann_hpf):
        old_id = re.search(r'\bid="([^"]*)"', item).group(1)
        href = re.search(r'\bhref="([^"]*)"', item).group(1)
        new_id, new_href = (
            f"{prefix}{old_id}",
            f"BinData/{prefix}{href[len('BinData/') :]}",
        )
        new_item = item.replace(f'id="{old_id}"', f'id="{new_id}"', 1).replace(
            f'href="{href}"', f'href="{new_href}"', 1
        )
        hpf = hpf.replace("</opf:manifest>", new_item + "</opf:manifest>")
        bin_map[old_id] = new_id
        files[new_href] = az.read(href)
    return hpf, bin_map, files


def merge_header(base_head, ann_head, bin_map: dict) -> tuple[dict, dict]:
    font_maps = merge_fonts(base_head, ann_head)
    maps = {key: {} for _, _, key in REF_LISTS}
    maps["bin"] = bin_map
    base_style_names = {
        s.get("name"): s.get("id")
        for s in ref_list(base_head, "styles").findall("hh:style", NS)
    }
    new_items = []
    # first pass: assign ids so cross-references inside the header can be rewritten
    for list_name, item_name, key in REF_LISTS:
        src = ref_list(ann_head, list_name)
        if src is None:
            continue
        dst = ref_list(base_head, list_name, create=True)
        nid = next_id(dst.findall(f"hh:{item_name}", NS))
        for item in src.findall(f"hh:{item_name}", NS):
            if key == "style" and item.get("name") in base_style_names:
                maps[key][item.get("id")] = base_style_names[item.get("name")]
                continue
            maps[key][item.get("id")] = str(nid)
            new = copy.deepcopy(item)
            new.set("id", str(nid))
            new_items.append((dst, new))
            nid += 1
    unmapped: set[str] = set()
    for dst, new in new_items:
        remap(new, maps, font_maps, unmapped)
        dst.append(new)
    for list_name, item_name, _ in REF_LISTS:
        dst = ref_list(base_head, list_name)
        if dst is not None:
            dst.set("itemCnt", str(len(dst.findall(f"hh:{item_name}", NS))))
    ff = ref_list(base_head, "fontfaces")
    ff.set("itemCnt", str(len(ff.findall("hh:fontface", NS))))
    if unmapped:
        print("  warning: unmapped header refs", sorted(unmapped))
    return maps, font_maps


def merge(out: Path, body: Path, annexes: list[Path]) -> None:
    bz = zipfile.ZipFile(body)
    base_head = etree.fromstring(bz.read("Contents/header.xml"))
    hpf = bz.read("Contents/content.hpf").decode("utf-8")
    n_sections = len(
        [n for n in bz.namelist() if re.match(r"Contents/section\d+\.xml$", n)]
    )
    new_files: dict[str, bytes] = {}

    for idx, ann in enumerate(annexes, start=1):
        az = zipfile.ZipFile(ann)
        hpf, bin_map, bin_files = merge_bindata(hpf, az, prefix=f"annex{idx}_")
        new_files.update(bin_files)
        ann_head = etree.fromstring(az.read("Contents/header.xml"))
        maps, font_maps = merge_header(base_head, ann_head, bin_map)
        for sec_name in sorted(
            (n for n in az.namelist() if re.match(r"Contents/section\d+\.xml$", n)),
            key=lambda n: int(re.search(r"\d+", n).group()),
        ):
            sec = etree.fromstring(az.read(sec_name))
            unmapped: set[str] = set()
            remap(sec, maps, font_maps, unmapped)
            if unmapped:
                print(f"  warning: {ann.name}: unmapped section refs", sorted(unmapped))
            name = f"section{n_sections}"
            new_files[f"Contents/{name}.xml"] = tostring(sec)
            hpf = hpf.replace(
                "</opf:manifest>",
                f'<opf:item id="{name}" href="Contents/{name}.xml" media-type="application/xml"/></opf:manifest>',
            )
            hpf = hpf.replace(
                "</opf:spine>", f'<opf:itemref idref="{name}"/></opf:spine>'
            )
            n_sections += 1

    base_head.set("secCnt", str(n_sections))

    with zipfile.ZipFile(out, "w") as oz:
        for info in bz.infolist():
            if info.filename == "Contents/header.xml":
                data = tostring(base_head)
            elif info.filename == "Contents/content.hpf":
                data = hpf.encode("utf-8")
            else:
                data = bz.read(info.filename)
            oz.writestr(info, data, compress_type=info.compress_type)
        for name, data in new_files.items():
            oz.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    out, body, *annexes = (Path(a) for a in sys.argv[1:])
    merge(out, body, annexes)
    print(f"wrote {out} ({len(annexes)} annex(es) appended)")


if __name__ == "__main__":
    main()
