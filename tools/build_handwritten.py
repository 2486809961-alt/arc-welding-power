# -*- coding: utf-8 -*-
"""由 tools/hw.json 生成 13 手写笔记 的页面笔记、页图与总览。"""
import os, re, json, sys
import pymupdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFDIR = '/Users/jiarun/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files/wxid_fw6mlzx84ez622_b83e/temp/drag'
HW = json.load(open(os.path.join(ROOT, 'tools/hw.json'), encoding='utf-8'))
META = {m['n']: m for m in json.load(open(os.path.join(ROOT, 'tools/meta.json'), encoding='utf-8'))}
CH = {1: ('第1章 绪论', '绪论'), 2: ('第2章 基本电气特性', '基本电气特性'), 3: ('第3章 弧焊变压器', '弧焊变压器'),
      4: ('第4章 电子控制型', '电子控制型'), 5: ('第5章 晶闸管整流器', '晶闸管整流器'), 6: ('第6章 逆变式', '逆变式')}
NAV = {c: '00 第%d章 %s 导航' % (c, v[1]) for c, v in CH.items()}
SRCFILE = {'1~5周': '1~5周 焊接电源(1).pdf', '6~8周': '6~8周 焊接电源(差最后一节课)(1).pdf'}
TAG = {'1~5周': 'w1', '6~8周': 'w2'}
OUT = os.path.join(ROOT, '13 手写笔记')
IMGDIR = os.path.join(OUT, '页图')


def san(t):
    t = re.sub(r'[\\/:*?"<>|#^\[\]]', ' ', t).strip(' .。,，、')
    return re.sub(r'\s+', ' ', t)[:36]


def main():
    os.makedirs(IMGDIR, exist_ok=True)
    for tag in ('1~5周', '6~8周'):
        d = os.path.join(OUT, tag)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):          # 清掉旧命名残留
            if re.match(r'^h-[a-z0-9]+-\d{3} .*\.md$', f):
                os.remove(os.path.join(d, f))
        pg = [r for r in HW if r['src'] == tag]
        if not pg:
            continue
        doc = pymupdf.open(os.path.join(PDFDIR, SRCFILE[tag]))
        for r in pg:
            base = 'h-%s-%03d' % (TAG[tag], r['page'])
            ip = os.path.join(IMGDIR, base + '.jpg')
            if not os.path.exists(ip):
                pix = doc[r['page'] - 1].get_pixmap(dpi=110)
                open(ip, 'wb').write(pix.tobytes('jpeg', jpg_quality=75))
            r['img'] = base + '.jpg'
            r['fn'] = '%s %s' % (base, san(r['title']))
            r['file'] = r['fn'] + '.md'
    # 写页面笔记
    for tag in ('1~5周', '6~8周'):
        pg = sorted([r for r in HW if r['src'] == tag], key=lambda x: x['page'])
        for i, r in enumerate(pg):
            ch = r['ch']
            name, short = CH[ch]
            L = ['---', 'type: 手写笔记', 'source: "%s"' % SRCFILE[tag],
                 'source_page: %d' % r['page'], 'week: "%s"' % tag,
                 'chapter: %d' % ch, 'chapter_name: "%s"' % name,
                 'kind: 讲义翻拍', 'ocr_quality: %s' % r.get('ocr', '一般'), 'tags:', '  - 弧焊电源', '  - 手写笔记',
                 '  - 周/%s' % tag, '  - 章/%02d' % ch, 'cssclass: 手写页', 'aliases:',
                 '  - "%s"' % san(r['title']), '  - %s' % ('h-%s-%03d' % (TAG[tag], r['page'])), '---', '']
            L += ['> 📷 原图：`%s` 第 %d 页（整页扫描，本库内嵌 `%s`）' % (SRCFILE[tag], r['page'], r['img']), '']
            L += ['# %s' % san(r['title']), '']
            L += ['![[%s|620]]' % r['img'], '']
            lines = r['lines'] if r.get('ocr') != '差' else []
            if lines:
                L += ['## 本页文字（OCR 整理）', '']
                hls = set(r['hl'])
                for l in lines:
                    L.append('- ' + ('==%s==' % l if l in hls else l))
                L.append('')
            else:
                L += ['## 本页文字（OCR 整理）', '',
                      '> 这一页基本是手写/画图，OCR 识出的字不可用（已隐藏），**请看上面的原图**。', '']
            if r['hl']:
                L.append('> [!important] 本页重点（自动标记：含"定义/特点/要求/结论/公式"等，或与课件原句高度一致）')
                for h in r['hl']:
                    L.append('> - ==%s==' % h)
                L.append('')
            L.append('> [!note]- OCR 说明')
            L.append('> 文字由 macOS Vision 识别手写体/翻拍页面得到，**错字难免**（如"弧"误识为"孤"）；'
                     '重点标记据此推断，请以页图为准。')
            L.append('')
            if r['like']:
                L.append('## 对应讲义页')
                L.append('')
                for n in r['like']:
                    m = META[n]
                    L.append('- [[%s|p%03d]] · %s' % (m['fn'][:-3], n, m['title']))
                L.append('')
            prev = pg[i - 1] if i > 0 else None
            nxt = pg[i + 1] if i + 1 < len(pg) else None
            L.append('## 关联')
            L.append('')
            L.append('- ← %s · [[00 手写笔记总览|总览]] · %s →' % (
                ('[[%s|上一页]]' % prev['fn']) if prev else '（首张）',
                ('[[%s|下一页]]' % nxt['fn']) if nxt else '（末张）'))
            L.append('- 讲义：[[%s]] · 概念：[[04 概念地图]]' % NAV[ch])
            L.append('')
            open(os.path.join(OUT, tag, r['file']), 'w', encoding='utf-8').write('\n'.join(L))
    # 总览
    L = ['---', 'type: 索引', 'tags:', '  - 弧焊电源', '  - 索引', '  - 手写笔记', 'aliases:',
         '  - 手写笔记总览', '  - 拍照笔记', '---', '', '# 手写笔记总览', '',
         '> 两份拍照笔记（`1~5周 焊接电源(1).pdf` 62 页、`6~8周 焊接电源(差最后一节课)(1).pdf` 67 页）整理成 **%d** 篇页面笔记。'
         % len(HW), '> 每页都内嵌整页扫描图、OCR 文字、自动标记的重点，并挂回对应讲义页；属性区默认折叠（悬停展开）。', '',
         '## 怎么用', '',
         '1. **对图复核**：每页正文第一块就是原图，OCR 只作检索；',
         '2. **只看重点**：每页 `> [!important] 本页重点` 块，或直接看 [[01 手写重点汇总]]；',
         '3. **对照课件**：`## 对应讲义页` 指向本库讲义页，概念再用 [[04 概念地图]] 串；',
         '4. **属性折叠**：`.obsidian/snippets/折叠属性.css` 已启用，属性区压成一行，鼠标移入展开。', '',
         '## 统计', '',
         '| 周 | 页数 | 去重前 |', '| --- | --- | --- |',
         '| 1~5周 | %d | 62 |' % sum(1 for r in HW if r['src'] == '1~5周'),
         '| 6~8周 | %d | 67 |' % sum(1 for r in HW if r['src'] == '6~8周'), '']
    for tag in ('1~5周', '6~8周'):
        pg = sorted([r for r in HW if r['src'] == tag], key=lambda x: x['page'])
        L += ['## %s（%d 页）' % (tag, len(pg)), '']
        for ch in range(1, 7):
            sub = [r for r in pg if r['ch'] == ch]
            if not sub:
                continue
            L += ['### %s · %d 页' % (CH[ch][0], len(sub)), '']
            for r in sub:
                L.append('- [[%s|%s 第%03d页]] · %s' % (r['fn'], tag, r['page'], san(r['title'])))
            L.append('')
    L += ['## 关联', '', '- [[01 弧焊电源 MOC]] · [[00 关于本知识库]] · [[05 红色重点总表|红色重点总表]]', '']
    open(os.path.join(OUT, '00 手写笔记总览.md'), 'w', encoding='utf-8').write('\n'.join(L))
    print('手写笔记页', len(HW), '页图', len(os.listdir(IMGDIR)))


if __name__ == '__main__':
    main()
