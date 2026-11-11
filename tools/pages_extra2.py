# -*- coding: utf-8 -*-
import sys, os, json, re, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cards_common import META, BY, link, ROOT

CH = [(1, '第一章 绪论', '绪论', 1, 16), (2, '第二章 弧焊电源的基本电气特性', '基本电气特性', 17, 82),
      (3, '第三章 弧焊变压器', '弧焊变压器', 83, 135), (4, '第四章 电子控制型弧焊电源', '电子控制型', 136, 188),
      (5, '第五章 晶闸管弧焊整流器', '晶闸管整流器', 189, 235), (6, '第六章 逆变式弧焊电源', '逆变式', 236, 273)]
NAV = {c[0]: '00 第%d章 %s 导航' % (c[0], c[2]) for c in CH}
cards = sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, '09 概念卡')) if f.endswith('.md'))
card_ch = {}
for c in cards:
    txt = open(os.path.join(ROOT, '09 概念卡', c + '.md'), encoding='utf-8').read()
    m = re.search(r'^chapter:\s*(\d+)', txt, re.M)
    card_ch[c] = int(m.group(1)) if m else 0

# ---------- 修 07 例题的章链接
p7 = os.path.join(ROOT, '07 例题', '复习题与思考题.md')
t = open(p7, encoding='utf-8').read()
t = re.sub(r'→ 原文页：(\[\[[^\]]+\]\]) · 章导航：\[\[00 第(\d)章 导航\]\]',
           lambda m: '→ 原文页：%s · 章导航：[[%s]]' % (m.group(1), NAV[int(m.group(2))]), t)
open(p7, 'w', encoding='utf-8').write(t)

# ---------- 08 课程地图 canvas
nodes, edges = [], []

def text_node(i, txt, x, y, w, h, color='4'):
    nodes.append(dict(id=i, type='text', text=txt, x=x, y=y, width=w, height=h, color=color))

text_node('course', '# 电力电子和焊接电源\n273 页课件 · 6 章\n[[01 弧焊电源 MOC]]', -60, -320, 420, 160, '1')
for c in CH:
    text_node('ch%d' % c[0], '# %s\np%03d–p%03d · %d 页\n[[%s]]' % (c[1], c[3], c[4], c[4] - c[3] + 1, NAV[c[0]]),
              (-560 + (c[0] - 1) * 400), 40, 360, 140, '5')
    edges.append(dict(id='e-ch%d' % c[0], fromNode='course', toNode='ch%d' % c[0], label='第%d章' % c[0]))
json.dump(dict(nodes=nodes, edges=edges), open(os.path.join(ROOT, '08 图谱', '课程地图.canvas'), 'w'),
          ensure_ascii=False, indent=1)

# ---------- 08 概念网 canvas
nodes, edges = [], []
for idx, c in enumerate(CH):
    text_node('g%d' % c[0], '# %s' % c[2], -700 + idx * 520, -300, 420, 90, '5')
for i, name in enumerate(cards):
    ch = card_ch.get(name, 1)
    col = i % 4
    row = i // 4
    nodes.append(dict(id='c%d' % i, type='file', file='09 概念卡/%s.md' % name,
                      x=-700 + (ch - 1) * 520, y=-160 + row * 120, width=420, height=90, color='6'))
    edges.append(dict(id='e%d' % i, fromNode='g%d' % ch, toNode='c%d' % i))
json.dump(dict(nodes=nodes, edges=edges), open(os.path.join(ROOT, '08 图谱', '概念网.canvas'), 'w'),
          ensure_ascii=False, indent=1)

# ---------- 01 MOC
reds = {c[0]: sum(len([1 for r in m['reds']]) for m in META if m['chapter'] == c[0]) for c in CH}
L = ['---', 'type: 索引', 'tags:', '  - 弧焊电源', '  - 索引', '  - MOC', 'aliases:',
     '  - MOC', '  - 弧焊电源总索引', '  - 首页', '---', '', '# 弧焊电源 MOC', '',
     '> 《电力电子和焊接电源》课件全 6 章 / **273 页幻灯片**，逐页一篇笔记 + %d 张概念卡 + 公式库；'
     '每条结论都能点回原页，红字重点单独汇总。' % len(cards), '',
     '```mermaid', 'graph LR', '  A[第1章 绪论] --> B[第2章 基本电气特性]',
     '  B --> C[第3章 弧焊变压器]', '  B --> D[第4章 电子控制型]', '  D --> E[第5章 晶闸管整流器]',
     '  D --> F[第6章 逆变式]', '  C --> E', '  E --> F', '```', '',
     '## 快速入口', '', '| 我要… | 去 |', '| --- | --- |',
     '| 系统学一遍 | [[03 学习路径]] |', '| 查公式 | [[公式总表]] |',
     '| 按概念跳转 | [[04 概念地图]] |', '| 只看老师标红 | [[05 红色重点总表]] |',
     '| 核对页码 | [[02 目录与页码对照]] |', '| 做复习题 | [[复习题与思考题]] |',
     '| 查表查图 | [[数据表与图注索引]] |', '| 中英术语 | [[术语中英对照]] |',
     '| 了解建库方式 | [[00 关于本知识库]] |', '', '## 六章', '']
for c in CH:
    sub = [m for m in META if m['chapter'] == c[0]]
    L += ['### %s' % c[1], '',
          '`%d 页` · `p%03d–p%03d` · `%d 条标红` · 导航：[[%s]]' % (c[4] - c[3] + 1, c[3], c[4], reds[c[0]], NAV[c[0]]),
          '', '首篇：%s　末篇：%s' % (link(sub[0]['n']), link(sub[-1]['n'])), '']
L += ['## 全库统计', '',
      '| 项 | 数 |', '| --- | --- |',
      '| 讲义页 | %d |' % len(META),
      '| 概念卡 | %d |' % len(cards),
      '| 章导航 | 6 |',
      '| 标红重点 | %d |' % sum(reds.values()),
      '| 幻灯片 | 273 |', '']
open(os.path.join(ROOT, '00 索引', '01 弧焊电源 MOC.md'), 'w', encoding='utf-8').write('\n'.join(L))

# ---------- 04 概念地图
L = ['---', 'type: 索引', 'tags:', '  - 弧焊电源', '  - 索引', 'aliases:',
     '  - 概念地图', '  - 概念索引', '---', '', '# 概念地图', '',
     '> %d 张原子概念卡按章归类。想按"问题"查（"为什么外特性要下降""逆变为什么轻"）从这里进。' % len(cards), '']
for c in CH:
    L += ['## %s' % c[1], '']
    cs = [x for x in cards if card_ch.get(x) == c[0]]
    L.append(' · '.join('[[%s]]' % x for x in cs) if cs else '（本章概念已并入相邻章卡片）')
    L.append('')
L += ['## 跨章线索', '',
      '- 负载 → 特性：[[焊接电弧]] → [[电弧静特性]] → [[外特性]] → [[外特性形状的选择]]',
      '- 稳定 → 可选：[[电源—电弧系统稳定条件]] → [[调节特性]] → [[动特性]]',
      '- 器件 → 电路：[[电力半导体器件]] → [[晶闸管]] → [[晶闸管弧焊整流器]] → [[触发电路]]',
      '- 器件 → 逆变：[[绝缘栅双极型晶体管]] → [[逆变主电路]] → [[PWM 控制]] → [[逆变式弧焊电源的特点]]',
      '', '## 关联', '', '- [[01 弧焊电源 MOC]] · [[12 术语/术语中英对照|术语中英对照]] · [[公式总表]]', '']
open(os.path.join(ROOT, '00 索引', '04 概念地图.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('moc/map/canvas ok, cards', len(cards))
