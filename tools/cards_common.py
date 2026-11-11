import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = json.load(open(os.path.join(ROOT, 'tools/meta.json'), encoding='utf-8'))
BY = {m['n']: m for m in META}

def link(n):
    m = BY[n]
    return '[[%s|p%03d]]' % (m['fn'][:-3], n)

def link_t(n):
    """表格单元格内用：别名竖线转义"""
    return link(n).replace('|', '\\|')


def sect(n):
    m = BY[n]
    s = m['sec'] if m['sec'] and m['sec'] != '本章导览' else '—'
    return re.sub(r'\s+', ' ', s)

def card(name, chapter, section, aliases, definition, points, pages, related, related_cards='- 章：[[%s]]'):
    nav = {1: '00 第1章 绪论 导航', 2: '00 第2章 基本电气特性 导航', 3: '00 第3章 弧焊变压器 导航',
           4: '00 第4章 电子控制型 导航', 5: '00 第5章 晶闸管整流器 导航',
           6: '00 第6章 逆变式 导航'}[chapter]
    L = ['---', 'type: 概念', 'chapter: %d' % chapter, 'section: "%s"' % section, 'tags:',
         '  - 弧焊电源', '  - 章/%02d' % chapter, '  - 概念', 'aliases:']
    for a in aliases:
        L.append('  - %s' % a)
    L += ['---', '', '# %s' % name, '', '## 一句话定义', '', '> %s' % definition, '', '## 要点', '']
    for i, p in enumerate(points, 1):
        L.append('%d. %s' % (i, p))
    L += ['', '## 讲义出处', '', '| 幻灯片 | 小节 | 内容 |', '| --- | --- | --- |']
    for n, desc in pages:
        L.append('| %s | %s | %s |' % (link_t(n), sect(n), desc))
    L += ['', '## 关联', '']
    L.append('- 同类：' + ' · '.join(related))
    L.append('- 章：[[%s]]' % nav)
    L.append('- 索引：[[01 弧焊电源 MOC]] · [[05 红色重点总表|红色重点总表]]')
    L.append('')
    path = os.path.join(ROOT, '09 概念卡', name + '.md')
    open(path, 'w', encoding='utf-8').write('\n'.join(L))
    return path
