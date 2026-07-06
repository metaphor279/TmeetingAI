#!/usr/bin/env python3
"""会议人格·轻量版 —— 仅用会议元数据(零录制内容读取)统计并渲染。

数据来源:
  1) collect_meetings.sh -> meetings.jsonl (meeting list-ended)
  2) 逐会议 tmeet meeting get --meeting-id <id> -> mget.jsonl
     每行: {"mid":"<id>","resp":<meeting get 原始返回或Error文本>}
     (用于判定"主动发起"占比；失败行容错跳过)
  3) 逐会议 tmeet record list --meeting-id <id> -> records.jsonl
     每行: {"mid":"<id>","resp":<record list 原始返回>}
     (仅判定该会议是否"有录制"，不读取任何录制内容，轻量不超时)

六维(全部来自元数据，无需读取录制内容):
  参与=总场次 / 投入=总时长(h) / 敏捷=平均时长(min，越短越敏捷)
  规划=预约会占比 / 主动=本人主持占比 / 沉淀=有录制会议占比

用法:
  python3 persona_light_stats.py <ME_OPEN_ID> <MEETINGS_JSONL> <MGET_JSONL> <RECORDS_JSONL> <OUT_JSON>
  ME_OPEN_ID: 当前登录账号 open_id(形如 cli_xxx)，来自 tmeet auth status；传 "-" 则"主动"按0计。
  RECORDS_JSONL: 传 "-" 则跳过，"沉淀"按0计。
"""
import json, sys
from datetime import datetime

DIM = [
 ('总场次','参与','◈','{v} 场','一个季度的参会总量'),
 ('总时长','投入','⬢','{v} 小时','累计投入的会议时间'),
 ('平均时长','敏捷','▲','{v} 分钟','单场越短越敏捷'),
 ('预约占比','规划','◆','{v}%','提前预约 vs 临时发起'),
 ('创建占比','主动','★','{v}%','主动发起会议的比例'),
 ('录制占比','沉淀','⬡','{v}%','有录制会议的留存占比'),
]
ANCHORS = {
 '总场次':[(0,0),(20,35),(50,55),(90,72),(130,85),(200,100)],
 '总时长':[(0,0),(20,35),(50,55),(100,75),(150,88),(250,100)],
 # 敏捷: 会开得越短越高分(反转)
 '平均时长':[(15,100),(30,90),(45,78),(60,60),(75,45),(90,30),(120,10)],
 '预约占比':[(0,0),(20,30),(40,50),(60,68),(75,82),(90,95),(100,100)],
 '创建占比':[(0,0),(10,35),(20,55),(35,72),(50,85),(70,100)],
 # 沉淀: 有录制会议占比，普通用户偏低；重度留存者可达60%+
 '录制占比':[(0,0),(5,25),(15,45),(30,65),(50,80),(70,90),(100,100)],
}
# 核心身份(最高维，口语梗身份名，追求传播性；全部正向/中性)
CORE = {'总场次':'会议钉子户','总时长':'会议收割机','平均时长':'会议速通选手',
        '预约占比':'会议操盘手','创建占比':'会议节奏大师','录制占比':'会议收藏家'}
LOW = {'总场次':'多参与一些讨论，存在感会更强','总时长':'时间安排张弛有度，挺好',
       '平均时长':'会议节奏可以再明快一点','预约占比':'多提前预约，节奏会更从容',
       '创建占比':'不妨多主动发起几场，带带节奏','录制占比':'重要的会开个录制，方便日后回看'}

def interp(x, a):
    if x <= a[0][0]: return a[0][1]
    for (x0,y0),(x1,y1) in zip(a, a[1:]):
        if x <= x1: return round(y0+(x-x0)/(x1-x0)*(y1-y0))
    return a[-1][1]

def segment(s):
    """单维段位。"""
    return '宗师' if s>=85 else ('高手' if s>=65 else ('进阶' if s>=40 else '萌新'))

def title_prefix(sc, srt):
    """口语状态前缀(呼应"越聊越上头的")。按形态优先级取第一个命中，全部正向。
    返回 (form_key, prefix, special)。special 非空则作为整句独立称号。"""
    vals=list(sc.values()); mx=max(vals); mn=min(vals); avg=sum(vals)/6
    (d1,s1),(d2,s2)=srt[0],srt[1]
    if mn>=80:
        return ('全能型', None, '会议King')
    if mx-mn<=15:
        return ('均衡型', 'Everything都拿手的', None)
    if s1>=85 and (s1-s2)>=12:
        return ('专精型', 'Very专业的', None)
    if s1>=75 and s2>=75:
        return ('双核型', '越开越起劲的', None)
    if avg>=68:
        return ('资深型', '游刃有余的', None)
    return ('成长型', '越来越有节奏的', None)

def main(me_oid, meetings_jsonl, mget_jsonl, records_jsonl, out):
    seen=set(); rows=[]
    for line in open(meetings_jsonl):
        line=line.strip()
        if not line: continue
        for m in json.loads(line)['data'].get('meeting_info_list', []):
            k=(m['meeting_id'], m.get('sub_meeting_id',''))
            if k in seen: continue
            seen.add(k); rows.append(m)

    n=len(rows); total_min=0; scheduled=0
    mids_all=set()
    for m in rows:
        mids_all.add(m['meeting_id'])
        st=datetime.fromisoformat(m['start_time']); et=datetime.fromisoformat(m['end_time'])
        d=min(max((et-st).total_seconds()/60,0),600); total_min+=d
        if '快速会议' not in m.get('subject',''): scheduled+=1

    # 主动发起占比: 容错解析 mget(错误响应行不是合法JSON,用字符串定位)
    uniq=set(); host_mine=set()
    if me_oid and me_oid != '-':
        for line in open(mget_jsonl):
            line=line.strip()
            if not line: continue
            try:
                mid=line.split('"mid":"',1)[1].split('"',1)[0]
            except Exception:
                continue
            uniq.add(mid)
            if '"current_hosts"' in line:
                seg=line.split('"current_hosts"',1)[1].split(']',1)[0]
                if me_oid in seg: host_mine.add(mid)
    create_pct = (len(host_mine)/len(uniq)*100) if uniq else 0

    # 沉淀=有录制会议占比: 用 record list 判定该会议是否有录制文件(不读内容)
    recorded=set()
    if records_jsonl and records_jsonl != '-':
        for line in open(records_jsonl):
            line=line.strip()
            if not line: continue
            try:
                d=json.loads(line)
            except Exception:
                continue
            mid=d.get('mid')
            data=(d.get('resp') or {}).get('data') or {}
            if data.get('total_count', 0) and data.get('record_meetings'):
                recorded.add(mid)
    rec_pct = (len(recorded)/len(mids_all)*100) if mids_all else 0

    raw={'总场次':n,'总时长':round(total_min/60,1),'平均时长':round(total_min/n,1) if n else 0,
         '预约占比':round(scheduled/n*100,1) if n else 0,'创建占比':round(create_pct,1),
         '录制占比':round(rec_pct,1)}
    sc={k:interp(raw[k],ANCHORS[k]) for k in raw}
    order=[x[0] for x in DIM]; disp={x[0]:x[1] for x in DIM}
    avg=round(sum(sc.values())/6,1)
    srt=sorted(sc.items(), key=lambda x:-x[1]); top1,top2,low1=srt[0][0],srt[1][0],srt[-1][0]

    # 称号 = 口语前缀 + 最高维身份；全能型用独立称号
    form_key, prefix, special = title_prefix(sc, srt)
    if special:
        title = special; title_prefix_text = ''; title_core_text = special
    else:
        title = f"{prefix}{CORE[top1]}"; title_prefix_text = prefix; title_core_text = CORE[top1]
    oneline=(f"你在「{disp[top1]}」「{disp[top2]}」上表现突出，一个季度 {raw['总时长']} 小时投入在 {raw['总场次']} 场会议里；"
             f"要说还能再进一步的，「{disp[low1]}」值得点一下——{LOW[low1]}。")
    detail=[{'name':x[1],'ico':x[2],'val':x[3].format(v=raw[x[0]]),'sub':x[4],'score':sc[x[0]],'seg':segment(sc[x[0]])} for x in DIM]

    out_obj={'scores':sc,'order':order,'disp':disp,'avg':avg,'title':title,'form':form_key,'oneline':oneline,
             'title_prefix':title_prefix_text,'title_core':title_core_text,
             'detail':detail,'raw':raw,
             'meta':{'hosted':len(host_mine),'detail_ok':len(uniq),'recorded':len(recorded),'total_uniq':len(mids_all)}}
    json.dump(out_obj, open(out,'w'), ensure_ascii=False, indent=2)
    print(json.dumps({'title':title,'form':form_key,'oneline':oneline,'scores':sc}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
