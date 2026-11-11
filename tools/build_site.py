#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「弧焊电源」Obsidian 库构建成自包含静态站点（GitHub Pages）。

用法: python3 tools/build_site.py [--out public]
依赖: markdown, pyyaml, pillow
"""
import argparse, html, io, json, re, shutil, sys
from pathlib import Path
from urllib.parse import quote

import markdown, yaml
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
COURSE = '弧焊电源'
TOTAL_SLIDES = 273

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
BLOCK_MATH_RE = re.compile(r"\$\$(.+?)\$\$", re.S)
INLINE_MATH_RE = re.compile(r"(?<!\\)\$(?!\$)([^\n$]+?)(?<!\\)\$")
MERMAID_RE = re.compile(r"```mermaid[ \t]*\n(.*?)```", re.S)
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
EMBED_IMG_RE = re.compile(r"!\[\[([^\[\]|]+?\.(?:jpg|jpeg|png|gif|svg))(?:\|(\d+))?\]\]", re.I)

MD_EXT = ["tables", "fenced_code", "footnotes", "md_in_html", "sane_lists", "attr_list"]


def split_fm(text):
    m = FM_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except Exception:
        meta = {}
    return (meta if isinstance(meta, dict) else {}), text[m.end():]


def protect(text, store, kind, pat, wrap):
    def repl(m):
        key = f"@@{kind}{len(store)}@@"
        store[key] = wrap(m.group(1))
        return key
    return pat.sub(repl, text)


def restore(text, store):
    for _ in range(4):
        hit = False
        for k, v in store.items():
            if k in text:
                text = text.replace(k, v)
                hit = True
        if not hit:
            break
    return text


def transform_callouts(text):
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        m = re.match(r"^>\s*\[!(\w+)\][-+]?\s*(.*)$", lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        kind, title = m.group(1).lower(), m.group(2).strip()
        body, i = [], i + 1
        while i < len(lines) and lines[i].startswith(">"):
            body.append(re.sub(r"^>\s?", "", lines[i])); i += 1
        inner = "\n".join(body).strip("\n")
        t = f'<div class="callout-title">{title}</div>' if title else ""
        if inner:
            out.append(f'<div class="callout callout-{kind}" markdown="1">')
            if t: out.append(t)
            out.append(inner)
            out.append("</div>")
        else:
            out.append(f'<div class="callout callout-{kind}">{t}</div>')
    return "\n".join(out)


def build_linker(alias, titles, prefix, imgmap):
    def repl(m):
        raw = m.group(1)
        target, _, label = raw.partition("|")
        target, label = target.strip().rstrip("\\"), label.strip()
        anchor = ""
        if "#" in target:
            target, _, anchor = target.partition("#")
            target, anchor = target.strip(), anchor.strip()
        if target.lower().endswith(".pdf"):
            mm = re.search(r"page=(\d+)", anchor or "")
            pg = f"（PDF 第 {mm.group(1)} 页）" if mm else ""
            return f'<span class="pdf-ref" title="原始课件 PDF 不在网页端">📄 {html.escape(label or COURSE + " 课件")}{pg}</span>'
        if not target:
            return f'<a href="#" class="wikilink">{html.escape(label or anchor)}</a>'
        url = alias.get(target) or alias.get(target.lower())
        name = label or titles.get(target, target)
        if anchor and not anchor.startswith("page="):
            name = label or f"{titles.get(target, target)} › {anchor}"
        if url:
            frag = f"#{quote(anchor)}" if anchor and not anchor.startswith("page=") else ""
            return f'<a href="{prefix}{quote(url)}{frag}" class="wikilink" title="{html.escape(target)}">{html.escape(name)}</a>'
        return f'<span class="wikilink broken" title="库中未找到：{html.escape(target)}">{html.escape(name)}</span>'
    return repl


def render_md(text, alias, titles, prefix, imgmap, demote=False):
    store = {}
    if demote:
        text = re.sub(r"^# (?!#)", "## ", text, flags=re.M)
    text = protect(text, store, "MER", MERMAID_RE,
                   lambda b: f'<pre class="mermaid">{html.escape(b.strip())}</pre>')
    text = protect(text, store, "CODE", re.compile(r"```[^\n`]*\n(.*?)```", re.S),
                   lambda b: f'<pre class="code-raw">{html.escape(b)}</pre>')

    def img(key, w):
        cls = "note-img" + (" small" if w and int(w) < 500 else "")
        return f'<figure class="fig"><img class="{cls}" src="{prefix}assets/img/{quote(imgmap.get(key, key))}" alt="{html.escape(key)}" loading="lazy"></figure>'
    text = EMBED_IMG_RE.sub(lambda m: img(m.group(1).strip(), m.group(2)), text)

    text = protect(text, store, "MB", BLOCK_MATH_RE, lambda b: f'<span class="math-block">$${b}$$</span>')
    text = protect(text, store, "MI", INLINE_MATH_RE, lambda b: f'<span class="math-inline">${b}$</span>')
    text = transform_callouts(text)
    text = WIKILINK_RE.sub(build_linker(alias, titles, prefix, imgmap), text)
    text = re.sub(r"==(.+?)==", r"<mark>\1</mark>", text)
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    md = markdown.Markdown(extensions=MD_EXT, output_format="html5")
    out = md.convert(text); md.reset()
    out = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', out)
    out = restore(out, store)
    out = re.sub(r'<p>\s*(<span class="math-block">.*?</span>)\s*</p>',
                 lambda m: m.group(1).replace('math-block', 'math-block block'), out, flags=re.S)
    out = re.sub(r'<p>\s*(<pre class="(?:code-raw|mermaid)">.*?</pre>)\s*</p>', r'\1', out, flags=re.S)
    out = re.sub(r'<p>\s*(<figure class="fig">.*?</figure>)\s*</p>', r'\1', out, flags=re.S)
    return out


DIR_ORDER = ['00 索引', '01 第1章 绪论', '02 第2章 基本电气特性', '03 第3章 弧焊变压器',
             '04 第4章 电子控制型弧焊电源', '05 第5章 晶闸管弧焊整流器', '06 第6章 逆变式弧焊电源',
             '07 例题', '08 图谱', '09 概念卡', '10 公式库', '11 附表数据', '12 术语', '13 手写笔记']
DIR_DESC = {
    '00 索引': 'MOC / 页码对照 / 学习路径 / 概念地图 / 红色重点 / 一页纸复习',
    '01 第1章 绪论': '16 页 · 焊接与弧焊电源、分类、发展',
    '02 第2章 基本电气特性': '66 页 · 电弧、外特性、调节特性、动特性',
    '03 第3章 弧焊变压器': '53 页 · 变压器基础、增强漏磁三型',
    '04 第4章 电子控制型弧焊电源': '53 页 · 电力半导体器件与反馈控制',
    '05 第5章 晶闸管弧焊整流器': '47 页 · 三相整流主电路与触发电路',
    '06 第6章 逆变式弧焊电源': '38 页 · 逆变主电路、PWM/PFM',
    '07 例题': '课件回顾页与思考题',
    '08 图谱': '课程地图 / 概念网（canvas 原件见仓库）',
    '09 概念卡': '47 张原子概念卡，双向链接',
    '10 公式库': '公式总表（KaTeX）',
    '11 附表数据': '数据表与图注索引',
    '12 术语': '中英术语对照',
    '13 手写笔记': '拍照讲义 118 页 + 课堂实拍重点 11 张',
}

PAGE = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 弧焊电源知识库</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title} · 弧焊电源知识库">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%278%27 fill=%27%23d9480f%27/%3E%3Ctext x=%2716%27 y=%2722%27 font-size=%2716%27 text-anchor=%27middle%27 fill=%27white%27 font-family=%27sans-serif%27%3E弧%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="{root}assets/style.css">
<link rel="stylesheet" href="{root}assets/katex/katex.min.css">
</head>
<body>
<header class="topbar">
  <button class="menu-btn" id="menuBtn" aria-label="目录">☰</button>
  <a class="brand" href="{root}index.html">弧焊电源<span class="brand-sub">焊接电源课件知识库</span></a>
  <div class="search-wrap">
    <input id="searchInput" type="search" placeholder="搜索笔记 / 概念 / 公式…" autocomplete="off">
    <div id="searchResults" class="search-results"></div>
  </div>
  <a class="btn dl" href="{repo}" target="_blank" rel="noopener">⬇︎ 下载整库</a>
  <button class="btn ghost" id="themeBtn" aria-label="切换主题">◐</button>
</header>
<div class="layout">
  <nav class="sidebar" id="sidebar"><div class="side-inner" id="sideInner"><a class="side-home" href="{root}index.html">🏠 首页</a></div></nav>
  <main class="content">
    <article class="note">
{body}
    </article>
    <nav class="pager">{pager}</nav>
    <footer class="foot">
      <a href="{repo}" target="_blank" rel="noopener">GitHub 仓库</a> ·
      <a href="{root}index.html">首页</a> ·
      个人学习笔记，课件版权归授课教师与学校所有
    </footer>
  </main>
</div>
<script>window.__ROOT__="{root}";</script>
<script src="{root}assets/katex/katex.min.js"></script>
<script defer src="{root}assets/katex/contrib/auto-render.min.js"></script>
<script src="{root}assets/mermaid.min.js"></script>
<script src="{root}assets/app.js"></script>
</body>
</html>
"""


def slugify(rel_noext: str) -> str:
    s = str(rel_noext).replace('\\', '/')
    s = re.sub(r'[ /]+', '-', s)
    s = re.sub(r'[^\w\u4e00-\u9fff\-（）()＋+~,，.．—]', '', s)
    return s[:90]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='public')
    ap.add_argument('--base', default='/arc-welding-power/')
    ap.add_argument('--repo', default='https://github.com/2486809961-alt/arc-welding-power')
    ap.add_argument('--deps', default='/tmp/site-deps/node_modules')
    args = ap.parse_args()

    out = ROOT / args.out
    if out.exists():
        shutil.rmtree(out)
    (out / 'notes').mkdir(parents=True)
    (out / 'assets' / 'img').mkdir(parents=True)

    md_files = [p for p in ROOT.rglob('*.md')
                if '.obsidian' not in p.parts and 'tools' not in p.parts
                and args.out not in p.parts and 'public' not in p.parts]
    def sortkey(p):
        rel = p.relative_to(ROOT)
        top = rel.parts[0] if len(rel.parts) > 1 else 'zz README'
        oi = DIR_ORDER.index(top) if top in DIR_ORDER else 99
        return (oi, str(rel))
    md_files.sort(key=sortkey)

    docs, alias, titles, imgmap = [], {}, {}, {}
    for i, p in enumerate(md_files, 1):
        raw = p.read_text(encoding='utf-8', errors='replace')
        meta, body = split_fm(raw)
        rel = p.relative_to(ROOT)
        rn = rel.with_suffix('')
        title = rn.name
        slug = f'notes/{i:03d}-{slugify(rn)}.html'
        d = dict(path=str(rel), rel=str(rn), dir=str(rn.parent), title=title,
                 meta=meta, body=body, slug=slug, seq=i)
        docs.append(d)
        for k in (title, str(rn), rel.name):
            alias.setdefault(k, slug); alias.setdefault(k.lower(), slug)
        titles[title] = title
        for a in (meta.get('aliases') or []):
            a = str(a).strip()
            if a:
                alias.setdefault(a, slug); alias.setdefault(a.lower(), slug)

    # 图片：引用到的才拷，统一缩到 1100/1000 宽
    used = set()
    for d in docs:
        for m in EMBED_IMG_RE.finditer(d['body']):
            used.add(m.group(1).strip())
    srcs = {}
    for pat in ('99 素材/页面/*.jpg', '13 手写笔记/页图/*.jpg', '13 手写笔记/课堂实拍/*.jpg'):
        for f in ROOT.glob(pat):
            srcs[f.name] = f
    made = 0
    for name in sorted(used):
        src = srcs.get(name)
        if not src:
            print('  ⚠ 缺图', name); continue
        im = Image.open(src).convert('RGB')
        target_w = 1000 if name.startswith('h-') else 1100
        if im.width > target_w:
            im = im.resize((target_w, int(im.height * target_w / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=70, optimize=True, progressive=True)
        (out / 'assets' / 'img' / name).write_bytes(buf.getvalue())
        imgmap[name] = name
        made += 1
    print(f'  图片 {made} 张（{sum((out/"assets"/"img"/n).stat().st_size for n in imgmap)//1024//1024} MB）')

    tree = {}
    for d in docs:
        tree.setdefault(d['dir'], []).append(d)
    def dirsort(k):
        top = k.split('/')[0]
        oi = DIR_ORDER.index(top) if top in DIR_ORDER else 99
        return (oi, k)
    sidebar = ['<a class="side-home" href="index.html">🏠 首页</a>']
    for dr in sorted(tree, key=dirsort):
        label = '根目录' if dr == '.' else dr
        sidebar.append('<details class="side-group" open><summary>' + html.escape(label) + '</summary><ul>')
        for d in sorted(tree[dr], key=lambda x: x['seq']):
            t = d['meta'].get('type') or ''
            cls = 'side-link'
            if t == '概念':
                cls += ' type-card'
            elif t == '讲义页':
                cls += ' type-lect'
            elif t == '手写笔记':
                cls += ' type-hand'
            elif t == '课堂实拍':
                cls += ' type-key'
            sidebar.append(f'<li><a class="{cls}" href="{quote(d["slug"])}" data-title="{html.escape(d["title"])}">{html.escape(d["title"])}</a></li>')
        sidebar.append('</ul></details>')
    sidebar = '\n'.join(sidebar)

    def sidebar_for(root):
        return re.sub(r'href="(index\.html|notes/)', lambda m: f'href="{root}{m.group(1)}', sidebar)
    # 侧栏抽成独立资源，避免每页重复几十 KB
    (out / 'assets' / 'sidebar.html').write_text(sidebar, encoding='utf-8')
    sidebar = ''

    def url_in_notes(slug):
        return quote(slug).replace('notes/', '', 1)

    search = []
    for idx, d in enumerate(docs):
        body_html = render_md(d['body'], alias, titles, '../', imgmap, demote=True)
        meta = d['meta']
        tags = meta.get('tags') or []
        if isinstance(tags, str):
            tags = [tags]
        chips = []
        if meta.get('chapter'):
            chips.append(f'<span class="meta-chip">第 {meta["chapter"]} 章</span>')
        if meta.get('slide_page'):
            chips.append(f'<span class="meta-chip">幻灯片 {meta["slide_page"]}/{TOTAL_SLIDES}</span>')
        if meta.get('section') and meta['section'] not in ('—', '全章'):
            chips.append(f'<span class="meta-chip">{html.escape(str(meta["section"]))}</span>')
        if meta.get('source_page'):
            chips.append(f'<span class="meta-chip">原 PDF 第 {meta["source_page"]} 页</span>')
        tag_html = ''.join(f'<span class="tag">{html.escape(str(t))}</span>' for t in tags)
        crumb = d['rel'].replace('\\', '/')
        head = (f'<div class="note-head"><div class="crumb">{html.escape(crumb)}</div>'
                f'<h1>{html.escape(d["title"])}</h1>'
                f'<div class="meta-row">{tag_html}{"".join(chips)}</div></div>')
        prev_d = docs[idx - 1] if idx else None
        nxt = docs[idx + 1] if idx + 1 < len(docs) else None
        pager = ''
        if prev_d:
            pager += f'<a class="prev" href="{quote(prev_d["slug"])}">← {html.escape(prev_d["title"])}</a>'
        if nxt:
            pager += f'<a class="next" href="{quote(nxt["slug"])}">{html.escape(nxt["title"])} →</a>'
        (out / d['slug']).write_text(PAGE.format(
            title=html.escape(d['title']), desc=html.escape(crumb), root='../',
            body=head + body_html, pager=pager, repo=args.repo),
            encoding='utf-8')
        plain = re.sub(r'```.*?```', ' ', d['body'], flags=re.S)
        plain = re.sub(r'!?\[\[[^\]]+\]\]', ' ', plain)
        plain = re.sub(r'[#>*`|\[\]()]|(@@\w+\d+@@)', ' ', plain)
        plain = re.sub(r'\s+', ' ', plain).strip()
        search.append(dict(t=d['title'], u=d['slug'], d=d['dir'],
                           g=' '.join(str(t) for t in tags), x=plain[:1200]))
        d['_html'] = body_html

    (out / 'assets' / 'search.json').write_text(json.dumps(search, ensure_ascii=False), encoding='utf-8')

    # 首页
    moc = next((d for d in docs if d['title'] == '01 弧焊电源 MOC'), docs[0])
    cards = []
    for dr in sorted(tree, key=dirsort):
        if dr == '.':
            continue
        first = sorted(tree[dr], key=lambda x: x['seq'])[0]
        cards.append(f'<a class="card" href="{quote(first["slug"])}"><div class="card-t">{html.escape(dr)}</div>'
                     f'<div class="card-d">{html.escape(DIR_DESC.get(dr, ""))}</div>'
                     f'<div class="card-n">{len(tree[dr])} 篇</div></a>')
    stats = dict(notes=len(docs), cards=len(alias and [d for d in docs if d['meta'].get('type') == '概念']),
                 hand=len([d for d in docs if d['meta'].get('type') == '手写笔记']),
                 keys=len([d for d in docs if d['meta'].get('type') == '课堂实拍']))
    landing = f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>弧焊电源 · 焊接电源课件知识库</title>
<meta name="description" content="《电力电子和焊接电源》273 页课件逐页笔记：6 章讲义 + 47 张概念卡 + 公式库 + 拍照笔记与课堂重点实拍。">
<meta property="og:title" content="弧焊电源 · 焊接电源课件知识库">
<meta property="og:description" content="273 页课件逐页笔记、47 张概念卡、手写笔记与课堂重点，全文可搜。">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%278%27 fill=%27%23d9480f%27/%3E%3Ctext x=%2716%27 y=%2722%27 font-size=%2716%27 text-anchor=%27middle%27 fill=%27white%27 font-family=%27sans-serif%27%3E弧%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/katex/katex.min.css">
</head>
<body class="landing">
<header class="topbar">
  <a class="brand" href="index.html">弧焊电源<span class="brand-sub">焊接电源课件知识库</span></a>
  <div class="search-wrap">
    <input id="searchInput" type="search" placeholder="搜索笔记 / 概念 / 公式…" autocomplete="off">
    <div id="searchResults" class="search-results"></div>
  </div>
  <a class="btn dl" href="{args.repo}" target="_blank" rel="noopener">⬇︎ 下载整库</a>
  <button class="btn ghost" id="themeBtn" aria-label="切换主题">◐</button>
</header>
<main class="hero">
  <h1>弧焊电源</h1>
  <p class="sub">{stats['notes']} 篇笔记 · 6 章 / 273 页课件 · {stats['cards']} 张概念卡 · 公式全 KaTeX · 手写笔记 {stats['hand']} 页 · 课堂重点 {stats['keys']} 张</p>
  <div class="cta">
    <a class="btn primary" href="{quote(moc['slug'])}">开始阅读 →</a>
    <a class="btn" href="notes/{quote(next(d['slug'] for d in docs if d['title']=='06 一页纸复习').replace('notes/',''))}">考前·一页纸复习</a>
    <a class="btn ghost" href="{args.repo}" target="_blank" rel="noopener">GitHub 仓库</a>
  </div>
  <div class="grid">{''.join(cards)}</div>
  <section class="intro">
{render_md(moc['body'], alias, titles, '', imgmap)}
  </section>
  <footer class="foot">
    <a href="{args.repo}" target="_blank" rel="noopener">GitHub</a> ·
    课件版权归授课教师与学校所有；本库为个人整理的结构化学习笔记。
  </footer>
</main>
<script>window.__ROOT__="";</script>
<script src="assets/katex/katex.min.js"></script>
<script defer src="assets/katex/contrib/auto-render.min.js"></script>
<script src="assets/mermaid.min.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""
    (out / 'index.html').write_text(landing, encoding='utf-8')

    # 静态资源
    deps = Path(args.deps)
    katex = deps / 'katex' / 'dist'
    (out / 'assets' / 'katex').mkdir(exist_ok=True)
    if katex.is_dir():
        for n in ('katex.min.css', 'katex.min.js'):
            shutil.copy(katex / n, out / 'assets' / 'katex' / n)
        (out / 'assets' / 'katex' / 'contrib').mkdir(exist_ok=True)
        shutil.copy(katex / 'contrib' / 'auto-render.min.js', out / 'assets' / 'katex' / 'contrib' / 'auto-render.min.js')
        (out / 'assets' / 'katex' / 'fonts').mkdir(exist_ok=True)
        for f in (katex / 'fonts').glob('*.woff2'):
            shutil.copy(f, out / 'assets' / 'katex' / 'fonts' / f.name)
    else:
        sys.exit('缺少 katex')
    mm = deps / 'mermaid' / 'dist' / 'mermaid.min.js'
    if mm.is_file():
        shutil.copy(mm, out / 'assets' / 'mermaid.min.js')
    shutil.copy(ROOT / 'tools' / 'site_assets' / 'style.css', out / 'assets' / 'style.css')
    shutil.copy(ROOT / 'tools' / 'site_assets' / 'app.js', out / 'assets' / 'app.js')
    (out / '.nojekyll').write_text('', encoding='utf-8')
    print(f'✓ {len(docs)} 页 → {out}')


if __name__ == '__main__':
    main()
