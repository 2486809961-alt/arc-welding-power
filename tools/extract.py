# -*- coding: utf-8 -*-
"""把《电力电子和焊接电源》课件 PDF 拆成逐页结构化数据（章节/标题/条目/红字）。"""
import pymupdf, re, json, sys

PDF = sys.argv[1] if len(sys.argv) > 1 else '99 素材/弧焊电源PPT.pdf'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'tools/pages.json'

FOOT = re.compile(r'^(上海工程技术大学材料工程学院|November \d|Slide\s*\d+$|20\d\d$|焊接技术与工程)')
MARKERS = set('Ønuü•●○◆■▪▶★☆①②③④⑤⑥⑦⑧⑨⑩△▲◇□■pqltvwsp')
CHAP_RE = re.compile(r'^第[一二三四五六七八九十]+章')
SEC_RE = re.compile(r'^(\d+\.\d+(?:\.\d+)?)\s*[．.、 ]\s*\S')
NUM_ITEM = re.compile(r'^(\(\d+\)|\d+[)）、]|[（(]\d+[）)]|[a-zA-Z][)）、])')


def clean(t):
    t = t.replace('\u3000', ' ').replace('\xa0', ' ')
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.replace('== ==', '').replace('====', '')
    t = re.sub(r'==\s*==', '', t)
    return t.strip()


def split_marker(t):
    if not t:
        return '', t, 'para'
    m = NUM_ITEM.match(t)
    if m:
        rest = t[m.end():].strip(' .、·:：')
        if rest:
            return m.group(1), rest, 'num'
    if len(t) > 1 and (t[0] in 'Ønuü•●○◆■▪▶★☆' or (t[0] in MARKERS and (t[1] in ' .、·:：' or re.match(r'[\u4e00-\u9fff0-9]', t[1])))):
        rest = t[1:].lstrip(' .、·:：')
        if rest:
            return t[0], rest, 'bullet'
    return '', t, 'para'


def junk(t):
    s = t.strip()
    if not s:
        return True
    if len(s) <= 2 and not re.search(r'[\u4e00-\u9fff]', s):
        return True
    if len(s) <= 4 and not re.search(r'[\u4e00-\u9fffA-Za-z]{2,}', s):
        return True
    return False


def line_info(l):
    spans = [s for s in l['spans'] if s['text'].strip()]
    if not spans:
        return None
    parts = []
    for s in spans:
        red = (s['color'] == 0xff0000)
        if parts and parts[-1][0] == red:
            parts[-1][1] += s['text']
        else:
            parts.append([red, s['text']])
    out = ''
    for red, t in parts:
        tt = clean(t)
        if not tt:
            continue
        if red:
            out += (' ' if out and not out.endswith(' ') else '') + '==' + tt + '=='
        else:
            out += (' ' if out and out[-1].isascii() and out[-1].isalnum() and tt[0].isascii() and tt[0].isalnum() else '') + tt
    return dict(x=round(l['bbox'][0], 1), y=round(l['bbox'][1], 1),
                sz=round(max(s['size'] for s in spans), 1),
                red=any(r for r, _ in parts), txt=clean(out))


def collect(pg):
    lines = []
    for b in pg.get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for l in b['lines']:
            li = line_info(l)
            if li and li['txt']:
                lines.append(li)
    lines.sort(key=lambda r: (round(r['y'], 1), r['x']))
    return lines


def build_page(i, pg):
    lines = [l for l in collect(pg) if not FOOT.match(l['txt'])]
    body = [l for l in lines if 55 <= l['y'] <= 480]
    chapter = ''
    for l in lines:
        t = re.sub(r'\s+', '', l['txt'])
        if CHAP_RE.match(t) and len(t) < 30:
            chapter = t
            break
    title = ''
    for l in body:
        t = re.sub(r'^==', '', l['txt'])
        if junk(l['txt']) or CHAP_RE.match(t) or re.match(r'^[\d.、]+$', t):
            continue
        title = clean(split_marker(l['txt'])[1])
        break
    blocks, prev = [], None
    for l in body:
        if junk(l['txt']):
            continue
        mk, txt, kind = split_marker(l['txt'])
        txt = clean(txt)
        if not txt:
            continue
        same_flow = (prev is not None and kind == 'para' and blocks and blocks[-1]['kind'] == 'para'
                     and abs(l['x'] - prev['x']) < 10 and (l['y'] - prev['y']) < max(l['sz'] * 2.1, 34)
                     and prev['sz'] == l['sz']
                     and not re.search(r'[。！？；：，、)）】”’…]$', blocks[-1]['text']))
        cont_bullet = (prev is not None and kind == 'para' and blocks and blocks[-1]['kind'] == 'bullet'
                       and prev['sz'] == l['sz'] and (l['y'] - prev['y']) < max(l['sz'] * 2.2, 34)
                       and not blocks[-1]['text'].endswith('。'))
        if cont_bullet:
            joiner = ' ' if (blocks[-1]['text'][-1].isascii() and blocks[-1]['text'][-1].isalnum()) else ''
            blocks[-1]['text'] += joiner + txt
            blocks[-1]['red'] = blocks[-1]['red'] or l['red']
            prev = l
            continue
        if same_flow and len(blocks) == 1 and blocks[0]['text'] == title:
            same_flow = False
        if same_flow:
            joiner = ' ' if (blocks[-1]['text'][-1].isascii() and blocks[-1]['text'][-1].isalnum()) else ''
            blocks[-1]['text'] += joiner + txt
            blocks[-1]['red'] = blocks[-1]['red'] or l['red']
            prev = l
            continue
        level = 0 if l['sz'] >= 23 else 1
        is_head = (kind == 'para' and l['sz'] >= 26 and len(txt) <= 28
                   and not re.search(r'[。！？；：，、]$', txt) and '==' not in txt
                   and not re.search(r'[=＝]', txt))
        blocks.append(dict(kind='head' if is_head else ('bullet' if kind != 'para' else 'para'),
                           level=level, marker=mk, sz=l['sz'], red=l['red'], text=txt))
        prev = l
    sec = ''
    for b in blocks:
        if b['kind'] == 'bullet':
            continue
        m = SEC_RE.match(b['text'])
        if m and b['sz'] >= 22:
            sec = re.sub(r'\s+', ' ', b['text']).strip()
            break
    return dict(pdf=i + 1, imgs=len(pg.get_images()), chapter=chapter, title=title,
                section=sec, blocks=blocks,
                reds=[b['text'] for b in blocks if b['red']],
                nlines=len(body))


def main():
    doc = pymupdf.open(PDF)
    pages = [build_page(i, pg) for i, pg in enumerate(doc)]
    json.dump(pages, open(OUT, 'w'), ensure_ascii=False, indent=1)
    empty = sum(1 for p in pages if not p['blocks'])
    print('pages', len(pages), 'empty', empty, '->', OUT)


if __name__ == '__main__':
    main()
