# -*- coding: utf-8 -*-
"""校验：wikilink 死链、笔记数、标红数、概念卡数。"""
import os, re, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files, names = [], collections.Counter()
for dp, dn, fn in os.walk(ROOT):
    if '.obsidian' in dp or '/tools' in dp:
        continue
    for f in fn:
        rel = os.path.relpath(os.path.join(dp, f), ROOT)
        files.append(rel)
        names[f] += 1
        if f.endswith('.md'):
            names[f[:-3]] += 1

LINK = re.compile(r'!?\[\[([^\]]+)\]\]')
dead, total = [], 0
for rel in files:
    if not rel.endswith('.md'):
        continue
    for m in LINK.finditer(open(os.path.join(ROOT, rel), encoding='utf-8').read()):
        target = m.group(1).split('|')[0].split('#')[0].strip().rstrip('\\')
        if not target:
            continue
        total += 1
        cand = [target, target + '.md', os.path.basename(target)]
        if not any(c in names for c in cand):
            dead.append((rel, target))
notes = sum(1 for f in files if re.match(r'^(0\d) [^/]+/p\d{3} .*\.md$', f))
cards = sum(1 for f in files if f.startswith('09 概念卡/'))
reds = 0
for rel in files:
    if rel.startswith('00 索引') and rel.endswith('.md'):
        continue
    if not rel.endswith('.md'):
        continue
    reds += len(re.findall(r'^> - ==', open(os.path.join(ROOT, rel), encoding='utf-8').read(), re.M))
print('md files', sum(1 for f in files if f.endswith('.md')), '| 讲义页', notes, '| 概念卡', cards)
print('wikilinks', total, '| 死链', len(dead))
for a, b in dead[:15]:
    print('  DEAD', a, '->', b)
print('标红条目（callout）', reds)
