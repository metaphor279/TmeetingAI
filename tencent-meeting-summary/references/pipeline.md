# 数据流水线与命令参考

两种总结共用「授权 → 采集 → 统计 → 渲染」四段式。所有 tmeet 命令输出为 `{trace_id, message, data}`。
临时产物一律写入系统临时目录（如 `/tmp/tmsummary/`），最终 HTML 写入当前工作目录。

## 通用前置：日期窗口

`tmeet meeting list-ended` 的时间区间**硬上限 90 天**（超出报 `error_code 190004`），`--page-size` 上限 20。
用 shell 动态取今天，起点设为今天前 89 天，避免踩上限：

```bash
END=$(date +%Y-%m-%dT23:59:59+08:00)
START=$(date -v-89d +%Y-%m-%dT00:00:00+08:00)   # macOS
# Linux: START=$(date -d '89 days ago' +%Y-%m-%dT00:00:00+08:00)
END_DATE=$(date +%Y-%m-%d)
```

---

## A. 季度热力图（轻量，只需会议列表）

```bash
DIR=/tmp/tmsummary; mkdir -p "$DIR"
bash scripts/collect_meetings.sh "$START" "$END" "$DIR/meetings.jsonl"
python3 scripts/heatmap_stats.py "$DIR/meetings.jsonl" "$END_DATE" "$DIR/heatmap.json"
python3 scripts/render_heatmap.py "$DIR/heatmap.json" "./季度会议热力图.html"
```

统计口径：按每场会议 `start_time` 前 10 位归日；窗口固定 13 整周（END 所在周的周一往前推 12 周）。
产出指标：总场次、有会天数、最忙一天/一周、零会清净日、最长连续开会天数。

---

## B. 会议人格 · 轻量版（默认，零录制内容读取）

**优先用这个。** 只需会议列表 + 逐会议 `meeting get`（判主持人）+ 逐会议 `record list`（判有无录制）。**不读取任何录制/转写内容**，秒出、永不超时、覆盖全部会议。

六维（全部来自元数据）：参与=总场次 / 投入=总时长(h) / 敏捷=平均时长(min，越短越高分) / 规划=预约会占比 / 主动=本人主持占比 / 沉淀=有录制会议占比。

```bash
DIR=/tmp/tmsummary; mkdir -p "$DIR"
ME_OID="<本人 open_id，来自 tmeet auth status 的 OpenId，形如 cli_xxx>"

# 1) 会议列表
bash scripts/collect_meetings.sh "$START" "$END" "$DIR/meetings.jsonl"

# 提取 unique meeting_id
python3 -c "
import json
mids=set()
for line in open('$DIR/meetings.jsonl'):
    line=line.strip()
    if not line: continue
    for m in json.loads(line)['data'].get('meeting_info_list',[]):
        mids.add(m['meeting_id'])
open('$DIR/mids.txt','w').write('\n'.join(sorted(mids)))
"

# 2) 逐会议 meeting get -> mget.jsonl（判主持人；部分会议返回错误(无权限/已回收)属正常，脚本容错跳过）
: > "$DIR/mget.jsonl"
while read mid; do
  resp=$(tmeet meeting get --meeting-id "$mid" 2>&1)
  echo "{\"mid\":\"$mid\",\"resp\":$resp}" >> "$DIR/mget.jsonl"
done < "$DIR/mids.txt"

# 3) 逐会议 record list -> records.jsonl（只判该会议有无录制文件，不读内容）
: > "$DIR/records.jsonl"
while read mid; do
  resp=$(tmeet record list --meeting-id "$mid" --page-size 20 2>&1)
  echo "{\"mid\":\"$mid\",\"resp\":$resp}" >> "$DIR/records.jsonl"
done < "$DIR/mids.txt"

# 4) 统计 + 渲染
python3 scripts/persona_light_stats.py "$ME_OID" "$DIR/meetings.jsonl" "$DIR/mget.jsonl" "$DIR/records.jsonl" "$DIR/persona_light.json"
python3 scripts/render_persona_light.py "$DIR/persona_light.json" "./会议人格卡-轻量版.html" "2026 Q2"
```

评分：锚点分段线性插值 0-100（校准点见 persona_light_stats.py 的 ANCHORS；敏捷维为反向——会越短分越高；沉淀维按有录制会议占比，普通用户偏低）。
称号：口语前缀（均衡/专精/双核/资深/成长五档 + 全能型独立称号）+ 最高维身份名（如"会议钉子户""会议收割机""会议收藏家"），拼接为整句。
一句话：最强两维 + 最低一维 + 正向建议，模板生成，无负面措辞。
呈现：简洁人格卡（称号 + 雷达图 + 一句话 + 六维数据格），不含标签墙/评级角标。
完整规则见 [persona_logic.md](persona_logic.md)。

> 若拿不到 open_id，可传 `ME_OID="-"`（"主动"按0计）；若不想跑 record list，第4步 records 参数传 `"-"`（"沉淀"按0计），其余维度照常。

---

## C. 会议人格 · 深度版（可选，需录制转写）

**仅当用户明确要"基于发言内容"的画像时使用。** 依赖转写，会议/内容量大时易超时，且只能覆盖有录制的会议。
六维：组织规划/稳定协作/主动引导/共情倾听/探索创新/高效执行。需要「本人 user_id」（可从任一转写的 `speaker.user_id` 确认）。

```bash
DIR=/tmp/tmsummary; mkdir -p "$DIR/transcripts"
ME="<本人 user_id，如 rakanpeng>"

# 1) 会议列表
bash scripts/collect_meetings.sh "$START" "$END" "$DIR/meetings.jsonl"

# 2) 逐会议查录制 -> records.jsonl（每行 {"mid":..,"resp":<record list 原始返回>}）
python3 -c "
import json
mids=set()
for line in open('$DIR/meetings.jsonl'):
    line=line.strip()
    if not line: continue
    for m in json.loads(line)['data'].get('meeting_info_list',[]):
        mids.add(m['meeting_id'])
open('$DIR/mids.txt','w').write('\n'.join(sorted(mids)))
"
: > "$DIR/records.jsonl"
while read mid; do
  resp=$(tmeet record list --meeting-id "$mid" --page-size 20 2>&1)
  echo "{\"mid\":\"$mid\",\"resp\":$resp}" >> "$DIR/records.jsonl"
done < "$DIR/mids.txt"

# 3) 逐录制文件拉转写 -> transcripts/<rfid>.json
python3 -c "
import json
for line in open('$DIR/records.jsonl'):
    line=line.strip()
    if not line: continue
    try: d=json.loads(line)
    except: continue
    mid=d['mid']
    for rm in d['resp'].get('data',{}).get('record_meetings',[]):
        for rf in rm.get('record_files',[]):
            print(mid, rf['record_file_id'])
" > "$DIR/tlist.txt"
while read mid rfid; do
  out="$DIR/transcripts/$rfid.json"
  [ -f "$out" ] && continue
  tmeet record transcript-get --record-file-id "$rfid" --meeting-id "$mid" --limit 3000 > "$out" 2>&1
done < "$DIR/tlist.txt"

# 4) 统计 + 渲染
python3 scripts/persona_stats.py "$ME" "$DIR/meetings.jsonl" "$DIR/records.jsonl" "$DIR/transcripts" "$DIR/persona.json"
python3 scripts/render_persona.py "$DIR/persona.json" "./会议人格卡.html" "2026 Q2"
```

### 六维口径与评分（已封装在 persona_stats.py，此处备查）

| 维度 | 原始口径 | 说明 |
|---|---|---|
| 组织规划 | 本人 host 的会议数（unique meeting_id） | `record list` 里 `host_user_id==ME`，仅有录制会议可判定，偏保守 |
| 稳定协作 | 参会会议数 | `meeting list-ended` 去重（meeting_id+sub_meeting_id）总数 |
| 主动引导 | 本人发言段 / 全场发言段 % | 仅统计有转写的会议 |
| 共情倾听 | 「对」「嗯」+短句(≤6字)里「是」 | 按密度（次/千段）评分 |
| 探索创新 | 「我觉得」「我想」「试试」 | 按密度评分 |
| 高效执行 | 「马上」「好的」「没问题」 | 按密度评分 |

- 评分用锚点分段线性插值映射到 0-100；语言三维先换算成密度消除"话多虚高"。
- 性格标签：单维 ≥65 解锁「高手」标签、≥85 解锁「宗师」标签，可多枚。
- 人格称号 = 气质前缀 + 亚型 + 核心身份：核心身份=最高维；亚型=语言主色（共情/探索/执行占比最高者，探索≥40%且主动引导≥65 时为"追问型"）；前缀由整体形态（极差<20 为六边形战士级，否则按语言主色）。
- 一句话 = 最强两维 + 最弱一维 + 对应建议，模板化生成。

> 注：SSR/五星评级为卡面装饰固定展示，稀有度真实分档体现在每枚标签的 SSR/SR 上。
