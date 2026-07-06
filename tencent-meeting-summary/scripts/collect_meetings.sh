#!/usr/bin/env bash
# 拉取近 N 天已结束会议，分页 + 去重，输出 JSONL 到指定文件。
# 用法: collect_meetings.sh <START_ISO> <END_ISO> <OUT_JSONL>
# 注意: tmeet meeting list-ended 的时间区间硬上限为 90 天(>90天报错 190004)，
#       调用方需保证 START 与 END 间隔 <= 90 天。page-size 上限为 20。
set -e
START="$1"; END="$2"; OUT="$3"
: > "$OUT"
token=""; page=1
while true; do
  if [ -z "$token" ]; then
    resp=$(tmeet meeting list-ended --start "$START" --end "$END" --page-size 20 2>&1)
  else
    resp=$(tmeet meeting list-ended --start "$START" --end "$END" --page-size 20 --page-token "$token" 2>&1)
  fi
  echo "$resp" >> "$OUT"
  token=$(echo "$resp" | python3 -c "import sys,json;print(json.load(sys.stdin)['data'].get('next_page_token',''))" 2>/dev/null || echo "")
  [ -z "$token" ] && break
  page=$((page+1)); [ $page -gt 15 ] && break
done
echo "collected pages into $OUT" >&2
