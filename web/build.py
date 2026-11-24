#!/usr/bin/env python3
"""把 wiki/ 編譯成靜態網站（輸出到 docs/）。只用 Python 標準函式庫。

用法（在專案根目錄）：
    python web/build.py            # 輸出到 docs/
    python web/build.py --out site # 輸出到其他資料夾
規格見 web/AGENTS.md。
"""
import argparse
import html
import json
import re
import os
import shutil
import stat
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from md import inline, parse_frontmatter, render, split_frontmatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
STATIC = Path(__file__).resolve().parent / "static"
SITE_NAME = "首爾旅遊攻略"
SPECIAL = {"index": "all.html", "overview": "index.html", "log": "log.html"}

CATEGORY_LABELS = {
    "itineraries": "行程範本", "areas": "區域", "markets": "市場",
    "brands": "品牌", "shopping": "購物地點", "must-buy": "必買",
    "food": "美食", "culture": "傳統文化", "practical": "實用資訊",
    "comparisons": "比較",
}
TYPE_LABELS = {
    "area": "區域", "restaurant": "餐廳", "dish": "料理", "market": "市場",
    "shop": "購物", "mall": "商場", "attraction": "景點", "experience": "體驗",
    "brand": "品牌", "must-buy": "必買", "practical": "實用資訊",
    "itinerary": "行程", "comparison": "比較",
}
CONF_LABELS = {"high": "可信度高", "medium": "可信度中", "low": "可信度低"}
STATUS_LABELS = {"open": "未解", "investigating": "研究中", "answered": "已解答"}
OP_LABELS = {"ingest": "收錄", "collect": "蒐集", "query": "查詢", "lint": "檢查", "refactor": "重組",
             "schema": "規則", "web": "網站"}

esc = html.escape


def force_writable(path):
    """清掉唯讀屬性。OneDrive 同步資料夾常被標成唯讀，Windows 會拒絕刪除。"""
    try:
        os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    except OSError:
        pass


def rmtree_force(path):
    """刪除資料夾；遇到唯讀檔案或資料夾時先解除唯讀再重試。"""
    def retry(func, p, _exc):
        force_writable(p)
        force_writable(os.path.dirname(p))
        func(p)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry)
    else:
        shutil.rmtree(path, onerror=retry)


# ---------------------------------------------------------------- 讀取 wiki

class Page:
    def __init__(self, path):
        self.path = path
        self.name = path.stem
        rel = path.relative_to(WIKI)
        self.cat = rel.parts[0] if len(rel.parts) > 1 else "misc"
        raw_fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        self.fm = parse_frontmatter(raw_fm)
        # 內文第一個 h1 由版型負責顯示，這裡移除
        self.body = re.sub(r"^\s*#\s+[^\n]*\n", "", body, count=1)
        self.title = self.fm.get("title") or self.name
        self.slug = re.sub(r"\s+", "-", self.name.strip())
        self.url = f"p/{self.slug}.html"
        self.summary = ""
        self.backlinks = set()

    def lst(self, key):
        v = self.fm.get(key, [])
        return v if isinstance(v, list) else [v] if v else []


def load_pages():
    pages = []
    for p in sorted(WIKI.rglob("*.md")):
        rel = p.relative_to(WIKI)
        if len(rel.parts) == 1 and p.stem in SPECIAL:
            continue
        if p.name.startswith("_"):
            continue
        pages.append(Page(p))
    seen = {}
    for pg in pages:
        if pg.slug.lower() in seen:
            sys.exit(f"錯誤：{pg.path} 與 {seen[pg.slug.lower()].path} 轉換後網址相同，請改檔名。")
        seen[pg.slug.lower()] = pg
    return pages


def read_special(name):
    p = WIKI / f"{name}.md"
    if not p.exists():
        return {}, ""
    raw_fm, body = split_frontmatter(p.read_text(encoding="utf-8"))
    return parse_frontmatter(raw_fm), re.sub(r"^\s*#\s+[^\n]*\n", "", body, count=1)


# ---------------------------------------------------------------- 連結解析

class Resolver:
    def __init__(self, pages):
        self.map = {}
        for pg in pages:  # 先放檔名與標題，再放別名（不覆蓋）
            for k in (pg.name, pg.title):
                self.map.setdefault(k.strip().lower(), pg)
        for pg in pages:
            for a in pg.lst("aliases"):
                self.map.setdefault(a.strip().lower(), pg)

    def page(self, target):
        return self.map.get(target.strip().lower())

    def for_root(self, root):
        def resolve(target):
            t = target.strip()
            if t.lower() in SPECIAL:
                label = {"index": "全部條目", "overview": "總覽", "log": "操作紀錄"}[t.lower()]
                return root + SPECIAL[t.lower()], label
            pg = self.page(t)
            if pg:
                return root + quote(pg.url), t
            return None, t
        return resolve


WIKILINK = re.compile(r"\[\[(.+?)\]\]")
CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def link_targets(text):
    out = []
    for m in WIKILINK.findall(CODE.sub("", text)):
        out.append(m.replace("\\|", "|").split("|")[0].split("#")[0].strip())
    return out


def plain_text(md_text):
    t = CODE.sub(" ", md_text)
    t = WIKILINK.sub(lambda m: m.group(1).replace("\\|", "|").split("|")[-1], t)
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"[#>*|`_]+|-{3,}", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- 版型

def cat_label(c):
    return CATEGORY_LABELS.get(c, c)


def badge(text, cls):
    return f'<span class="badge {cls}">{esc(text)}</span>'


def layout(title, root, body, cats, active="", toc=None, latest=""):
    nav_items = [("index.html", "首頁", "home"), ("all.html", "全部條目", "all"),
                 ("tags.html", "標籤", "tags"), ("log.html", "操作紀錄", "log")]
    nav = "".join(
        f'<li><a href="{root}{h}"{" aria-current=page" if a == active else ""}>{t}</a></li>'
        for h, t, a in nav_items)
    catnav = "".join(
        f'<li><a href="{root}c/{quote(c)}.html"{" aria-current=page" if active == "c:" + c else ""}>'
        f'{esc(cat_label(c))}<span class="count">{n}</span></a></li>'
        for c, n in cats)
    toc_html = ""
    if toc:
        items = "".join(f'<li class="l{lv}"><a href="#{hid}">{esc(t)}</a></li>' for lv, hid, t in toc)
        toc_html = f'<aside class="toc" aria-label="本頁目錄"><div class="toc-title">本頁目錄</div><ol>{items}</ol></aside>'
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {SITE_NAME}</title>
<link rel="stylesheet" href="{root}assets/style.css">
<script>try{{var t=localStorage.getItem("wiki-theme");if(t)document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
</head>
<body data-root="{root}">
<header class="topbar">
  <button class="menu-btn" type="button" aria-label="開啟選單" aria-expanded="false">☰</button>
  <a class="brand" href="{root}index.html">{SITE_NAME}</a>
  <button class="theme-btn" type="button" aria-label="切換深淺色模式" title="切換深淺色模式"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/></svg></button>
</header>
<div class="shell">
<nav class="sidebar" aria-label="網站導覽">
  <a class="brand side-brand" href="{root}index.html">{SITE_NAME}</a>
  <div class="search">
    <label for="q" class="sr-only">搜尋</label>
    <input id="q" type="search" placeholder="搜尋標題、別名、內文…（按 / ）" autocomplete="off">
    <ul id="results" class="results" hidden></ul>
  </div>
  <ul class="nav">{nav}</ul>
  <div class="nav-title">分類</div>
  <ul class="nav cats">{catnav}</ul>
</nav>
<main class="content" id="main">
{body}
<footer class="footer">內容最後更新：{esc(latest)} · 由 <code>web/build.py</code> 從 <code>wiki/</code> 產生</footer>
</main>
{toc_html}
</div>
<script src="{root}assets/search-index.js"></script>
<script src="{root}assets/app.js"></script>
</body>
</html>
"""


def page_card(pg, root):
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in pg.lst("tags")[:5])
    conf = pg.fm.get("confidence", "")
    meta = []
    if pg.fm.get("type"):
        meta.append(badge(TYPE_LABELS.get(pg.fm["type"], pg.fm["type"]), "type"))
    if conf in CONF_LABELS:
        meta.append(badge(CONF_LABELS[conf], f"conf-{conf}"))
    if pg.fm.get("status") in STATUS_LABELS:
        meta.append(badge(STATUS_LABELS[pg.fm["status"]], "status"))
    return f"""<li class="card">
  <a class="card-title" href="{root}{quote(pg.url)}">{esc(pg.title)}</a>
  <div class="card-meta">{''.join(meta)}<span class="date">{esc(pg.fm.get('last_updated', ''))}</span></div>
  <p class="card-sum">{inline(pg.summary, lambda t: (None, t)) if pg.summary else ''}</p>
  <div class="card-tags">{tags}</div>
</li>"""


# ---------------------------------------------------------------- 主程式

def main():
    ap = argparse.ArgumentParser(description="把 wiki/ 編譯成靜態網站")
    ap.add_argument("--out", default="docs", help="輸出資料夾（預設 docs）")
    args = ap.parse_args()
    out = (ROOT / args.out).resolve()
    if ROOT not in out.parents:
        sys.exit("輸出資料夾必須在專案內")

    pages = load_pages()
    res = Resolver(pages)
    broken = []

    # 一句話摘要：取自 index.md
    _, index_body = read_special("index")
    sums = {}
    for m in re.finditer(r"^\s*[-*]\s*\[\[([^\]|]+)(?:\|[^\]]*)?\]\]\s*[：:]\s*(.+)$", index_body, re.M):
        s = re.sub(r"[（(]\s*also\s*[:：].*?[）)]\s*$", "", m.group(2)).strip()
        sums[m.group(1).strip().lower()] = s
    for pg in pages:
        pg.summary = sums.get(pg.name.lower()) or sums.get(pg.title.lower()) or ""
        if not pg.summary:
            first = next((b for b in pg.body.split("\n\n") if b.strip() and not b.lstrip().startswith(("#", "|", ">", "-", "```"))), "")
            pg.summary = plain_text(first)[:120]

    # 反向連結
    for pg in pages:
        targets = link_targets(pg.body) + [t.strip("[] ") for t in pg.lst("related")]
        for t in targets:
            tp = res.page(t)
            if tp and tp is not pg:
                tp.backlinks.add(pg)

    # 分類統計
    order = list(CATEGORY_LABELS)
    by_cat = {}
    for pg in pages:
        by_cat.setdefault(pg.cat, []).append(pg)
    cats = sorted(by_cat, key=lambda c: (order.index(c) if c in order else 99, c))
    cat_counts = [(c, len(by_cat[c])) for c in cats]
    latest = max((pg.fm.get("last_updated", "") for pg in pages), default="")

    # 清空並準備輸出資料夾
    if out.exists():
        for child in out.iterdir():
            if child.is_dir():
                rmtree_force(child)
            else:
                force_writable(child)
                child.unlink()
    (out / "p").mkdir(parents=True, exist_ok=True)
    (out / "c").mkdir(exist_ok=True)
    (out / "assets").mkdir(exist_ok=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    for f in ("style.css", "app.js"):
        shutil.copy(STATIC / f, out / "assets" / f)

    def write(rel, text):
        (out / rel).write_text(text, encoding="utf-8")

    # ---- 條目頁
    for pg in pages:
        root = "../"
        resolve = res.for_root(root)
        bl = []
        body_html, toc = render(pg.body, resolve, bl)
        broken += [(pg.name, b) for b in bl]
        fm = pg.fm
        rows = []
        t = fm.get("type")
        badges = []
        if t:
            badges.append(badge(TYPE_LABELS.get(t, t), "type"))
        if fm.get("confidence") in CONF_LABELS:
            badges.append(badge(CONF_LABELS[fm["confidence"]], f"conf-{fm['confidence']}"))
        if fm.get("status") in STATUS_LABELS:
            badges.append(badge(STATUS_LABELS[fm["status"]], "status"))
        dates = " · ".join(x for x in (
            f"更新 {fm['last_updated']}" if fm.get("last_updated") else "",
            f"資料確認 {fm['checked']}" if fm.get("checked") else "") if x)
        if pg.lst("aliases"):
            rows.append(("別名", "、".join(esc(a) for a in pg.lst("aliases"))))
        for key, label in (("name_ko", "韓文"), ("brand_type", "類型"), ("style", "風格"),
                           ("area", "區域"), ("station", "交通"), ("hours", "時間"), ("price", "價格"),
                           ("stores", "門市")):
            v = fm.get(key)
            if v:
                txt = "、".join(v) if isinstance(v, list) else v
                rows.append((label, inline(txt, resolve)))
        if fm.get("arxiv"):
            a = esc(fm["arxiv"])
            rows.append(("arXiv", f'<a href="https://arxiv.org/abs/{a}" target="_blank" rel="noopener">{a}</a>'))
        if pg.lst("tags"):
            rows.append(("標籤", " ".join(
                f'<a class="tag" href="{root}tags.html#{quote("t-" + x)}">{esc(x)}</a>' for x in pg.lst("tags"))))
        if pg.lst("sources"):
            rows.append(("來源", "<br>".join(f"<code>{esc(s)}</code>" for s in pg.lst("sources"))))
        meta_rows = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)

        related = []
        for r in pg.lst("related"):
            tgt = r.strip("[] ").split("|")[0]
            related.append(f"<li>{inline('[[' + tgt + ']]', resolve)}</li>")
        backs = "".join(f'<li><a href="{root}{quote(b.url)}">{esc(b.title)}</a></li>'
                        for b in sorted(pg.backlinks, key=lambda x: x.title))
        extra = ""
        if related:
            extra += f'<section class="links"><h2>相關頁面</h2><ul>{"".join(related)}</ul></section>'
        extra += (f'<section class="links"><h2>反向連結 <span class="count">{len(pg.backlinks)}</span></h2>'
                  f'<ul>{backs or "<li class=muted>目前沒有其他頁面連到這裡</li>"}</ul></section>')

        body = f"""<nav class="crumbs" aria-label="麵包屑"><a href="{root}index.html">首頁</a> › <a href="{root}c/{quote(pg.cat)}.html">{esc(cat_label(pg.cat))}</a></nav>
<article>
<h1>{esc(pg.title)}</h1>
<div class="meta-badges">{''.join(badges)}<span class="date">{esc(dates)}</span></div>
{f'<table class="meta">{meta_rows}</table>' if meta_rows else ''}
<div class="prose">{body_html}</div>
</article>
{extra}"""
        write(f"p/{pg.slug}.html", layout(pg.title, root, body, cat_counts, "", toc, latest))

    # ---- 分類頁
    for c in cats:
        root = "../"
        lst = sorted(by_cat[c], key=lambda p: (p.fm.get("last_updated", ""), p.title), reverse=True)
        body = (f'<nav class="crumbs"><a href="{root}index.html">首頁</a> › 分類</nav>'
                f'<h1>{esc(cat_label(c))} <span class="count big">{len(lst)}</span></h1>'
                f'<ul class="cards">{"".join(page_card(p, root) for p in lst)}</ul>')
        write(f"c/{c}.html", layout(cat_label(c), root, body, cat_counts, "c:" + c, None, latest))

    # ---- 首頁
    root = ""
    ov_fm, ov_body = read_special("overview")
    ov_html, ov_toc = render(ov_body, res.for_root(root), [])
    sources = {s for pg in pages for s in pg.lst("sources")}
    _, log_body = read_special("log")
    entries = parse_log(log_body)
    recent = "".join(
        f'<li><span class="date">{esc(d)}</span>{badge(OP_LABELS.get(op, op), "op op-" + esc(op))}'
        f'<span>{esc(t)}</span></li>' for d, op, t, _ in entries[:5])
    tiles = "".join(f'<div class="tile"><div class="num">{v}</div><div class="lbl">{k}</div></div>' for k, v in (
        ("攻略頁面", len(pages)), ("資料來源檔", len(sources)), ("分類", len(cats)), ("最後更新", latest or "—")))
    catcards = "".join(
        f'<a class="catcard" href="c/{quote(c)}.html"><div class="catname">{esc(cat_label(c))}</div>'
        f'<div class="catcount">{len(by_cat[c])} 頁</div><ul>'
        + "".join(f"<li>{esc(p.title)}</li>" for p in sorted(by_cat[c], key=lambda p: p.fm.get('last_updated', ''), reverse=True)[:3])
        + "</ul></a>" for c in cats)
    body = f"""<section class="hero">
<h1>{SITE_NAME}</h1>
<p class="lead">給台灣旅客的首爾通用攻略：美食、購物逛街、傳統文化與市場、韓國必買。由 AI 依 Karpathy 的 LLM Wiki 模式，從網路資料持續整理而成。</p>
<div class="tiles">{tiles}</div>
</section>
<section class="overview"><h2 class="sec">攻略總覽</h2><div class="prose">{ov_html}</div></section>
<section><h2 class="sec">分類</h2><div class="catgrid">{catcards}</div></section>
<section><h2 class="sec">最近紀錄</h2><ul class="recent">{recent}</ul><p><a href="log.html">查看全部紀錄 →</a></p></section>"""
    write("index.html", layout("首頁", root, body, cat_counts, "home", None, latest))

    # ---- 全部條目（index.md）
    idx_html, idx_toc = render(index_body, res.for_root(root), broken_idx := [])
    broken += [("index", b) for b in broken_idx]
    write("all.html", layout("全部條目", root,
                             f'<h1>全部條目</h1><div class="prose index-page">{idx_html}</div>',
                             cat_counts, "all", idx_toc, latest))

    # ---- 標籤頁
    tagmap = {}
    for pg in pages:
        for t in pg.lst("tags"):
            tagmap.setdefault(t, []).append(pg)
    cloud = " ".join(f'<a class="tag" href="#{quote("t-" + t)}">{esc(t)} <span class="count">{len(v)}</span></a>'
                     for t, v in sorted(tagmap.items(), key=lambda kv: (-len(kv[1]), kv[0])))
    groups = "".join(
        f'<section class="taggroup" id="{esc("t-" + t)}"><h2>{esc(t)}</h2><ul>'
        + "".join(f'<li><a href="{quote(p.url)}">{esc(p.title)}</a> <span class="muted">· {esc(cat_label(p.cat))}</span></li>'
                  for p in sorted(v, key=lambda p: p.title))
        + "</ul></section>" for t, v in sorted(tagmap.items()))
    write("tags.html", layout("標籤", root, f'<h1>標籤</h1><div class="cloud">{cloud}</div>{groups}',
                              cat_counts, "tags", None, latest))

    # ---- 紀錄頁
    items = []
    for d, op, t, b in entries:
        bh, _ = render(b, res.for_root(root), [])
        items.append(f'<li class="logentry"><div class="loghead"><span class="date">{esc(d)}</span>'
                     f'{badge(OP_LABELS.get(op, op), "op op-" + esc(op))}<strong>{esc(t)}</strong></div>'
                     f'<div class="prose">{bh}</div></li>')
    write("log.html", layout("操作紀錄", root,
                             f'<h1>操作紀錄</h1><p class="muted">新的在上。原始檔：<code>wiki/log.md</code>（只追加不改寫）。</p>'
                             f'<ol class="loglist">{"".join(items)}</ol>', cat_counts, "log", None, latest))

    # ---- 搜尋索引
    idx = [{
        "t": pg.title, "u": pg.url, "c": cat_label(pg.cat),
        "a": pg.lst("aliases"), "g": pg.lst("tags"), "s": plain_text(pg.summary),
        "x": plain_text(pg.body)[:4000],
    } for pg in pages]
    write("assets/search-index.js", "window.WIKI_INDEX=" + json.dumps(idx, ensure_ascii=False) + ";\n")

    print(f"完成：{len(pages)} 個條目、{len(cats)} 個分類 → {out.relative_to(ROOT)}/")
    if broken:
        print(f"斷鏈 {len(broken)} 個：")
        for src, b in broken:
            print(f"  {src} → [[{b}]]")
    else:
        print("沒有斷鏈。")


def parse_log(text):
    """回傳 [(日期, 操作, 標題, 內文)]，新的在前。"""
    parts = re.split(r"^##\s+", text, flags=re.M)
    out = []
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        m = re.match(r"\[(.+?)\]\s*(\S+)\s*\|\s*(.+)", head.strip())
        if m:
            out.append((m.group(1), m.group(2), m.group(3).strip(), body.strip()))
        else:
            out.append(("", "", head.strip(), body.strip()))
    return list(reversed(out))


if __name__ == "__main__":
    main()
