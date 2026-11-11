# -*- coding: utf-8 -*-
"""由 tools/pages.json + tools/ocr.json 生成 Obsidian 讲义页、章导航与自动索引。"""
import json, re, os, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFNAME = '弧焊电源PPT.pdf'
TOTAL = 273
COURSE = '弧焊电源'

CHAPTERS = [
    dict(n=1, folder='01 第1章 绪论', short='绪论',
         name='第一章 绪论', start=1, end=16),
    dict(n=2, folder='02 第2章 基本电气特性', short='基本电气特性',
         name='第二章 弧焊电源的基本电气特性', start=17, end=82),
    dict(n=3, folder='03 第3章 弧焊变压器', short='弧焊变压器',
         name='第三章 弧焊变压器', start=83, end=135),
    dict(n=4, folder='04 第4章 电子控制型弧焊电源', short='电子控制型',
         name='第四章 电子控制型弧焊电源', start=136, end=188),
    dict(n=5, folder='05 第5章 晶闸管弧焊整流器', short='晶闸管整流器',
         name='第五章 晶闸管弧焊整流器', start=189, end=235),
    dict(n=6, folder='06 第6章 逆变式弧焊电源', short='逆变式',
         name='第六章 逆变式弧焊电源', start=236, end=273),
]

BANDS = {
 1: [(1, 2, '封面与主要内容'), (3, 6, '焊接与弧焊电源'), (7, 10, '弧焊电源的分类'),
     (11, 15, '弧焊电源的发展与现代电源'), (16, 17, '课程目的与第2章导览')],
 2: [(17, 20, '2.1 焊接电弧与电离'), (21, 25, '引弧方式'), (26, 27, '电弧结构与电压分布'),
     (28, 31, '电弧静特性'), (32, 33, '电弧动特性与负载特点'), (34, 37, '交流电弧与脉冲电弧'),
     (38, 42, '2.2 弧焊电源的基本要求'), (43, 51, '2.3 外特性与“电源—电弧”系统稳定'),
     (52, 63, '外特性形状的选择'), (64, 66, '空载电压、短路电流与常用外特性'),
     (67, 73, '2.4 调节特性'), (74, 81, '2.5 动态特性'), (82, 82, '第二章回顾')],
 3: [(83, 87, '本章导览与 3.1 变压器基础知识'), (88, 92, '磁路与铁心材料'),
     (93, 96, '3.2 变压器结构与工作原理'), (97, 104, '空载运行、漏抗与负载运行'),
     (105, 110, '变压器外特性与简化等效电路'), (111, 115, '3.4 串联电抗器式弧焊变压器'),
     (116, 123, '动铁心式弧焊变压器(BX1)'), (124, 128, '动绕组式弧焊变压器(BX3)'),
     (129, 132, '抽头式弧焊变压器(BX6)'), (133, 135, '上一章回顾与思考题')],
 4: [(136, 138, '本章导览与电子控制型概述'), (139, 148, '4.1.1 晶闸管'),
     (149, 157, '晶体管与场效应管'), (158, 166, '绝缘栅双极型晶体管(IGBT)'),
     (167, 170, '第四章回顾与 4.2 基本工作原理'), (171, 182, '4.3 反馈控制与外特性形状'),
     (183, 188, '信号检测与 4.4 调节特性')],
 5: [(189, 191, '本章导览与 5.1 概述'), (192, 197, '整流电路预备知识'),
     (198, 204, '5.2 三相半波可控整流'), (205, 211, '三相半控桥式整流'),
     (212, 219, '六相半波与桥式整流'), (220, 227, '带平衡电抗器双反星形整流'),
     (228, 235, '5.3 触发电路')],
 6: [(236, 239, '本章导览与 6.1 逆变电源系统结构'), (240, 253, '逆变主电路与特点'),
     (254, 262, '6.2 逆变电路（单端/双端/全桥）'), (263, 266, '6.3 输入输出整流滤波'),
     (267, 270, '6.4 时间比率控制 PWM/PFM'), (271, 273, '6.5 特性控制')],
}

BAD_OCR = re.compile(r'(协同创新|制造技术|材料科学|上海市|SHANGHAI|LASER|EAM|ビA|LAMT|材料科学与工程|科学\s*与\s*工程)')
LEAD_JUNK = re.compile(r'^[『「【（(·•\-—\s|｜Ønuü●○◆■▪▶★☆]+')
TRIM = ' ：:；;，,、。.…'


def polish(t, chapter=''):
    t = t.replace('==', '')
    t = LEAD_JUNK.sub('', t).strip()
    if chapter and re.sub(r'\s+', '', t) == re.sub(r'\s+', '', chapter):
        return ''
    t = re.sub(r'^\d+\s+(?=[\u4e00-\u9fff])', '', t) if re.match(r'^\d+\s', t) else t
    while t.endswith(('）', ')')) and t.count('（') + t.count('(') < t.count('）') + t.count(')'):
        t = t[:-1].strip(TRIM)
    t = t.strip(TRIM)
    if len(t) > 22:
        cut = min([i for i in (t.find(c) for c in '：:，,；;') if i >= 6] or [len(t)])
        t = t[:cut].strip(TRIM)
    return t


def san(t):
    t = t.replace('==', '').strip()
    t = re.sub(r'[\\/:*?"<>|#^\[\]]', ' ', t)
    t = t.replace('/', '／')
    t = re.sub(r'\s+', ' ', t).strip(' .。,，')
    return t[:40].strip()


def chap_of(n):
    for c in CHAPTERS:
        if c['start'] <= n <= c['end']:
            return c
    return CHAPTERS[-1]


def residue_title(ocr):
    """OCR 候选标题（有序）"""
    out = []
    for line in ocr:
        if re.match(r'^\d+\.\d+(\.\d+)?\s', line) and re.search(r'[\u4e00-\u9fff]{2}', line):
            out.append(line)
    for line in ocr:
        if '※' in line or '＊' in line:
            out.append(line.replace('※', '').replace('＊', '').strip())
    for line in ocr:
        if len(re.findall(r'[\u4e00-\u9fff]', line)) >= 4 and not BAD_OCR.search(line):
            out.append(line)
    return out


def reds_clean(reds):
    out = []
    for r in reds:
        for part in re.findall(r'==(.+?)==', r):
            part = part.strip(' 。，、')
            if len(part) >= 4 and part not in out:
                out.append(part)
    return out


def blocks_md(blocks, title):
    lines, seen_title = [], False
    for b in blocks:
        t = b['text']
        if not seen_title and t.replace('==', '') == title:
            seen_title = True
            continue
        if b['kind'] == 'head':
            lines.append('### ' + t)
        elif b['kind'] == 'bullet':
            lines.append(('  ' * b['level']) + '- ' + t)
        else:
            lines.append(t)
        if lines and b['kind'] != 'bullet':
            lines.append('')
    out = '\n'.join(lines).strip()
    out = re.sub(r'\n{3,}', '\n\n', out)
    return out


def load_cards():
    """概念卡 → {页码: [卡名]} + 卡清单"""
    d = os.path.join(ROOT, '09 概念卡')
    by_page, cards = {}, []
    if not os.path.isdir(d):
        return by_page, cards
    for f in sorted(os.listdir(d)):
        if not f.endswith('.md'):
            continue
        name = f[:-3]
        txt = open(os.path.join(d, f), encoding='utf-8').read()
        cards.append(name)
        for n in set(int(x) for x in re.findall(r'\|p(\d{3})\]\]', txt)):
            by_page.setdefault(n, []).append(name)
    return by_page, cards


def main():
    pages = json.load(open(os.path.join(ROOT, 'tools/pages.json'), encoding='utf-8'))
    card_pages, _cards = load_cards()
    ocr = json.load(open(os.path.join(ROOT, 'tools/ocr.json'), encoding='utf-8'))
    meta, stats = [], dict(total=0, red=0, img=0)
    section_carry = {}
    for p in pages:
        n = p['pdf']
        c = chap_of(n)
        chapter = c['name']
        title = ''
        cands = ([p['title']] if p['title'] else []) + residue_title(ocr.get(str(n), []))
        for cand in cands:
            t = san(polish(cand, c['name']))
            if t and len(t) >= 2:
                title = t
                break
        title = title or f'图版 p{n:03d}'
        if n == c['start'] and c['n'] > 1:
            title = '本章导览'
        sec = p['section']
        if not sec:
            for line in ocr.get(str(n), []):
                m = re.match(r'^(\d+\.\d+(\.\d+)?)\s*\S', line)
                if m:
                    sec = line.strip()
                    break
        if sec:
            section_carry[c['n']] = sec
        elif n == c['start']:
            section_carry[c['n']] = '本章导览'
        sec = section_carry.get(c['n'], '本章导览')
        if n == c['start']:
            sec = '本章导览'
        kind = '正文'
        if n == 1:
            kind = '封面'
        elif n == c['start'] or '主要内容' in title:
            kind = '导学'
        elif re.search(r'(回顾|小结|总结|思考题|习题|重点与难点)', title + sec):
            kind = '小结'
        meta.append(dict(n=n, c=c, title=title, sec=sec, kind=kind, p=p))

    # ---- 清空旧讲义页
    for c in CHAPTERS:
        d = os.path.join(ROOT, c['folder'])
        if os.path.isdir(d):
            for f in os.listdir(d):
                if re.match(r'^p\d{3} .*\.md$', f):
                    os.remove(os.path.join(d, f))

    # ---- 写讲义页
    for m in meta:
        p, c, n = m['p'], m['c'], m['n']
        fn = f"p{n:03d} {m['title']}.md"
        m['fn'] = fn
        d = os.path.join(ROOT, c['folder'])
        os.makedirs(d, exist_ok=True)
        rel = os.path.join(d, fn)
        blocks = p['blocks']
        body = blocks_md(blocks, m['title'])
        reds = reds_clean(p['reds'])
        ocr_lines = []
        for l in ocr.get(str(n), []):
            t = l.replace('==', '').strip()
            if BAD_OCR.search(t):
                continue
            if re.sub(r'\s+', '', t) == re.sub(r'\s+', '', c['name']):
                continue
            if len(re.findall(r'[\u4e00-\u9fff]', t)) < 2 and not re.search(r'[=%]', t):
                continue
            ocr_lines.append(t)
            if len(ocr_lines) >= 14:
                break
        chunks = []
        chunks.append('---')
        chunks.append('type: 讲义页')
        chunks.append(f"chapter: {c['n']}")
        chunks.append(f'chapter_name: "{c["name"]}"')
        chunks.append(f'section: "{re.sub(r"\"", "", m["sec"])}"')
        chunks.append(f'slide_page: {n}')
        chunks.append(f'slide_total: {TOTAL}')
        chunks.append(f'pdf_page: {n}')
        chunks.append(f'kind: {m["kind"]}')
        chunks.append('tags:')
        chunks.append(f'  - {COURSE}')
        chunks.append(f'  - 章/{c["n"]:02d}')
        chunks.append(f'  - 类型/{m["kind"]}')
        chunks.append('aliases:')
        chunks.append(f'  - "{m["title"]}"')
        chunks.append(f'  - p{n:03d}')
        chunks.append('---')
        chunks.append('')
        chunks.append(f'> 📄 原文：[[{PDFNAME}#page={n}]]（幻灯片 {n}/{TOTAL}；PDF 第 {n} 页）')
        chunks.append('')
        chunks.append(f'# {m["title"]}')
        chunks.append('')
        chunks.append(f'![[p{n:03d}.jpg|760]]')
        chunks.append('')
        if body:
            chunks.append('## 讲义原文')
            chunks.append('')
            chunks.append(body)
            chunks.append('')
        else:
            chunks.append('## 讲义原文')
            chunks.append('')
            chunks.append('> 本页在课件中是纯图文版式（无文字层），内容以页图与下面的 OCR 文本为准。')
            chunks.append('')
        if reds:
            chunks.append('> [!important] 本页标红（老师强调）')
            for r in reds:
                chunks.append(f'> - =={r}==')
            chunks.append('')
        if ocr_lines and (not body or sum(len(b['text']) for b in blocks) < 80):
            chunks.append('> [!note]- 页面文字（OCR 机读，可能有错字，以页图为准）')
            for l in ocr_lines:
                chunks.append(f'> {l}')
            chunks.append('')
        prev_fn = meta[n - 2]['title'] if n - 2 >= 0 and n - 1 >= 1 else None
        nav = f"[[00 第{c['n']}章 {c['short']} 导航|本章索引]]"
        left = f"[[p{n-1:03d} {san(meta[n-2]['title'])}|p{n-1:03d}]]" if n > 1 else '（首篇）'
        right = f"[[p{n+1:03d} {san(meta[n]['title'])}|p{n+1:03d}]]" if n < TOTAL else '（末篇）'
        chunks.append('## 关联')
        chunks.append('')
        chunks.append(f'- ← {left} · {nav} · {right} →')
        chunks.append(f"- 同组：{m['sec']} · 全章：[[00 第{c['n']}章 {c['short']} 导航|{c['short']}]]")
        cps = card_pages.get(n, [])
        if cps:
            chunks.append('- 概念卡：' + ' · '.join('[[%s]]' % x for x in cps))
        chunks.append('')
        open(rel, 'w', encoding='utf-8').write('\n'.join(chunks))
        stats['total'] += 1
        stats['red'] += len(reds)
        stats['img'] += 1

    # ---- 章导航
    for c in CHAPTERS:
        sub = [m for m in meta if m['c']['n'] == c['n']]
        nred = sum(len(reds_clean(m['p']['reds'])) for m in sub)
        L = ['---', 'type: 索引', f"chapter: {c['n']}", f'chapter_name: "{c["name"]}"',
             'section: "全章"', 'tags:', f'  - {COURSE}', f'  - 章/{c["n"]:02d}', '  - 索引',
             'aliases:', f'  - "{c["name"]}"', f'  - "{c["short"]} 导航"', '---', '',
             f"# {c['name']} · 索引", '',
             f"> {c['end']-c['start']+1} 页幻灯片（p{c['start']:03d}–p{c['end']:03d}）· "
             f"{len(BANDS[c['n']])} 个分组 · {nred} 条标红重点。原文页一律 `幻灯片 n/{TOTAL}`。", '',
             '## 分组地图', '']
        for a, b, name in BANDS[c['n']]:
            grp = [m for m in sub if a <= m['n'] <= b]
            if not grp:
                continue
            L.append(f'### {name}')
            L.append('')
            for m in grp:
                L.append(f"- [[{m['fn'][:-3]}|{m['title']}]]")
            L.append('')
            L.append(f"`p{a:03d}–p{grp[-1]['n']:03d}` · {len(grp)} 页")
            L.append('')
        L.append('## 全章标红重点')
        L.append('')
        if nred:
            L.append('> [!important] 课件红字（逐页汇总，点页号回原文）')
            for m in sub:
                for r in reds_clean(m['p']['reds']):
                    L.append(f"> - [[{m['fn'][:-3]}|p{m['n']:03d}]] · {r}")
        else:
            L.append('> 本章课件无标红文字。')
        L.append('')
        L.append('## 关联')
        L.append('')
        prev_c = CHAPTERS[c['n'] - 2] if c['n'] > 1 else None
        next_c = CHAPTERS[c['n']] if c['n'] < len(CHAPTERS) else None
        links = []
        if prev_c:
            links.append(f"[[00 第{prev_c['n']}章 {prev_c['short']} 导航]]")
        links.append('[[01 弧焊电源 MOC]]')
        if next_c:
            links.append(f"[[00 第{next_c['n']}章 {next_c['short']} 导航]]")
        L.append('- ← ' + ' · '.join(links) + ' →')
        L.append('')
        open(os.path.join(ROOT, c['folder'], f"00 第{c['n']}章 {c['short']} 导航.md"), 'w', encoding='utf-8').write('\n'.join(L))

    # ---- 自动索引：02 目录与页码对照 / 05 红色重点总表
    os.makedirs(os.path.join(ROOT, '00 索引'), exist_ok=True)
    L = ['---', 'type: 索引', 'tags:', f'  - {COURSE}', '  - 索引', 'aliases:',
         '  - 目录与页码对照', '  - 页码对照', '---', '', '# 目录与页码对照', '',
         f"> 本课件 PDF 共 {TOTAL} 页，页脚 `Slide n` 与 PDF 页序号**完全一致**（全文校验 273/273 一致，偏移 = 0）："
         '`幻灯片 n` = `PDF 第 n 页`。每篇笔记顶部 `📄 原文` 直接跳到该页。', '',
         '## 章与页码', '', '| 章 | 短名 | 页范围 | 页数 | 目录 |', '| --- | --- | --- | --- | --- |']
    for c in CHAPTERS:
        L.append(f"| {c['name']} | {c['short']} | p{c['start']:03d}–p{c['end']:03d} | {c['end']-c['start']+1} "
                 f"| [[00 第{c['n']}章 {c['short']} 导航]] |")
    L += ['', '## 分组（内容线索）', '']
    for c in CHAPTERS:
        L.append(f"### {c['name']}")
        L.append('')
        L.append('| 分组 | 页 |')
        L.append('| --- | --- |')
        for a, b, name in BANDS[c['n']]:
            L.append(f'| {name} | p{a:03d}–p{b:03d} |')
        L.append('')
    open(os.path.join(ROOT, '00 索引', '02 目录与页码对照.md'), 'w', encoding='utf-8').write('\n'.join(L))

    L = ['---', 'type: 索引', 'tags:', f'  - {COURSE}', '  - 索引', 'aliases:',
         '  - 红色重点总表', '  - 红字考点', '---', '', '# 红色重点总表', '',
         f"> 课件里所有红字（老师强调）逐条汇总，共 **{stats['red']} 条**。点页号回原文；"
         '每条都保留了原句，笔记正文里对应位置也做了 `==高亮==`。', '']
    for c in CHAPTERS:
        sub = [m for m in meta if m['c']['n'] == c['n']]
        rows = [(m, r) for m in sub for r in reds_clean(m['p']['reds'])]
        L.append(f"## {c['name']}")
        L.append('')
        if not rows:
            L.append('> 本章无标红文字。')
            L.append('')
            continue
        for m, r in rows:
            L.append(f"- [[{m['fn'][:-3]}|p{m['n']:03d}]] · {r}")
        L.append('')
    open(os.path.join(ROOT, '00 索引', '05 红色重点总表.md'), 'w', encoding='utf-8').write('\n'.join(L))

    json.dump([{k: m[k] for k in ('n', 'title', 'sec', 'kind', 'fn')} | {'chapter': m['c']['n'],
               'folder': m['c']['folder'], 'reds': reds_clean(m['p']['reds'])} for m in meta],
              open(os.path.join(ROOT, 'tools/meta.json'), 'w'), ensure_ascii=False, indent=1)
    print('notes', stats['total'], 'red', stats['red'])


if __name__ == '__main__':
    main()
