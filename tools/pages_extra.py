# -*- coding: utf-8 -*-
"""生成 公式库 / 术语表 / 附表数据 / 例题 / 图谱 canvas / MOC / 概念地图。"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cards_common import META, BY, link, link_t, ROOT

os.makedirs(os.path.join(ROOT, '10 公式库'), exist_ok=True)
os.makedirs(os.path.join(ROOT, '11 附表数据'), exist_ok=True)
os.makedirs(os.path.join(ROOT, '12 术语'), exist_ok=True)
os.makedirs(os.path.join(ROOT, '07 例题'), exist_ok=True)
os.makedirs(os.path.join(ROOT, '08 图谱'), exist_ok=True)

FM = ['---', 'type: 索引', 'tags:', '  - 弧焊电源', '  - 索引']
NAV = {1: '00 第1章 绪论 导航', 2: '00 第2章 基本电气特性 导航', 3: '00 第3章 弧焊变压器 导航',
       4: '00 第4章 电子控制型 导航', 5: '00 第5章 晶闸管整流器 导航', 6: '00 第6章 逆变式 导航'}

# ---------------- 10 公式库
L = FM + ['aliases:', '  - 公式总表', '  - 公式速查', '---', '', '# 公式总表', '',
          '> 课件里出现的算式一览，按章排；点页码回原页核对上下文。**公式写法逐字取自课件**，'
          'OCR 或有噪声的地方已注明"以页图为准"。', '']

def row(no, f, name, cond, page):
    return f'| ({no}) | {f} | {name} | {cond} | {link_t(page)} |'

L += ['## 第2章 基本电气特性', '', '| 编号 | 公式 | 名称 | 条件/说明 | 页 |', '| --- | --- | --- | --- | --- |',
      row(1, r'$U_f=U_K+U_C+U_A$', '电弧电压＝三区压降之和', '弧柱压降与弧长成正比', 26),
      row(2, r'$U_y=f(I_y)$', '外特性定义式', '电源内参数一定、改变负载', 43),
      row(3, r'$U_y=E-I_y r_o$', '外特性方程一般式', '$r_o$：等效内阻抗；$r_o>0$ 下降，$r_o=0$ 平', 44),
      row(4, r'$U_0>(1.8\sim2.25)U_f$', '交流电源空载电压下限', '保证交流电弧稳定燃烧', 64),
      row(5, r'$U_y=0\ \Rightarrow\ I_y=I_{wd}$', '稳态短路电流定义', '下降特性中电压为零时的电流', 65),
      row(6, r'$U_2=20+0.04I_2\ (I_2\le600\text{A}),\ U_2=44\ (I_2>600\text{A})$', '焊条电弧焊约定负载特性',
          'TIG：$10+0.04I_2$；MIG：$14+0.05I_2$；埋弧：$20+0.04I_2$', 69),
      row(7, r'$I_{2\max}\ge100\%\,I_{2r}$', '下降特性电源可调上限', '额定电流 $I_{2r}$ 的百分比', 70),
      row(8, r'$I_{2\min}\le20\%\,I_{2r}$', '焊条电弧焊可调下限', '下限越小调节范围越宽', 70),
      row(9, r'$FC=\dfrac{t}{t+t_0}\times100\%$', '负载持续率', '与温升、额定电流绑定；原文见页图（OCR）', 73),
      '']

L += ['## 第3章 弧焊变压器', '', '| 编号 | 公式 | 名称 | 条件/说明 | 页 |', '| --- | --- | --- | --- | --- |',
      row(10, r'$B=\mu H,\quad \Phi=B\cdot S$', '磁感应强度、磁通', '$\mu$ 为磁导率', 85),
      row(11, r'$\Phi=\dfrac{F_m}{R_m},\quad R_m=\dfrac{l}{\mu S},\quad F_m=NI$', '磁路欧姆定律',
          '铁心饱和后 $\mu$、$R_m$ 均非常数，只作定性分析', 88),
      row(12, r'$E=4.44\,fN\Phi_m$', '感应电动势有效值', '一次/二次绕组同式，下标区别', 98),
      row(13, r'$X=\omega L$', '感抗', '电抗器上 $X=\omega L$，改变气隙即改变 $L$', 113),
      row(14, r'$U_f=U_0-I_f X_z$', '动铁心式外特性方程', '$X_z=X_1+X_2+X$ 为总等效漏抗', 119),
      row(15, r'$\left(\dfrac{U_f}{U_0}\right)^2+\left(\dfrac{I_f X_z}{U_0}\right)^2=1$',
          '外特性曲线方程（椭圆）', '课件表述：以 $U_0/X_z$、$U_0$ 为长短轴的四分之一椭圆', 110),
      row(16, r'$k_M=0\sim1$', '磁耦合系数', '$k_M$ 越小漏磁越多、漏抗越大', 101),
      '']

L += ['## 第4章 电子控制型弧焊电源', '', '| 编号 | 公式 | 名称 | 条件/说明 | 页 |', '| --- | --- | --- | --- | --- |',
      row(17, r'$U_H=S\,H\,I\,B$', '磁放大器输出（课件原文）', '磁场平衡式磁放大器的控制关系，以页图为准', 185),
      row(18, r'$I_dN_d=I_sN_s$', '磁放大器磁场平衡', '$N_d,I_d$ 检测线圈；$N_s,I_s$ 补偿线圈', 186),
      '']

L += ['## 第5章 晶闸管弧焊整流器', '', '| 编号 | 公式 | 名称 | 条件/说明 | 页 |', '| --- | --- | --- | --- | --- |',
      row(19, r'$U_D=1.17U_2(1+\cos\alpha)$', '三相半控桥输出平均电压', '半控桥（三晶闸管+三二极管）', 209),
      row(20, r'$U_D=2.34U_2\cos\alpha$', '三相全控桥输出平均电压', '$\alpha=90^\circ$ 时输出为零', 208),
      row(21, r'$U_D=1.35U_2\cos\alpha$', '六相半波输出平均电压', '$\alpha=60^\circ$ 输出波形临界连续', 215),
      row(22, r'$U_D=1.17U_2\cos\alpha$', '双反星形带平衡电抗器输出', '$\alpha=0^\circ$ 时 $U_D=1.17U_2$', 222),
      '']

L += ['## 第6章 逆变式弧焊电源', '', '| 编号 | 公式 | 名称 | 条件/说明 | 页 |', '| --- | --- | --- | --- | --- |',
      row(23, r'$f\ \propto\ \dfrac{1}{N\,S}$', '频率与匝数·铁心截面成反比', '$U$、$B_m$ 确定后成立——逆变电源小型化的根据', 247),
      row(24, r'$U_{av}\propto D$', '输出电压与占空比', 'PWM 定频调宽，占空比决定电压平均值', 269),
      '']
L += ['## 说明', '',
      '- 编号 (1)–(24) 只为检索方便，与课件原编号无关；课件正文里出现的 $\alpha$、$U_2$、$I_2$ 等符号沿用课件写法。',
      '- 标"以页图为准"的公式，其文字层只有 OCR 结果，正式引用前请对照页图。', '']
open(os.path.join(ROOT, '10 公式库', '公式总表.md'), 'w', encoding='utf-8').write('\n'.join(L))

# ---------------- 12 术语
T = [('弧焊电源', 'arc welding power source', '对电弧供电、具有焊接工艺电气特性的电源装置', '1'),
     ('焊接电弧', 'welding arc', '气体介质中强烈而持久的放电现象，低电压大电流', '2'),
     ('引弧', 'arc ignition / arc striking', '建立电弧的过程，分接触引弧与非接触引弧', '2'),
     ('热电离', 'thermal ionization', '中性粒子受热而电离', '2'),
     ('场致电离', 'field ionization', '中性粒子受电场作用而电离', '2'),
     ('光电离', 'photo ionization', '吸收光子能量而电离', '2'),
     ('碰撞电离', 'impact ionization', '粒子碰撞传递能量而电离', '2'),
     ('热发射', 'thermionic emission', '电极受热发射电子', '2'),
     ('阴极区', 'cathode region', '电弧靠近阴极的区域，压降 3–20 V', '2'),
     ('阳极区', 'anode region', '电弧靠近阳极的区域，压降 2–10 V', '2'),
     ('弧柱', 'arc column', '电弧中间区域，压降与弧长成正比', '2'),
     ('电弧静特性', 'static characteristic of arc', '稳态下电弧电压与电流的关系曲线', '2'),
     ('电弧动特性', 'dynamic characteristic of arc', '电流快速变化时的电弧电压—电流关系', '2'),
     ('外特性', 'external characteristic', '电源稳态输出电压与电流的关系', '2'),
     ('下降外特性', 'drooping characteristic', '电压随电流增大而下降的外特性', '2'),
     ('平特性', 'flat characteristic', '电压基本不随电流变化的外特性', '2'),
     ('恒流特性', 'constant current characteristic', '电流近似不随电压变化的外特性', '2'),
     ('恒流带外拖', 'constant current with drooping tail', '焊条电弧焊电源理想的外特性形状', '2'),
     ('空载电压', 'open-circuit voltage', '输出开路时的电压，决定引弧与稳弧', '2'),
     ('稳态短路电流', 'steady short-circuit current', '外特性上电压为零时对应的电流', '2'),
     ('调节特性', 'adjusting characteristic', '输出电流电压的可调性（外特性曲线族）', '2'),
     ('约定负载特性', 'conventional load characteristic', '按标准约定、用于比较电源的负载关系', '2'),
     ('负载持续率', 'duty cycle', '负载时间占工作周期的百分比', '2'),
     ('动特性', 'dynamic characteristic', '负载突变时电源输出的动态响应', '2'),
     ('飞溅率', 'spatter rate', '飞溅损失质量占焊丝熔化质量的百分比', '2'),
     ('弧焊变压器', 'arc welding transformer', '最简单的交流弧焊电源', '3'),
     ('漏抗', 'leakage reactance', '漏磁通对应的电抗，决定下降外特性', '3'),
     ('磁路欧姆定律', 'Ohm law of magnetic circuit', '磁通＝磁动势/磁阻', '3'),
     ('磁阻', 'reluctance', '磁路对磁通的阻碍，$R_m=l/(\\mu S)$', '3'),
     ('磁耦合系数', 'magnetic coupling coefficient', '$k_M$，反映一二次绕组耦合程度', '3'),
     ('增强漏磁式', 'enhanced leakage flux type', '人为增大漏抗以获得下降外特性', '3'),
     ('动铁心式', 'moving iron core type', '移动铁心改变漏抗（BX1）', '3'),
     ('动绕组式', 'moving winding type', '移动绕组改变漏抗（BX3）', '3'),
     ('抽头式', 'tap-changing type', '改变抽头匝数分级调节（BX6）', '3'),
     ('电抗器', 'reactor', '串入回路的带铁心线圈，提供电抗压降', '3'),
     ('电力半导体器件', 'power semiconductor device', '承担大功率通断的半导体开关', '4'),
     ('晶闸管', 'thyristor (SCR)', '导通时刻可控的二极管式器件', '4'),
     ('场效应管', 'MOSFET', '电压控制型开关器件，驱动功率小', '4'),
     ('绝缘栅双极型晶体管', 'IGBT', '兼有 MOSFET 与 GTR 优点的复合器件', '4'),
     ('触发角', 'firing angle', '晶闸管开始导通的相位角', '4'),
     ('反馈控制', 'feedback control', '取输出量反馈以塑造外特性形状', '4'),
     ('晶闸管弧焊整流器', 'thyristor rectifier power source', '晶闸管可控整流式弧焊电源', '5'),
     ('整流', 'rectification', '把交流变为直流', '5'),
     ('逆变', 'inversion', '把直流变为交流', '5'),
     ('半控桥', 'half-controlled bridge', '晶闸管与二极管混合的三相桥', '5'),
     ('六相半波', 'six-phase half-wave', '六绕组共阴极整流，每管导通 60°', '5'),
     ('平衡电抗器', 'interphase reactor', '使两组整流桥并联均流的电抗器', '5'),
     ('移相触发', 'phase-shift triggering', '改变触发脉冲相位来调压', '5'),
     ('逆变式弧焊电源', 'inverter arc welding power source', 'AC-DC-AC-DC 结构的高频电源', '6'),
     ('单端逆变电路', 'single-ended inverter', '变压器承受单向电流（正激/反激）', '6'),
     ('双端逆变电路', 'double-ended inverter', '变压器承受双向电流（推挽/半桥/全桥）', '6'),
     ('PWM', 'pulse width modulation', '定频调宽的时间比率控制', '6'),
     ('PFM', 'pulse frequency modulation', '定宽调频的时间比率控制', '6'),
     ('正激', 'forward converter', '一次有电流时二次有电流', '6'),
     ('反激', 'flyback converter', '一次无电流时二次才有电流', '6')]
L = FM + ['aliases:', '  - 术语表', '  - 术语中英对照', '---', '', '# 术语中英对照', '',
          '> 只收课件里出现、考试会写到的术语。英文为通用写法，课件以中文为主。', '',
          '| 中文 | 英文 | 一句话 | 章 |', '| --- | --- | --- | --- |']
for cn, en, d, ch in T:
    L.append(f'| {cn} | {en} | {d} | {ch} |')
L += ['', '## 关联', '', '- [[01 弧焊电源 MOC]] · [[04 概念地图]] · [[10 公式库/公式总表|公式总表]]', '']
open(os.path.join(ROOT, '12 术语', '术语中英对照.md'), 'w', encoding='utf-8').write('\n'.join(L))

# ---------------- 11 附表数据
pages = json.load(open(os.path.join(ROOT, 'tools/pages.json'), encoding='utf-8'))
tab, fig = [], []
for p in pages:
    txt = ' '.join(b['text'] for b in p['blocks'])
    for m in re.findall(r'表\s*\\d+\s*[-–—]\s*\\d+', txt):
        tab.append((p['pdf'], m, txt[:90]))
    for m in re.findall(r'图\s*\\d+\s*[-–—]\s*\\d+', txt):
        fig.append((p['pdf'], m, txt[:90]))
L = FM + ['aliases:', '  - 课件数据表汇总', '  - 图注索引', '---', '', '# 数据表与图注索引', '',
          '> 课件里的表格与带编号图，按出现页列出，点页号回原页看图/表。图注只记录课件自己写的编号，不描述图内容。', '',
          '## 表格', '']
if tab:
    L += ['| 编号 | 出现页 | 上下文 |', '| --- | --- | --- |']
    for n, name, ctx in tab:
        L.append(f'| {name} | {link_t(n)} | {ctx.replace("|", "/")[:70]} |')
else:
    L.append('> 课件文字层没有检索到编号表格。')
L += ['', '## 图', '']
if fig:
    L += ['| 编号 | 出现页 | 上下文 |', '| --- | --- | --- |']
    for n, name, ctx in fig:
        L.append(f'| {name} | {link_t(n)} | {ctx.replace("|", "/")[:70]} |')
else:
    L.append('> 课件文字层没有检索到编号图注（大量插图为纯图片，见各页页图）。')
L += ['', '## 页图说明', '',
      '每篇讲义页内嵌的 `pNNN.jpg` 页图（144 dpi 渲染）就是该页原始幻灯片，'
      '图上的曲线、波形、电路拓扑都以它为准；文字层的 OCR 只作检索辅助。', '']
open(os.path.join(ROOT, '11 附表数据', '数据表与图注索引.md'), 'w', encoding='utf-8').write('\n'.join(L))

# ---------------- 07 例题
def is_q(m):
    t = m['title'] + m['sec']
    return bool(re.search(r'(回顾|问题|思考|习题|练习|要求|重点与难点|难点)', t)) or m['kind'] == '小结'
qs = [m for m in META if is_q(m)]
L = FM + ['aliases:', '  - 例题与思考题', '  - 复习题', '---', '', '# 复习题与思考题', '',
          '> 课件里的回顾页、提问页与章末思考页汇总（课件未给标准答案，答案就在对应章的正文页里）。'
          '共 %d 页。' % len(qs), '']
for m in qs:
    L.append(f"### {m['title']} · p{m['n']:03d}")
    L.append('')
    p = next(x for x in pages if x['pdf'] == m['n'])
    lines = [b['text'] for b in p['blocks'] if b['kind'] != 'head'][:8]
    if not lines:
        ocr = json.load(open(os.path.join(ROOT, 'tools/ocr.json'), encoding='utf-8')).get(str(m['n']), [])
        lines = ['（本页为纯图文页，题目见页图）'] + [x for x in ocr if len(re.findall(r'[\u4e00-\u9fff]', x)) >= 4][:4]
    for ln in lines:
        L.append('- ' + ln)
    L.append('')
    L.append('→ 原文页：%s · 章导航：[[%s]]' % (link(m['n']), NAV[m['chapter']]))
    L.append('')
open(os.path.join(ROOT, '07 例题', '复习题与思考题.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('extra pages ok', len(qs), 'question pages')
