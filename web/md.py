"""零依賴 Markdown 轉 HTML 轉換器（LLM Wiki 專用）。

支援：標題、段落、粗體、斜體、行內程式碼、程式碼區塊、引用（含 ⚠️ / 💡 提示框）、
巢狀清單、核取方塊、表格、水平線、連結、圖片、[[wikilink]]。
所有文字都會先做 HTML escape，內容中的 HTML 不會被執行。

用法：
    html, toc = render(markdown_text, resolve)
resolve(target) 回傳 (href 或 None, 預設顯示文字)。
"""
import html as _html
import re

__all__ = ["render", "inline", "split_frontmatter", "parse_frontmatter"]

# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text):
    """回傳 (frontmatter 原始字串, 內文)。"""
    text = text.lstrip("﻿")
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.S)
        if m:
            return m.group(1), text[m.end():]
    return "", text


def _split_list(s):
    items, buf, quote, depth = [], "", None, 0
    for ch in s:
        if quote:
            if ch == quote:
                quote = None
            else:
                buf += ch
            continue
        if ch in "\"'" and not buf.strip():
            quote = ch
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            items.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        items.append(buf.strip())
    return [i for i in items if i]


def parse_frontmatter(raw):
    """簡單 YAML：一行一個 key，值為字串或單行 [a, b] 清單。"""
    data = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        val = re.sub(r"\s+#\s.*$", "", val)  # 去掉行尾註解
        if val.startswith("[") and val.endswith("]"):
            data[key] = _split_list(val[1:-1])
        else:
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key] = val
    return data

# ---------------------------------------------------------------- inline

_ph_re = re.compile(r"\x00(\d+)\x00")


def inline(text, resolve, broken=None):
    """把單行 Markdown 轉成 HTML。broken 為 list 時會收集找不到的連結。"""
    store = []

    def keep(h):
        store.append(h)
        return f"\x00{len(store) - 1}\x00"

    # 行內程式碼
    text = re.sub(r"`([^`]+)`", lambda m: keep(f"<code>{_html.escape(m.group(1))}</code>"), text)

    # [[wikilink]]（支援 \| 跳脫）
    def wl(m):
        inner = m.group(1).replace("\\|", "|")
        target, _, label = inner.partition("|")
        target = target.strip()
        page = target.split("#")[0].strip() or target
        href, default = resolve(page)
        shown = _html.escape(label.strip() or default or page)
        if href:
            return keep(f'<a class="wl" href="{_html.escape(href)}">{shown}</a>')
        if broken is not None:
            broken.append(page)
        return keep(f'<span class="wl-broken" title="尚未建立：{_html.escape(page)}">{shown}</span>')

    text = re.sub(r"\[\[(.+?)\]\]", wl, text)

    # 圖片與連結
    def img(m):
        return keep(f'<img src="{_html.escape(m.group(2))}" alt="{_html.escape(m.group(1))}" loading="lazy">')

    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", img, text)

    def link(m):
        url = m.group(2)
        if re.match(r"^\s*javascript:", url, re.I):
            url = "#"
        ext = ' target="_blank" rel="noopener"' if re.match(r"^https?://", url) else ""
        return keep(f'<a href="{_html.escape(url)}"{ext}>{inline(m.group(1), resolve, broken)}</a>')

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, text)

    # 裸網址
    text = re.sub(r"(?<![\"'=])(https?://[^\s<>）)]+)",
                  lambda m: keep(f'<a href="{_html.escape(m.group(1))}" target="_blank" rel="noopener">{_html.escape(m.group(1))}</a>'),
                  text)

    text = _html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![\*\w])", r"<em>\1</em>", text)
    text = text.replace("（我的推測）", '<span class="guess">（我的推測）</span>')

    while _ph_re.search(text):
        text = _ph_re.sub(lambda m: store[int(m.group(1))], text)
    return text

# ---------------------------------------------------------------- blocks

_list_re = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_heading_re = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_hr_re = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
_table_sep_re = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def _split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells, buf, depth, i = [], "", 0, 0
    while i < len(line):
        ch = line[i]
        if line.startswith("[[", i):
            depth += 1
            buf += "[["
            i += 2
            continue
        if line.startswith("]]", i) and depth:
            depth -= 1
            buf += "]]"
            i += 2
            continue
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            buf += "\\|"
            i += 2
            continue
        if ch == "|" and depth == 0:
            cells.append(buf.strip())
            buf = ""
        else:
            buf += ch
        i += 1
    cells.append(buf.strip())
    return [c.replace("\\|", "|") if "[[" not in c else c for c in cells]


def _is_block_start(line, nxt):
    return bool(
        not line.strip()
        or line.startswith("```")
        or _heading_re.match(line)
        or _hr_re.match(line)
        or line.lstrip().startswith(">")
        or _list_re.match(line)
        or (line.lstrip().startswith("|") and nxt is not None and _table_sep_re.match(nxt))
    )


def _render_list(items, resolve, broken):
    """items: [(indent, ordered, text)]，依縮排產生巢狀清單。"""
    out, i = [], 0

    def build(i, base):
        ordered = items[i][1]
        tag = "ol" if ordered else "ul"
        parts = []
        while i < len(items) and items[i][0] >= base:
            indent, _, text = items[i]
            if indent > base:
                sub, i = build(i, indent)
                if parts:
                    parts[-1] = parts[-1][:-5] + sub + "</li>"
                else:
                    parts.append(f"<li>{sub}</li>")
                continue
            m = re.match(r"^\[([ xX])\]\s+(.*)$", text)
            if m:
                checked = " checked" if m.group(1) in "xX" else ""
                body = f'<input type="checkbox" disabled{checked}> {inline(m.group(2), resolve, broken)}'
                parts.append(f'<li class="task">{body}</li>')
            else:
                parts.append(f"<li>{inline(text, resolve, broken)}</li>")
            i += 1
        return f"<{tag}>{''.join(parts)}</{tag}>", i

    while i < len(items):
        html_, i = build(i, items[i][0])
        out.append(html_)
    return "".join(out)


def render(text, resolve, broken=None, _toc=None, _counter=None):
    """回傳 (html, toc)。toc 為 [(level, id, 純文字)]，只收 h2、h3。"""
    toc = _toc if _toc is not None else []
    counter = _counter if _counter is not None else [0]
    lines = text.replace("\r\n", "\n").split("\n")
    out, i, n = [], 0, len(lines)

    while i < n:
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < n else None

        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):
            lang = line[3:].strip()
            buf, i = [], i + 1
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{_html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{_html.escape(chr(10).join(buf))}</code></pre>")
            continue

        m = _heading_re.match(line)
        if m:
            level = len(m.group(1))
            body = inline(m.group(2), resolve, broken)
            counter[0] += 1
            hid = f"s{counter[0]}"
            if level in (2, 3):
                plain = re.sub(r"<[^>]+>", "", body)
                toc.append((level, hid, _html.unescape(plain)))
            out.append(f'<h{level} id="{hid}">{body}</h{level}>')
            i += 1
            continue

        if _hr_re.match(line):
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith("|") and nxt is not None and _table_sep_re.match(nxt):
            head = _split_row(line)
            aligns = []
            for c in _split_row(nxt):
                c = c.strip()
                aligns.append("center" if c.startswith(":") and c.endswith(":")
                              else "right" if c.endswith(":") else "")
            rows, i = [], i + 2
            while i < n and lines[i].strip().startswith("|"):
                rows.append(_split_row(lines[i]))
                i += 1

            def cell(tag, c, k):
                a = aligns[k] if k < len(aligns) and aligns[k] else ""
                st = f' style="text-align:{a}"' if a else ""
                return f"<{tag}{st}>{inline(c, resolve, broken)}</{tag}>"

            th = "".join(cell("th", c, k) for k, c in enumerate(head))
            trs = "".join("<tr>" + "".join(cell("td", c, k) for k, c in enumerate(r)) + "</tr>" for r in rows)
            out.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue

        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            first = next((b.strip() for b in buf if b.strip()), "")
            cls = ""
            if first.startswith("⚠️") or first.startswith("⚠"):
                cls = ' class="callout warn"'
            elif first.startswith("💡"):
                cls = ' class="callout tip"'
            inner, _ = render("\n".join(buf), resolve, broken, toc, counter)
            out.append(f"<blockquote{cls}>{inner}</blockquote>")
            continue

        if _list_re.match(line):
            items = []
            while i < n:
                l = lines[i]
                lm = _list_re.match(l)
                if lm:
                    indent = len(lm.group(1).replace("\t", "    "))
                    items.append([indent, lm.group(2)[0].isdigit(), lm.group(3)])
                    i += 1
                elif l.strip() and l.startswith((" ", "\t")) and items:
                    items[-1][2] += " " + l.strip()
                    i += 1
                else:
                    break
            out.append(_render_list(items, resolve, broken))
            continue

        buf = [line.strip()]
        i += 1
        while i < n and not _is_block_start(lines[i], lines[i + 1] if i + 1 < n else None):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf), resolve, broken)}</p>")

    return "".join(out), toc
