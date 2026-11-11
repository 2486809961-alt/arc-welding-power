# -*- coding: utf-8 -*-
"""生成 13 手写笔记/01 手写重点汇总.md（按章汇总划线句）。"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = json.load(open(os.path.join(ROOT, 'tools/hw.json'), encoding='utf-8'))
CH = {1: '第1章 绪论', 2: '第2章 基本电气特性', 3: '第3章 弧焊变压器',
      4: '第4章 电子控制型', 5: '第5章 晶闸管整流器', 6: '第6章 逆变式'}
TAG = {'1~5周': 'w1', '6~8周': 'w2'}
name = {}
for src in TAG:
    d = os.path.join(ROOT, '13 手写笔记', src)
    for f in os.listdir(d):
        if f.endswith('.md'):
            name[f.split(' ')[0]] = '%s/%s' % (src, f[:-3])
total = sum(len(r['hl']) for r in H)
L = ['---', 'type: 索引', 'tags:', '  - 弧焊电源', '  - 索引', '  - 手写笔记', 'aliases:',
     '  - 手写重点汇总', '  - 划线重点', '---', '', '# 手写笔记 · 划线重点汇总', '',
     '> 两份拍照笔记里**被划成重点的句子**按章汇总，共 %d 条。每条后面点页码回原页对图。' % total,
     '> 判定口径：句中含「定义/特点/要求/结论/公式」类词，或与课件原句 2-gram 重合 ≥85%。'
     'OCR 有错字（如"弧"误识为"孤"），以页图为准。', '']
for ch in range(1, 7):
    rows = [(r, l) for r in H if r['ch'] == ch for l in r['hl']]
    if not rows:
        continue
    L += ['## %s（%d 条）' % (CH[ch], len(rows)), '']
    for r, l in rows:
        key = 'h-%s-%03d' % (TAG[r['src']], r['page'])
        L.append('- ==%s== · [[%s|%s p%03d]]' % (l, name[key], r['src'], r['page']))
    L.append('')
L += ['## 关联', '', '- [[00 手写笔记总览]] · [[01 弧焊电源 MOC]] · [[05 红色重点总表|课件标红总表]]', '']
open(os.path.join(ROOT, '13 手写笔记', '01 手写重点汇总.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('划线重点', total, '条')
