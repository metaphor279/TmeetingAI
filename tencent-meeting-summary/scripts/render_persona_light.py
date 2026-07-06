#!/usr/bin/env python3
"""会议人格·轻量版 —— HTML 渲染器(暗色科技 HUD 风)。
用法: python3 render_persona_light.py <STATS_JSON(来自 persona_light_stats.py)> <OUT_HTML> [PERIOD]

版式: 深空黑蓝底 + 青蓝霓虹描边 + HUD 角标 + 网格纹背景，发光雷达图；
自上而下: 顶栏(周期标+状态点) -> 称号(纯文字渐变,无高亮圈) -> 雷达图(中心叠加综合战力)
         -> 一句话总结(左侧霓虹竖线) -> 六维数据格(顶部发光细线+数值+说明)。
不含标签墙/评级角标/五角星等游戏化元素。
"""
import json, sys, math

def build_radar(sc, order, disp):
    cx, cy, R = 185, 178, 118; n = 6
    def pt(i, r):
        a = -math.pi/2 + i*2*math.pi/n
        return (cx+r*math.cos(a), cy+r*math.sin(a))
    grid = ''
    for g in [0.25, 0.5, 0.75, 1.0]:
        poly = ' '.join(f"{pt(i,R*g)[0]:.1f},{pt(i,R*g)[1]:.1f}" for i in range(n))
        grid += f'<polygon points="{poly}" fill="none" stroke="rgba(100,220,255,{0.34 if g==1 else 0.14})" stroke-width="{1.2 if g==1 else 0.7}"/>'
    axes = ''
    for i in range(n):
        x, y = pt(i, R)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="rgba(100,220,255,.16)" stroke-width="0.7"/>'
    dp = ' '.join(f"{pt(i,R*sc[order[i]]/100)[0]:.1f},{pt(i,R*sc[order[i]]/100)[1]:.1f}" for i in range(n))
    dots = ''; labels = ''
    for i in range(n):
        x, y = pt(i, R*sc[order[i]]/100)
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="#04101f" stroke="#5ad8ff" stroke-width="2.4"/>'
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="#5ad8ff"/>'
        lx, ly = pt(i, R+30); anc = 'middle'
        if lx > cx+12: anc = 'start'
        elif lx < cx-12: anc = 'end'
        dy = -4 if ly < cy-5 else (11 if ly > cy+5 else 0)
        labels += f'<text x="{lx:.1f}" y="{ly+dy:.1f}" text-anchor="{anc}" font-size="12.5" font-weight="700" letter-spacing="1" fill="#a9c4e8">{disp[order[i]]}</text>'
        labels += f'<text x="{lx:.1f}" y="{ly+dy+16:.1f}" text-anchor="{anc}" font-size="13.5" font-weight="800" fill="#5ad8ff" font-family="\'SF Mono\',Consolas,monospace">{sc[order[i]]}</text>'
    return (f'<svg viewBox="0 0 370 360" width="330" height="322" xmlns="http://www.w3.org/2000/svg">'
            f'<defs>'
            f'<radialGradient id="rf" cx="50%" cy="50%" r="62%">'
            f'<stop offset="0%" stop-color="rgba(90,216,255,.32)"/><stop offset="100%" stop-color="rgba(43,95,246,.06)"/></radialGradient>'
            f'<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
            f'<feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'</defs>'
            f'{grid}{axes}<polygon points="{dp}" fill="url(#rf)" stroke="#5ad8ff" stroke-width="2.2" filter="url(#glow)"/>{dots}{labels}</svg>')

def main(stats_json, out, period='2026 Q2'):
    d = json.load(open(stats_json))
    sc = d['scores']; order = d['order']; disp = d['disp']; avg = d['avg']
    oneline = d['oneline']; detail = d['detail']
    prefix = d.get('title_prefix',''); core = d.get('title_core', d['title'])
    title_html = f'<span class="pre">{prefix}</span><span class="core">{core}</span>' if prefix else f'<span class="core">{core}</span>'
    radar = build_radar(sc, order, disp)

    det_html = ''
    for i, x in enumerate(detail):
        det_html += (f'<div class="mcell"><span class="mtag">0{i+1}</span>'
                     f'<span class="mname">{x["name"]}</span>'
                     f'<span class="mval">{x["val"]}</span>'
                     f'<span class="msub">{x["sub"]}</span></div>')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>会议人格</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{display:flex;justify-content:center;align-items:flex-start;padding:44px 20px;background:#eef2fb;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased;}}
.card{{width:620px;border-radius:22px;position:relative;overflow:hidden;padding:34px 38px 30px;color:#dce6f7;
  background:
    radial-gradient(760px 340px at 8% -12%, rgba(60,140,255,.30), transparent 60%),
    radial-gradient(640px 380px at 105% 10%, rgba(90,216,255,.22), transparent 55%),
    radial-gradient(560px 420px at 55% 118%, rgba(43,95,246,.28), transparent 60%),
    linear-gradient(165deg,#070c1a 0%,#0a1330 45%,#060a16 100%);
  background-color:#070c1a;
  border:1px solid rgba(100,200,255,.35);
  box-shadow:0 36px 80px -28px rgba(10,20,60,.6), inset 0 1px 0 rgba(255,255,255,.05);}}
.card::before{{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(100,200,255,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(100,200,255,.055) 1px,transparent 1px);
  background-size:28px 28px;mask:radial-gradient(circle at 50% 18%,#000 0%,transparent 72%);}}
/* HUD 角标 */
.corner{{position:absolute;width:22px;height:22px;border-color:rgba(100,220,255,.75);z-index:3;}}
.corner.tl{{top:12px;left:12px;border-top:1.5px solid;border-left:1.5px solid;border-top-left-radius:6px;}}
.corner.tr{{top:12px;right:12px;border-top:1.5px solid;border-right:1.5px solid;border-top-right-radius:6px;}}
.corner.bl{{bottom:12px;left:12px;border-bottom:1.5px solid;border-left:1.5px solid;border-bottom-left-radius:6px;}}
.corner.br{{bottom:12px;right:12px;border-bottom:1.5px solid;border-right:1.5px solid;border-bottom-right-radius:6px;}}

.top{{display:flex;align-items:center;justify-content:space-between;position:relative;z-index:2;}}
.kicker{{font-size:11px;letter-spacing:3px;color:#7fd4ff;font-weight:700;font-family:'SF Mono',Consolas,monospace;display:flex;align-items:center;gap:7px;}}
.kicker .dot{{width:6px;height:6px;border-radius:50%;background:#5ad8ff;box-shadow:0 0 8px #5ad8ff;animation:blink 1.8s ease-in-out infinite;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
.kicker2{{font-size:10px;letter-spacing:1.5px;color:#5a6b90;font-family:'SF Mono',Consolas,monospace;}}

.title-zone{{margin-top:20px;position:relative;z-index:2;}}
.title-zone .lbl{{font-size:10.5px;letter-spacing:3px;color:#5a7bb0;font-weight:600;font-family:'SF Mono',Consolas,monospace;}}
.title-zone .name{{font-size:29px;font-weight:900;letter-spacing:-.2px;line-height:1.35;margin-top:9px;}}
.title-zone .name .pre{{color:#9fc4ff;font-weight:700;}}
.title-zone .name .core{{
  background:linear-gradient(96deg,#ffffff 10%,#8fe3ff 55%,#5ad8ff 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 2px 14px rgba(90,216,255,.45));}}

.radar-zone{{display:flex;justify-content:center;position:relative;z-index:2;margin-top:2px;}}
.radar{{position:relative;}}
.radar .core-v{{position:absolute;top:calc(50% - 4px);left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;}}
.radar .core-v .cv{{font-size:28px;font-weight:900;color:#fff;line-height:1;font-family:'SF Mono',Consolas,monospace;filter:drop-shadow(0 0 10px rgba(90,216,255,.7));}}
.radar .core-v .cl{{font-size:9.5px;letter-spacing:2px;color:#6f92c8;font-weight:700;margin-top:4px;font-family:'SF Mono',Consolas,monospace;}}

.verdict{{margin-top:4px;position:relative;z-index:2;background:rgba(100,200,255,.06);border:1px solid rgba(100,200,255,.22);border-left:2.5px solid #5ad8ff;border-radius:4px 14px 14px 4px;padding:15px 20px;}}
.verdict p{{font-size:13.5px;line-height:1.78;color:#bcd0ee;font-weight:400;}}
.verdict p b{{color:#7fe0ff;font-weight:700;}}

.metrics{{margin-top:18px;display:grid;grid-template-columns:repeat(3,1fr);gap:9px;position:relative;z-index:2;}}
.mcell{{position:relative;background:rgba(100,200,255,.05);border:1px solid rgba(100,200,255,.18);border-radius:12px;padding:14px 10px 11px;display:flex;flex-direction:column;align-items:center;gap:3px;text-align:center;overflow:hidden;}}
.mcell::before{{content:"";position:absolute;top:0;left:14px;right:14px;height:2px;background:linear-gradient(90deg,transparent,#5ad8ff,transparent);box-shadow:0 0 6px rgba(90,216,255,.6);}}
.mcell .mtag{{position:absolute;top:7px;right:9px;font-size:9px;color:#3f5c8a;font-weight:700;font-family:'SF Mono',Consolas,monospace;letter-spacing:1px;}}
.mcell .mname{{font-size:11px;color:#7fa0d0;font-weight:700;letter-spacing:1px;margin-top:2px;}}
.mcell .mval{{font-size:17px;font-weight:900;color:#fff;font-family:'SF Mono',Consolas,monospace;}}
.mcell .msub{{font-size:9.5px;color:#4f6690;font-weight:500;line-height:1.35;margin-top:1px;}}

.footer{{margin-top:20px;text-align:center;font-size:10.5px;color:#4f6690;letter-spacing:1.2px;display:flex;align-items:center;justify-content:center;gap:7px;position:relative;z-index:2;font-family:'SF Mono',Consolas,monospace;}}
.footer .fdot{{width:5px;height:5px;border-radius:50%;background:#5ad8ff;box-shadow:0 0 6px #5ad8ff;}}
</style></head>
<body><div class="card">
<span class="corner tl"></span><span class="corner tr"></span><span class="corner bl"></span><span class="corner br"></span>
<div class="top">
  <div class="kicker"><span class="dot"></span>MEETING PERSONA · {period}</div>
  <div class="kicker2">DATA: TMEET REAL-TIME</div>
</div>
<div class="title-zone"><div class="lbl">// 你的会议人格</div><div class="name">{title_html}</div></div>
<div class="radar-zone"><div class="radar">{radar}<div class="core-v"><div class="cv">{avg}</div><div class="cl">综合战力</div></div></div></div>
<div class="verdict"><p>{oneline}</p></div>
<div class="metrics">{det_html}</div>
<div class="footer"><span class="fdot"></span>调用腾讯会议 Skill 生成 · 仅用会议元数据统计</div>
</div></body></html>'''
    open(out, 'w').write(html)
    print("wrote", out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '2026 Q2')
