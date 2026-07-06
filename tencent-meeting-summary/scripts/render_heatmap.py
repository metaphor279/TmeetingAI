#!/usr/bin/env python3
"""季度会议热力图 —— HTML 渲染器。
用法: python3 render_heatmap.py <STATS_JSON(来自 heatmap_stats.py)> <OUT_HTML>
风格: 横向800px, 浅蓝→白渐变, 主色 #2B5FF6, 淡蓝边框, 无阴影(扁平), GitHub式贡献墙。
"""
import json, sys
from datetime import date

def color(cnt, future):
    if future: return 'transparent'
    S = {0:'#eef1f7',1:'#d7e2ff',2:'#b3caff',3:'#8fb0ff',4:'#6b93fb',5:'#4778f6',6:'#2B5FF6'}
    return '#1c46c9' if cnt >= 7 else S.get(cnt, '#eef1f7')

def main(stats_json, out):
    data = json.load(open(stats_json))
    r = data['result']; cols = data['cols']
    CELL=22; GAP=6; LEFT=34; TOP=26
    W = LEFT + 13*(CELL+GAP); H = TOP + 7*(CELL+GAP)
    MONTHS = ['','1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']
    DOW = ['一','二','三','四','五','六','日']
    svg = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg" font-family="inherit">']
    last = None
    for ci, c in enumerate(cols):
        mon = date.fromisoformat(c['mon']); x = LEFT+ci*(CELL+GAP)
        if mon.month != last:
            svg.append(f'<text x="{x}" y="16" font-size="11" fill="#8891a8" font-weight="600">{MONTHS[mon.month]}</text>')
            last = mon.month
    for ri in range(7):
        y = TOP+ri*(CELL+GAP)+CELL-6
        svg.append(f'<text x="2" y="{y}" font-size="10.5" fill="#a6adbf">{DOW[ri]}</text>')
    for ci, c in enumerate(cols):
        for ri, day in enumerate(c['days']):
            if day['future']: continue
            x = LEFT+ci*(CELL+GAP); y = TOP+ri*(CELL+GAP)
            fill = color(day['count'], day['future'])
            stroke = '#e3e8f4' if day['count']==0 else 'rgba(43,95,246,.08)'
            svg.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="5" ry="5" fill="{fill}" stroke="{stroke}" stroke-width="1"><title>{day["date"]} · {day["count"]}场</title></rect>')
    svg.append('</svg>')
    svg_str = '\n'.join(svg)

    bd = date.fromisoformat(r['busiest_day']); bw = date.fromisoformat(r['busiest_week_mon'])
    ss = date.fromisoformat(r['streak_start']); se = date.fromisoformat(r['streak_end'])
    roast = (f"你最长连续 {r['max_streak']} 天泡在会里（{ss.month}/{ss.day}–{se.month}/{se.day}），"
             f"但也守住了 {r['zero_days']} 天的清净日——忙而不乱，算你赢。")
    ws = date.fromisoformat(r['window_start']); we = date.fromisoformat(r['window_end'])
    period = f"{ws.year}.{ws.month:02d}.{ws.day:02d} – {we.month:02d}.{we.day:02d}"
    busy_day_str = f"{bd.month}月{bd.day}日"; busy_week_str = f"{bw.month}/{bw.day} 那一周"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>季度会议热力图</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{display:flex;justify-content:center;align-items:flex-start;padding:40px 20px;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased;}}
.card{{width:800px;border-radius:32px;overflow:hidden;position:relative;background:linear-gradient(160deg,#e3ebff 0%,#eef3ff 32%,#f7faff 66%,#ffffff 100%);border:1.5px solid rgba(43,95,246,.22);padding:34px 38px 28px;}}
.kicker{{font-size:12px;letter-spacing:3px;color:#2B5FF6;font-weight:700;margin-bottom:10px;opacity:.85;}}
.title{{font-size:27px;font-weight:900;color:#1e2748;line-height:1.4;letter-spacing:-.5px;}}
.title .hl{{position:relative;color:#2B5FF6;display:inline-block;padding:0 4px;z-index:1;}}
.title .hl::after{{content:"";position:absolute;left:-3px;right:-3px;top:2px;bottom:2px;z-index:-1;border:2.5px solid #2B5FF6;border-radius:50%/60%;transform:rotate(-2deg);}}
.subtitle{{margin-top:12px;font-size:13px;color:#5b6478;font-weight:500;}}
.subtitle b{{color:#2B5FF6;font-weight:700;}}
.heatwrap{{margin-top:24px;background:#fff;border-radius:20px;padding:22px 22px 20px;border:1px solid rgba(43,95,246,.06);}}
.heatwrap svg{{display:block;max-width:100%;height:auto;}}
.points{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px;}}
.pt{{background:#fff;border:1.5px solid rgba(43,95,246,.22);border-radius:18px;padding:16px 16px 15px;}}
.pt .plbl{{font-size:12px;color:#8891a8;font-weight:600;display:flex;align-items:center;gap:6px;}}
.pt .pv{{font-size:26px;font-weight:900;color:#2B5FF6;line-height:1.15;margin-top:8px;letter-spacing:-.5px;}}
.pt .pv small{{font-size:12px;font-weight:700;color:#9aa3ba;margin-left:3px;}}
.pt .psub{{font-size:11.5px;color:#a6adbf;margin-top:4px;}}
.roast{{margin-top:20px;background:linear-gradient(100deg,#2B5FF6,#5a7ff8);color:#fff;border-radius:16px;padding:15px 20px;font-size:14px;line-height:1.6;font-weight:500;display:flex;align-items:center;gap:12px;}}
.roast .quote{{font-size:30px;font-weight:900;opacity:.5;line-height:1;flex-shrink:0;}}
.footer{{margin-top:20px;text-align:center;font-size:11.5px;color:#9aa3ba;letter-spacing:1px;display:flex;align-items:center;justify-content:center;gap:7px;}}
.footer .fdot{{width:7px;height:7px;border-radius:50%;background:#2B5FF6;}}
</style></head>
<body><div class="card">
<div class="kicker">MEETING HEATMAP</div>
<div class="title">过去一个季度，你把日子过成了什么<span class="hl">颜色</span>？</div>
<div class="subtitle">数据周期 <b>{period}</b> · 近 13 周 · 共 <b>{r['total_meetings']}</b> 场会议 · <b>{r['active_days']}</b> 天有会</div>
<div class="heatwrap">{svg_str}</div>
<div class="points">
<div class="pt"><div class="plbl">🔥 最忙的一天</div><div class="pv">{busy_day_str}</div><div class="psub">当天 {r['busiest_day_count']} 场会议连轴转</div></div>
<div class="pt"><div class="plbl">📅 最忙的一周</div><div class="pv">{r['busiest_week_count']}<small>场</small></div><div class="psub">{busy_week_str}最密集</div></div>
<div class="pt"><div class="plbl">🌿 零会清净日</div><div class="pv">{r['zero_days']}<small>天</small></div><div class="psub">{r['total_window_days']} 天里没有会的日子</div></div>
</div>
<div class="roast"><span class="quote">“</span><span>{roast}</span></div>
<div class="footer"><span class="fdot"></span>调用腾讯会议 Skill 生成 · 数据源自真实会议记录</div>
</div></body></html>'''
    open(out, 'w').write(html)
    print("wrote", out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
