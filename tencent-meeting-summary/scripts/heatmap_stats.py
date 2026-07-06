#!/usr/bin/env python3
"""季度会议热力图 —— 数据统计。

读取 collect_meetings.sh 产出的 JSONL，按每场会议开始日期统计每日会议数，
计算最忙一天/最忙一周/零会清净日/最长连续开会天数，并输出可直接喂给渲染器的 JSON。

用法:
  python3 heatmap_stats.py <MEETINGS_JSONL> <END_DATE:YYYY-MM-DD> <OUT_JSON>

窗口固定为 13 整周(91天)，以 END_DATE 所在周的周一往前推 12 周为起点。
"""
import json, sys
from datetime import date, timedelta
from collections import defaultdict

def main(jsonl, end_str, out):
    meetings = []
    for line in open(jsonl):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        for m in d.get('data', {}).get('meeting_info_list', []):
            meetings.append(m)
    # 去重: meeting_id + sub_meeting_id
    seen = set(); uniq = []
    for m in meetings:
        k = (m['meeting_id'], m.get('sub_meeting_id', ''))
        if k in seen:
            continue
        seen.add(k); uniq.append(m)

    daycount = defaultdict(int)
    for m in uniq:
        daycount[m['start_time'][:10]] += 1

    end = date.fromisoformat(end_str)
    this_mon = end - timedelta(days=end.weekday())
    start_mon = this_mon - timedelta(weeks=12)

    cols = []
    for w in range(13):
        col_mon = start_mon + timedelta(weeks=w)
        days = []
        for dow in range(7):
            dd = col_mon + timedelta(days=dow)
            days.append({'date': dd.isoformat(), 'count': daycount.get(dd.isoformat(), 0),
                         'future': dd > end})
        cols.append({'mon': col_mon.isoformat(), 'days': days})

    window = []
    dd = start_mon
    while dd <= end:
        window.append(dd); dd += timedelta(days=1)

    dates = sorted(daycount)
    busiest_day = max(dates, key=lambda x: daycount[x]) if dates else None
    week_tot = [(c['mon'], sum(x['count'] for x in c['days'] if not x['future'])) for c in cols]
    busiest_week = max(week_tot, key=lambda x: x[1]) if week_tot else (None, 0)
    zero_days = sum(1 for wd in window if daycount.get(wd.isoformat(), 0) == 0)
    active_days = sum(1 for wd in window if daycount.get(wd.isoformat(), 0) > 0)

    maxstreak = cur = 0; best_end = None
    for wd in window:
        if daycount.get(wd.isoformat(), 0) > 0:
            cur += 1
            if cur > maxstreak:
                maxstreak = cur; best_end = wd
        else:
            cur = 0
    best_start = (best_end - timedelta(days=maxstreak - 1)) if best_end else None

    result = {
        'total_meetings': sum(daycount.values()),
        'window_start': start_mon.isoformat(), 'window_end': end.isoformat(),
        'total_window_days': len(window), 'active_days': active_days, 'zero_days': zero_days,
        'busiest_day': busiest_day, 'busiest_day_count': daycount.get(busiest_day, 0) if busiest_day else 0,
        'busiest_week_mon': busiest_week[0], 'busiest_week_count': busiest_week[1],
        'max_streak': maxstreak,
        'streak_start': best_start.isoformat() if best_start else None,
        'streak_end': best_end.isoformat() if best_end else None,
    }
    json.dump({'result': result, 'cols': cols}, open(out, 'w'), ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
