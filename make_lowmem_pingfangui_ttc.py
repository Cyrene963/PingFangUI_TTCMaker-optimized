#!/usr/bin/env python3
"""
Low-memory PingFangUI.ttc generator for iPad / a-Shell.

Key idea:
1. Generate each renamed subfont one by one.
2. Save intermediate TTFs to disk instead of keeping all fonts in RAM.
3. Optionally skip final TTC merge with --no-merge.

This avoids the original script's huge memory blow-up from deepcopy(base_font)
for every subfont plus one-shot in-memory TTCollection assembly.
"""

import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ensure_fonttools():
    try:
        import fontTools  # noqa: F401
    except ImportError:
        print("正在安装 fonttools，请稍候...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fonttools", "-q"], check=True)
        print("安装完成")


ensure_fonttools()

from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection
from fontTools.ttLib.tables._n_a_m_e import NameRecord


def parse_args():
    p = argparse.ArgumentParser(description="Low-memory PingFangUI TTC maker")
    p.add_argument("font", help="Source font path (TTF/OTF/TTC)")
    p.add_argument("--names", default="names.json", help="Path to names.json")
    p.add_argument("--out", default="PingFangUI.ttc", help="Output TTC path")
    p.add_argument("--tmp-dir", default="pingfangui_parts", help="Directory for intermediate subfonts")
    p.add_argument("--no-merge", action="store_true", help="Only generate intermediate subfonts, skip final TTC merge")
    p.add_argument("--keep-temp", action="store_true", help="Keep intermediate files after merge")
    return p.parse_args()


def load_base_font(path: Path):
    try:
        return TTFont(str(path))
    except Exception:
        col = TTCollection(str(path))
        if not col.fonts:
            raise RuntimeError("TTC file has no subfonts")
        print("检测到 TTC 格式，使用第 1 个子字体")
        return col.fonts[0]


def rewrite_name_table(font, records):
    name_table = font["name"]
    name_table.names = []
    for rec in records:
        nr = NameRecord()
        nr.nameID = rec["nameID"]
        nr.platformID = rec["platformID"]
        nr.platEncID = rec["platEncID"]
        nr.langID = rec["langID"]
        value = rec["value"]
        try:
            nr.string = value.encode("utf-16-be")
        except Exception:
            nr.string = bytes.fromhex(value)
        name_table.names.append(nr)


def generate_intermediates(base_font_path: Path, names_list, tmp_dir: Path):
    tmp_dir.mkdir(parents=True, exist_ok=True)
    total = len(names_list)
    generated = []
    for idx, records in enumerate(names_list, 1):
        print(f"生成子字体 {idx}/{total} ...")
        base_font = load_base_font(base_font_path)
        font = copy.deepcopy(base_font)
        rewrite_name_table(font, records)
        out_file = tmp_dir / f"{idx:03d}.ttf"
        font.save(str(out_file))
        generated.append(out_file)
    return generated


def merge_to_ttc(parts, out_path: Path):
    fonts = []
    total = len(parts)
    for idx, part in enumerate(parts, 1):
        print(f"载入中间子字体 {idx}/{total} 用于合并 ...")
        fonts.append(TTFont(str(part)))
    collection = TTCollection()
    collection.fonts = fonts
    collection.save(str(out_path))
    if not out_path.exists():
        raise RuntimeError("最终 TTC 未生成")
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"完成：{out_path}（{size_mb:.1f} MB）")


def main():
    args = parse_args()
    font_path = Path(args.font).expanduser().resolve()
    names_path = Path(args.names).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    tmp_dir = Path(args.tmp_dir).expanduser().resolve()

    if not font_path.exists():
        raise SystemExit(f"找不到字体文件：{font_path}")
    if not names_path.exists():
        raise SystemExit(f"找不到 names.json：{names_path}")

    names_list = json.loads(names_path.read_text(encoding="utf-8"))
    print(f"共需生成 {len(names_list)} 个子字体")
    print(f"源字体：{font_path}")
    print(f"中间目录：{tmp_dir}")

    parts = generate_intermediates(font_path, names_list, tmp_dir)

    if args.no_merge:
        print("--no-merge 已启用：仅生成中间子字体，不合并 TTC")
        return

    merge_to_ttc(parts, out_path)

    if not args.keep_temp:
        print("清理中间文件...")
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
