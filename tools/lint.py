#!/usr/bin/env python3
"""LLM Wiki 健康檢查：找出斷鏈、孤兒頁、過胖／過瘦頁面，並產生 wiki/_backlinks.json。

用法：python3 tools/lint.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
SPECIAL = {"index", "log", "overview"}
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")


def page_names():
    pages = {}
    for p in WIKI.rglob("*.md"):
        pages[p.stem] = p
    return pages


def main():
    pages = page_names()
    lower = {k.lower(): k for k in pages}
    backlinks = {name: [] for name in pages}
    broken = []

    for name, path in pages.items():
        text = CODE_RE.sub("", path.read_text(encoding="utf-8"))
        for target in set(LINK_RE.findall(text)):
            target = target.strip()
            key = lower.get(target.lower())
            if key is None:
                broken.append((str(path.relative_to(ROOT)), target))
            elif key != name:
                backlinks[key].append(name)

    orphans = [n for n, srcs in backlinks.items()
               if not srcs and n not in SPECIAL]
    sizes = {n: len(p.read_text(encoding="utf-8").splitlines())
             for n, p in pages.items() if n not in SPECIAL}
    fat = sorted((n, l) for n, l in sizes.items() if l > 150)
    thin = sorted((n, l) for n, l in sizes.items() if l < 15)

    (WIKI / "_backlinks.json").write_text(
        json.dumps({k: sorted(v) for k, v in sorted(backlinks.items())},
                   ensure_ascii=False, indent=2),
        encoding="utf-8")

    print(f"頁面數：{len(pages)}（不含 index/log/overview：{len(sizes)}）")
    print(f"\n斷鏈（{len(broken)}）：")
    for src, t in broken:
        print(f"  {src} → [[{t}]]")
    print(f"\n孤兒頁（{len(orphans)}）：")
    for n in sorted(orphans):
        print(f"  {n}")
    print(f"\n過胖 >150 行（{len(fat)}）：")
    for n, l in fat:
        print(f"  {n}（{l} 行）")
    print(f"\n過瘦 <15 行（{len(thin)}）：")
    for n, l in thin:
        print(f"  {n}（{l} 行）")
    top = sorted(backlinks.items(), key=lambda kv: -len(kv[1]))[:10]
    print("\n連入最多的頁面：")
    for n, srcs in top:
        if srcs:
            print(f"  {n}（{len(srcs)}）")
    print("\n已更新 wiki/_backlinks.json")


if __name__ == "__main__":
    main()
