# -*- coding: utf-8 -*-
"""拍照讲义/手写笔记 → Obsidian 手写笔记页：划重点、折属性、挂回讲义页。"""
import os, re, json, sys, difflib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = [('1~5周', '1~5周 焊接电源(1).pdf', '/tmp/hw1.txt'),
       ('6~8周', '6~8周 焊接电源(差最后一节课)(1).pdf', '/tmp/hw2.txt')]
PDFDIR = '/Users/jiarun/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_fw6mlzx84ez622_b83e/temp/drag'
OUT = os.path.join(ROOT, '13 手写笔记')
CH = {1: ('第1章 绪论', '绪论'), 2: ('第2章 基本电气特性', '基本电气特性'), 3: ('第3章 弧焊变压器', '弧焊变压器'),
      4: ('第4章 电子控制型', '电子控制型'), 5: ('第5章 晶闸管整流器', '晶闸管整流器'), 6: ('第6章 逆变式', '逆变式')}
NAV = {c: '00 第%d章 %s 导航' % (c, v[1]) for c, v in CH.items()}
DROP = re.compile(r'(扫描全能王|亿人都在用|扫描App|勤奋|求是|创新|奉献|主讲教师|材料科学与工程|上海工程技术大学|数字化控制|数子化控制)')
MARK = re.compile(r'(定义|特点|要求|原理|公式|结论|注意|重点|最基本|必须|条件|作用|优点|缺点|分类|组成|步骤|判断|规律|口诀)')
# 常见 OCR 形近字（仅按整词替换，避免误伤）
FIX = [('孤焊', '弧焊'), ('电孤', '电弧'), ('孤电源', '弧电源'), ('孤柱', '弧柱'), ('都分', '部分'),
       ('电扱', '电极'), ('特生', '特性'), ('特悴', '特性'), ('特怕', '特性'), ('特恆', '特性'),
       ('数宇化', '数字化'), ('选变', '逆变'), ('煇', '焊'), ('弧煇', '弧焊'), ('尚核心', '的核心'),
       ('先选弧焊', '先进弧焊'), ('挖制', '控制'), ('控削', '控制'), ('控俐', '控制'), ('芥式', '桥式'),
       ('整统', '整流'), ('整流嚣', '整流器'), ('整流暴', '整流器'), ('鳖院', '整流'), ('晶闸', '晶闸')]


def fix(t):
    for a, b in FIX:
        t = t.replace(a, b)
    return t
LEAD = re.compile(r'^[·•◇◆■□❑口〇○*※\-—>》\s]+')
HEADER_LIKE = ['弧焊电源及其数字化控制', '电力电子和焊接电源', '焊接电源', '弧焊电源及其数字控制']


def header_like(l):
    return any(difflib.SequenceMatcher(None, l, h).ratio() > 0.45 for h in HEADER_LIKE)


def clean(t):
    t = t.replace('==', '')
    t = re.sub(r'\s+', '', t)
    t = LEAD.sub('', t)
    return t.strip()


def parse_ocr(path):
    raw = open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'@@PAGE (\d+)@@\n(.*?)(?=@@PAGE \d+@@|\Z)', raw, re.S):
        out[int(m.group(1))] = [clean(x) for x in m.group(2).split('\n')]
    return out


def grams(s, n=2):
    s = re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', s)
    return {s[i:i + n] for i in range(len(s) - n + 1)} if len(s) >= n else {s}


def main():
    pages = json.load(open(os.path.join(ROOT, 'tools/pages.json'), encoding='utf-8'))
    meta = {m['n']: m for m in json.load(open(os.path.join(ROOT, 'tools/meta.json'), encoding='utf-8'))}
    lec_text = {p['pdf']: ''.join(b['text'] for b in p['blocks']).replace('==', '') for p in pages}
    lec_g = {n: grams(t) for n, t in lec_text.items()}
    ALL = set().union(*lec_g.values())

    recs = []
    for tag, fname, ocrpath in SRC:
        raw = parse_ocr(ocrpath)
        N = len(raw)
        freq = collections.Counter(l for ls in raw.values() for l in set(ls) if l)
        for n in sorted(raw):
            ls = []
            for idx, l in enumerate(raw[n]):
                if not l or DROP.search(l) or len(l) < 4:
                    continue
                if header_like(l):
                    continue
                if idx <= 2 and len(l) <= 22:
                    lg0 = grams(l)
                    if len(lg0 & ALL) / max(1, len(lg0)) < 0.3:
                        continue
                if freq[l] >= max(3, N * 0.12):      # 页眉页脚/水印
                    continue
                if len(re.findall(r'[\u4e00-\u9fff]', l)) < 3 and '=' not in l:
                    continue
                ls.append(fix(l))
            recs.append(dict(src=tag, pdf=fname, page=n, lines=ls, text=''.join(ls)))
    # 去重（同页拍两张）
    kept, dups = [], []
    for r in recs:
        hit = None
        for k in kept:
            if k['src'] == r['src'] and k['text'] and r['text']:
                sm = difflib.SequenceMatcher(None, k['text'], r['text'])
                if sm.real_quick_ratio() > 0.8 and sm.ratio() > 0.75:
                    hit = k
                    break
        if hit:
            dups.append((r['src'], r['page']))
            if len(r['text']) > len(hit['text']) * 1.15:
                hit.update(page=r['page'], lines=r['lines'], text=r['text'])
        else:
            kept.append(r)
    kept.sort(key=lambda r: (r['src'], r['page']))

    cur = 1
    for r in kept:
        g = grams(r['text'])
        sc = sorted(((len(g & lec_g[n]) / max(1, len(g | lec_g[n])), n) for n in lec_g if lec_g[n]), reverse=True)
        top = [n for s, n in sc[:3] if s > 0.04]
        r['like'] = top
        acc = collections.Counter()
        for sc_, n_ in sc[:3]:
            if sc_ > 0.04:
                acc[meta[n_]['chapter']] += sc_
        r['ch'] = acc.most_common(1)[0][0] if acc else cur
        cur = r['ch']
        hl = []
        for l in r['lines']:
            if len(l) < 10 or l in hl:
                continue
            lg = grams(l)
            contain = len(lg & ALL) / max(1, len(lg))
            if MARK.search(l) or (contain >= 0.85 and len(l) >= 12):
                hl.append(l)
        good = [l for l in r['lines']
                if len(re.findall(r'[\u4e00-\u9fff]', l)) >= 6
                and len(grams(l) & ALL) / max(1, len(grams(l))) >= 0.3]
        r['ocr'] = '好' if len(good) >= 3 else ('一般' if len(good) >= 1 else '差')
        if len(hl) > max(3, len(r['lines']) * 0.5):
            hl = [l for l in hl if MARK.search(l)] or hl[:2]
        r['hl'] = hl[:5]
        r['title'] = ''
        for l in r['lines']:
            if re.match(r'^\d+(\.\d+)*[ 、.．]', l) and len(l) <= 28:
                r['title'] = l
                break
        if not r['title']:
            best, bs = '', 0
            for l in r['lines']:
                if not (6 <= len(l) <= 26) or not re.search(r'[\u4e00-\u9fff]{4}', l) or MARK.search(l):
                    continue
                lg = grams(l)
                sc = len(lg & ALL) / max(1, len(lg))
                if sc > bs:
                    best, bs = l, sc
            if best and bs >= 0.35:
                r['title'] = best
        r['title'] = r['title'] or '手写页 p%03d' % r['page']
    json.dump([{k: r[k] for k in ('src', 'page', 'ch', 'title', 'lines', 'hl', 'like', 'ocr')} for r in kept],
              open(os.path.join(ROOT, 'tools/hw.json'), 'w'), ensure_ascii=False, indent=1)
    print('OCR 页', sum(1 for _ in recs), '| 去重后', len(kept), '| 重复', len(dups))


if __name__ == '__main__':
    main()
