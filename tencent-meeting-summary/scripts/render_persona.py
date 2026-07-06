#!/usr/bin/env python3
"""会议人格卡 —— HTML 渲染器(竖版抽卡风)。
用法: python3 render_persona.py <STATS_JSON(来自 persona_stats.py)> <OUT_HTML> [PERIOD_LABEL]
风格: 竖版600px, 深空蓝紫渐变+网格纹, SSR评级, 发光雷达图(中心叠加综合战力), 引号评语条, 2列标签墙。
"""
import json, sys, math

ICON = {'组织规划':'◈','稳定协作':'⬡','主动引导':'▲','共情倾听':'❤','探索创新':'✦','高效执行':'⚡'}

def main(stats_json, out, period='2026 Q2'):
    d = json.load(open(stats_json))
    scores = d['scores']; order = d['order']; avg = d['avg']
    title = d['title']; oneline = d['oneline']; tags = d['tags']

    cx=cy=None; R=120; cx,cy=185,180; n=6
    def pt(i, r):
        ang = -math.pi/2 + i*2*math.pi/n
        return (cx+r*math.cos(ang), cy+r*math.sin(ang))
    grid=''
    for g in [0.25,0.5,0.75,1.0]:
        poly=' '.join(f"{pt(i,R*g)[0]:.1f},{pt(i,R*g)[1]:.1f}" for i in range(n))
        grid+=f'<polygon points="{poly}" fill="none" stroke="rgba(120,160,255,{0.32 if g==1 else 0.14})" stroke-width="{1.3 if g==1 else 0.8}"/>'
    axes=''
    for i in range(n):
        x,y=pt(i,R); axes+=f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="rgba(120,160,255,.14)" stroke-width="0.8"/>'
    dpts=' '.join(f"{pt(i,R*scores[order[i]]/100)[0]:.1f},{pt(i,R*scores[order[i]]/100)[1]:.1f}" for i in range(n))
    dots=''; labels=''
    for i in range(n):
        x,y=pt(i,R*scores[order[i]]/100)
        dots+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#fff" stroke="#3d7bff" stroke-width="2.5"/>'
        lx,ly=pt(i,R+27); anchor='middle'
        if lx>cx+12: anchor='start'
        elif lx<cx-12: anchor='end'
        dy = -4 if ly<cy-5 else (11 if ly>cy+5 else 0)
        labels+=f'<text x="{lx:.1f}" y="{ly+dy:.1f}" text-anchor="{anchor}" font-size="12.5" font-weight="800" fill="#dbe6ff">{order[i]}</text>'
        labels+=f'<text x="{lx:.1f}" y="{ly+dy+16:.1f}" text-anchor="{anchor}" font-size="13" font-weight="900" fill="#6fa0ff">{scores[order[i]]}</text>'
    radar=(f'<svg viewBox="0 0 370 370" width="330" height="330" xmlns="http://www.w3.org/2000/svg">'
           f'<defs><radialGradient id="rfill" cx="50%" cy="50%" r="60%">'
           f'<stop offset="0%" stop-color="rgba(90,140,255,.55)"/><stop offset="100%" stop-color="rgba(120,80,255,.28)"/></radialGradient>'
           f'<filter id="glow"><feGaussianBlur stdDeviation="3.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>'
           f'{grid}{axes}<polygon points="{dpts}" fill="url(#rfill)" stroke="#5a8cff" stroke-width="2.5" filter="url(#glow)"/>{dots}{labels}</svg>')

    tag_html=''
    for t in tags:
        cls='ssr' if t['rarity']=='SSR' else 'sr'
        tag_html+=(f'<div class="tag {cls}"><span class="tico">{ICON[t["dim"]]}</span>'
                   f'<span class="tbody"><span class="tname">{t["name"]}</span>'
                   f'<span class="tdim">{t["dim"]} · {t["score"]}</span></span>'
                   f'<span class="trar">{t["rarity"]}</span></div>')

    html=f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>会议人格卡</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{display:flex;justify-content:center;align-items:flex-start;padding:40px 20px;background:#eef2fb;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased;}}
.card{{width:600px;border-radius:32px;position:relative;overflow:hidden;padding:30px 34px 26px;color:#eaf0ff;background:radial-gradient(900px 380px at 15% -10%,rgba(90,120,255,.5),transparent 60%),radial-gradient(760px 420px at 110% 15%,rgba(140,80,255,.46),transparent 55%),radial-gradient(600px 460px at 55% 118%,rgba(40,90,230,.46),transparent 60%),linear-gradient(160deg,#0b1230 0%,#111a44 45%,#0d1130 100%);background-color:#0b1230;border:1.5px solid rgba(120,160,255,.35);box-shadow:0 40px 90px -30px rgba(30,50,160,.65),inset 0 1px 0 rgba(255,255,255,.08);}}
.card::before{{content:"";position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(rgba(120,160,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(120,160,255,.05) 1px,transparent 1px);background-size:32px 32px;mask:radial-gradient(circle at 50% 22%,#000,transparent 76%);}}
.top{{display:flex;justify-content:space-between;align-items:center;position:relative;z-index:2;}}
.kicker{{font-size:11.5px;letter-spacing:3.5px;color:#9fc0ff;font-weight:700;}}
.rarity{{display:flex;align-items:center;gap:8px;}}
.rarity .ssrbig{{font-size:26px;font-weight:900;letter-spacing:1px;line-height:1;background:linear-gradient(92deg,#ffd76a,#ff8a3c 55%,#ff5f9e);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 2px 8px rgba(255,160,60,.5));}}
.rarity .stars{{color:#ffd166;font-size:12px;letter-spacing:2px;}}
.title-zone{{text-align:center;margin-top:20px;position:relative;z-index:2;}}
.title-zone .lbl{{font-size:11.5px;letter-spacing:3px;color:#8fb0ff;font-weight:600;}}
.title-zone .name{{font-size:32px;font-weight:900;letter-spacing:-.5px;line-height:1.28;margin-top:9px;background:linear-gradient(96deg,#ffffff,#bcd3ff 55%,#8ea0ff);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 3px 14px rgba(120,150,255,.5));}}
.radar-zone{{position:relative;z-index:2;display:flex;flex-direction:column;align-items:center;margin-top:6px;}}
.radar{{position:relative;}}
.radar .core{{position:absolute;top:calc(50% - 6px);left:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;}}
.radar .core .cv{{font-size:30px;font-weight:900;color:#fff;line-height:1;filter:drop-shadow(0 2px 8px rgba(90,140,255,.8));}}
.radar .core .cl{{font-size:10px;letter-spacing:2px;color:#9fc0ff;font-weight:700;margin-top:3px;}}
.verdict{{position:relative;z-index:2;margin-top:6px;background:rgba(120,160,255,.1);border:1px solid rgba(120,160,255,.26);border-radius:16px;padding:15px 20px;display:flex;gap:13px;align-items:flex-start;}}
.verdict .q{{font-size:30px;font-weight:900;line-height:.9;color:#5a8cff;flex-shrink:0;}}
.verdict p{{font-size:13.5px;line-height:1.75;color:#c3d2ff;font-weight:400;}}
.tagwrap{{margin-top:20px;position:relative;z-index:2;}}
.tagwrap .th{{font-size:12.5px;font-weight:800;color:#c3d2ff;margin-bottom:12px;display:flex;align-items:center;gap:9px;letter-spacing:.5px;}}
.tagwrap .th .cnt{{font-size:10.5px;font-weight:800;color:#0b1230;background:linear-gradient(92deg,#ffd76a,#ff9a4c);border-radius:99px;padding:3px 10px;}}
.tagwrap .th .line{{flex:1;height:1px;background:linear-gradient(90deg,rgba(120,160,255,.4),transparent);}}
.tags{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;}}
.tag{{display:flex;align-items:center;gap:11px;border-radius:14px;padding:11px 14px;position:relative;overflow:hidden;background:rgba(120,160,255,.09);border:1px solid rgba(120,160,255,.26);}}
.tag.ssr{{border-color:rgba(255,190,90,.5);background:linear-gradient(120deg,rgba(255,180,80,.15),rgba(120,160,255,.08));}}
.tag .tico{{font-size:19px;color:#7fa5ff;flex-shrink:0;}}
.tag.ssr .tico{{color:#ffce6a;}}
.tag .tbody{{display:flex;flex-direction:column;gap:2px;min-width:0;flex:1;}}
.tag .tname{{font-size:13.5px;font-weight:800;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.tag .tdim{{font-size:10px;color:#8fa3d6;font-weight:600;}}
.tag .trar{{font-size:10px;font-weight:900;letter-spacing:.5px;color:#7fa5ff;flex-shrink:0;}}
.tag.ssr .trar{{color:#ffce6a;}}
.footer{{margin-top:22px;text-align:center;font-size:11px;color:#7f93c8;letter-spacing:1px;display:flex;align-items:center;justify-content:center;gap:7px;position:relative;z-index:2;}}
.footer .fdot{{width:6px;height:6px;border-radius:50%;background:#5a8cff;box-shadow:0 0 8px #5a8cff;}}
</style></head>
<body><div class="card">
<div class="top"><div class="kicker">MEETING PERSONA · {period}</div><div class="rarity"><span class="ssrbig">SSR</span><span class="stars">★★★★★</span></div></div>
<div class="title-zone"><div class="lbl">你 的 会 议 人 格 称 号</div><div class="name">{title}</div></div>
<div class="radar-zone"><div class="radar">{radar}<div class="core"><div class="cv">{avg}</div><div class="cl">综合战力</div></div></div></div>
<div class="verdict"><span class="q">“</span><p>{oneline}</p></div>
<div class="tagwrap"><div class="th">已解锁性格标签 <span class="cnt">{len(tags)} 枚</span><span class="line"></span></div><div class="tags">{tag_html}</div></div>
<div class="footer"><span class="fdot"></span>调用腾讯会议 Skill 生成 · 数据源自近 90 天真实统计</div>
</div></body></html>'''
    open(out, 'w').write(html)
    print("wrote", out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else '2026 Q2')
