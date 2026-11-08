"""Build out/candle_board_viewer.html from the per-part STLs in out/parts.

Usage: python3 tools/build_viewer.py
Each STL is quantised to int16 (5 µm steps, +-163 mm range), base64 encoded,
and inlined into tools/viewer_template.html at the __MESH__ marker.
"""
import base64
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS = ROOT / "out" / "parts"
TEMPLATE = ROOT / "tools" / "viewer_template.html"
OUTPUT = ROOT / "out" / "candle_board_viewer.html"
SCALE = 200.0  # must match the divisor in the template's decoder


def read_stl(path: Path) -> list[float]:
    raw = path.read_bytes()
    if raw[:5] == b"solid" and b"facet" in raw[:300]:
        return [float(v) for m in re.finditer(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", raw) for v in m.groups()]
    count = struct.unpack("<I", raw[80:84])[0]
    pts: list[float] = []
    for i in range(count):
        off = 84 + i * 50 + 12
        pts.extend(struct.unpack("<9f", raw[off:off + 36]))
    return pts


def main() -> None:
    mesh = {}
    for stl in sorted(PARTS.glob("*.stl")):
        pts = read_stl(stl)
        packed = struct.pack(f"<{len(pts)}h", *(int(round(v * SCALE)) for v in pts))
        mesh[stl.stem] = base64.b64encode(packed).decode()
        print(f"{stl.stem}: {len(pts) // 9} triangles")
    html = TEMPLATE.read_text().replace("__MESH__", json.dumps(mesh))
    OUTPUT.write_text(html)
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
