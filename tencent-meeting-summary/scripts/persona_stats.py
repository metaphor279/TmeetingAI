#!/usr/bin/env python3
"""会议人格 —— 六维评分统计。

流程(调用方负责先完成):
  1) collect_meetings.sh 拉取近90天会议 -> meetings.jsonl
  2) 对每个 unique meeting_id 执行: tmeet record list --meeting-id <id>  -> 收集到 records.jsonl
     每行格式: {"mid":"<meeting_id>","resp":<record list 原始返回>}
  3) 对每个 record_file 执行: tmeet record transcript-get --record-file-id <rfid> --meeting-id <mid> --limit 3000
     产物落盘到 <TRANSCRIPT_DIR>/<rfid>.json

本脚本读取上述产物，计算六维原始值与 0-100 评分、性格标签、人格称号、一句话评价。

用法:
  python3 persona_stats.py <ME_USER_ID> <MEETINGS_JSONL> <RECORDS_JSONL> <TRANSCRIPT_DIR> <OUT_JSON>
"""
import json, sys, os, glob, re, math
from collections import Counter

ORDER = ['组织规划', '稳定协作', '主动引导', '共情倾听', '探索创新', '高效执行']

ANCHORS = {
 '组织规划': [(0,5),(2,30),(5,50),(10,68),(20,80),(40,92),(60,100)],
 '稳定协作': [(0,0),(5,30),(15,50),(30,65),(60,80),(100,92),(150,100)],
 '主动引导': [(0,0),(5,25),(10,45),(15,55),(20,65),(30,80),(45,92),(60,100)],
 '共情倾听': [(0,0),(200,30),(400,50),(600,65),(800,78),(1000,88),(1300,100)],
 '探索创新': [(0,0),(50,25),(100,42),(200,60),(300,75),(400,88),(550,100)],
 '高效执行': [(0,0),(30,25),(60,42),(100,58),(150,72),(250,88),(400,100)],
}
TAG_POOL = {
 '组织规划': {'高手':'局面铺排师','宗师':'会议架构师'},
 '稳定协作': {'高手':'全勤参会人','宗师':'团队定盘星'},
 '主动引导': {'高手':'节奏推进者','宗师':'掌控全场的麦霸'},
 '共情倾听': {'高手':'走心接话王','宗师':'万物皆可"对对对"'},
 '探索创新': {'高手':'灵感发射器','宗师':'停不下来的点子王'},
 '高效执行': {'高手':'干脆利落派','宗师':'秒接需求的行动力'},
}
CORE = {'组织规划':'幕后操盘手','稳定协作':'团队压舱石','主动引导':'全场指挥官',
        '共情倾听':'群聊粘合剂','探索创新':'点子王','高效执行':'需求收割机'}
SUBTYPE = {'共情':'接话型','探索':'发散型','执行':'秒办型'}
ADVICE = {'组织规划':'可以试着多攒几个局','稳定协作':'别缺席那些关键会',
          '主动引导':'你搭好了台，不妨多抢两次麦','共情倾听':'多接一句话会更暖',
          '探索创新':'大胆抛点不成熟的想法','高效执行':'把"好的"落成"已完成"'}

def interp(x, anchors):
    if x <= anchors[0][0]:
        return anchors[0][1]
    for (x0,y0),(x1,y1) in zip(anchors, anchors[1:]):
        if x <= x1:
            return round(y0 + (x-x0)/(x1-x0)*(y1-y0))
    return anchors[-1][1]

def par_text(p):
    return ''.join(w.get('text','') for s in p.get('sentences',[]) for w in s.get('words',[]))

def main(me, meetings_jsonl, records_jsonl, tdir, out):
    # 参会总数(去重)
    mids_all = set()
    for line in open(meetings_jsonl):
        line = line.strip()
        if not line: continue
        for m in json.loads(line)['data'].get('meeting_info_list', []):
            mids_all.add((m['meeting_id'], m.get('sub_meeting_id','')))
    attended_total = len(mids_all)

    # 创会数: record list 里 host_user_id == me 的会议(去重)
    hosted = set(); rf2mid = {}
    for line in open(records_jsonl):
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except Exception: continue
        mid = d['mid']
        for rm in d['resp'].get('data', {}).get('record_meetings', []):
            if rm.get('host_user_id') == me:
                hosted.add(mid)
            for rf in rm.get('record_files', []):
                rf2mid[rf['record_file_id']] = mid
    created = len(hosted)

    # 同一会议多份录制取段落最多的一份
    mid_best = {}
    for fp in glob.glob(os.path.join(tdir, '*.json')):
        rfid = os.path.basename(fp).replace('.json','')
        mid = rf2mid.get(rfid)
        if mid is None: continue
        try: d = json.load(open(fp))
        except Exception: continue
        minutes = (d.get('data') or {}).get('minutes')
        if not minutes: continue
        pars = minutes.get('paragraphs', [])
        if not pars: continue
        cur = mid_best.get(mid)
        if cur is None or len(pars) > cur[0]:
            mid_best[mid] = (len(pars), pars)

    EXP = ['我觉得','我想','试试']; EXE = ['马上','好的','没问题']
    my_seg = all_seg = emp = exp = exe = 0
    for mid,(n,pars) in mid_best.items():
        for p in pars:
            uid = (p.get('speaker') or {}).get('user_id','')
            all_seg += 1
            if uid != me: continue
            my_seg += 1
            txt = par_text(p)
            for k in EXP: exp += txt.count(k)
            for k in EXE: exe += txt.count(k)
            emp += txt.count('对') + txt.count('嗯')
            if len(re.sub(r'\s','',txt)) <= 6:
                emp += txt.count('是')

    share = round(my_seg/all_seg*100, 1) if all_seg else 0
    dens = lambda c: (c/my_seg*1000) if my_seg else 0
    raw = {'组织规划':created, '稳定协作':attended_total, '主动引导':share,
           '共情倾听':dens(emp), '探索创新':dens(exp), '高效执行':dens(exe)}
    scores = {k: interp(v, ANCHORS[k]) for k, v in raw.items()}

    tags = []
    for d in ORDER:
        s = scores[d]
        if s >= 85: tags.append({'name':TAG_POOL[d]['宗师'],'dim':d,'score':s,'rarity':'SSR'})
        elif s >= 65: tags.append({'name':TAG_POOL[d]['高手'],'dim':d,'score':s,'rarity':'SR'})

    srt = sorted(scores.items(), key=lambda x: -x[1])
    top1, top2, low1 = srt[0][0], srt[1][0], srt[-1][0]
    tot = emp + exp + exe
    lang = {'共情':emp, '探索':exp, '执行':exe}
    main_lang = max(lang, key=lang.get) if tot else '共情'
    exp_share = exp/tot if tot else 0
    subtype = '追问型' if (exp_share >= 0.40 and scores['主动引导'] >= 65) else SUBTYPE[main_lang]
    rng = max(scores.values()) - min(scores.values())
    if rng < 20: prefix = '六边形战士级'
    elif main_lang == '探索': prefix = '越聊越上头的'
    elif main_lang == '共情': prefix = '越聊越暖的'
    elif main_lang == '执行': prefix = '说干就干的'
    else: prefix = '稳扎稳打的'
    core = CORE[srt[0][0]]
    title = f"{prefix}{subtype}{core}"
    oneline = (f"你是团队里的{core}，尤其在「{top1}」「{top2}」上很在线；"
               f"但「{low1}」是你的留白区，{ADVICE[low1]}。")

    result = {
        'raw': raw, 'scores': scores, 'order': ORDER,
        'avg': round(sum(scores.values())/6, 1),
        'tags': tags, 'title': title, 'oneline': oneline,
        'meta': {'my_segments':my_seg, 'all_segments':all_seg, 'transcripts_used':len(mid_best),
                 'empathy':emp, 'explore':exp, 'execute':exe}
    }
    json.dump(result, open(out, 'w'), ensure_ascii=False, indent=2)
    print(json.dumps({'scores':scores, 'title':title, 'oneline':oneline,
                      'tags':[t['name'] for t in tags]}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main(*sys.argv[1:6])
