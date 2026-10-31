#!/usr/bin/env python3
"""새 기록을 넣으면 사이트의 숫자 칸과 능력별 문단 후보를 다시 만드는 장치.

입력 (inputs/)
  ritual.json        리추얼 기록 (대시보드에서 내려받은 파일 그대로)
  attendance.json    내 출석 기록에서 옮겨 적은 숫자
  assignments.csv    내 제출 현황에서 옮겨 적은 과제 목록
  defense.json       (선택) 메모리얼 파크의 방어전 단계 수
내용 (content/)
  profile.json       이름·한 줄 소개·연락처·대표작 (직접 씀)
  story.json         이야기 본편 (직접 씀)
  approved.json      후보 가운데 사이트에 넣기로 승인한 후보 id 목록
출력 (output/)
  numbers.json       숫자 칸 (출처 포함)
  candidates.md      능력별 문단 후보 (날짜·근거·id) — 여기서 골라 approved.json에 id를 적음
  data.js            사이트가 읽는 데이터 (승인된 문장만 들어감)
  manifest.txt       출력 파일의 SHA-256 (두 번 돌려 비교할 때 사용)

같은 입력이면 같은 결과가 나오도록 AI 호출·현재 시각·난수를 쓰지 않습니다.
표준 라이브러리만 씁니다 (Python 3.8 이상).
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

# 능력별 단서 낱말. 단서가 많이 나온 문장이 앞에 옵니다.
ABILITIES = {
    "자기조절력": ["비교", "아끼", "존중", "휴식", "쉬", "부담", "압박", "즐기", "멘탈", "마음 편", "후회", "나 자신", "내 길", "집중"],
    "대인관계력": ["동료", "다가가", "먼저", "칭찬", "들어", "경청", "공감", "배려", "응원", "도와", "도움", "함께", "감사", "말을 건"],
    "자기동기력": ["포기", "도전", "질문", "물어", "배우", "배움", "끝까지", "시도", "연습", "자격증", "익혔", "공부", "노력"],
}
# 후보로 볼 칸 (본인이 쓴 칸만. 동료가 쓴 칸은 넣지 않음)
FIELDS = ["강점이 드러난 일화", "강점을 위해 노력하고 생각한 것", "나에게 남기는 말", "오늘 지킬 강점·가치", "그 결과·알게 된 점"]
# 공개 사이트에 올리지 않을 낱말 (건강·사적인 내용)
EXCLUDE = ["두통", "약에", "약을", "잠이", "아파", "아픈", "병원", "컨디션", "몸 상태", "돈 걱정"]
TOP_N = 5


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_inputs(inp: Path):
    ritual = json.loads((inp / "ritual.json").read_text(encoding="utf-8"))
    att = json.loads((inp / "attendance.json").read_text(encoding="utf-8"))
    with (inp / "assignments.csv").open(encoding="utf-8", newline="") as f:
        tasks = list(csv.DictReader(f))
    dpath = inp / "defense.json"
    defense = json.loads(dpath.read_text(encoding="utf-8")) if dpath.exists() else None
    return ritual, att, tasks, defense


def split_line(s: str):
    key, _, val = s.partition(":")
    return key.strip(), val.strip()


def count_numbers(ritual, att, tasks, story, defense=None):
    days = sorted(ritual["days"], key=lambda d: d["date"])
    dates = [dt.date.fromisoformat(d["date"]) for d in days]
    start = dt.date.fromisoformat(att["course_start"])
    weeks_with = sorted({(x - start).days // 7 + 1 for x in dates})
    elapsed_weeks = (dt.date.fromisoformat(att["as_of"]) - start).days // 7 + 1
    morning = sum(1 for d in days if d.get("open"))
    evening = sum(1 for d in days if d.get("close"))
    acts = [split_line(s)[1] for d in days for s in d.get("close", []) if s.startswith("강점 행동")]
    done = sum(1 for a in acts if a == "실천했다")
    partial = sum(1 for a in acts if a == "일부 실천했다")
    weekend = sum(1 for x in dates if x.weekday() >= 5)
    gratitude = sum(1 for d in days for s in d.get("close", []) if s.startswith("감사일기"))
    peer_praise = sum(1 for d in days for s in d.get("open", []) if re.match(r"동료 \d+가 말해 준 내 장점", s))
    first3_end = start + dt.timedelta(days=20)
    first3 = sum(1 for x in dates if start <= x <= first3_end)
    confirmed = sum(1 for t in tasks if t["status"].strip() == "최종 확인 완료")
    sub = [t["submitted"] for t in tasks if t["submitted"].strip()]
    last = max(sub) if sub else ""
    first = min(sub) if sub else ""
    rest = len(tasks) - confirmed
    note = f" ({att['note']})" if att.get("note") else ""

    R, A, S = "리추얼 기록", att["source"], "내 제출 현황 (ALEPH 학생 대시보드)"
    return {
        "as_of": att["as_of"],
        "items": [
            {"id": "absent", "value": f"{att['absent']}일", "label": "결석",
             "detail": f"훈련일 {att['training_days']}일 중 출석 {att['present']}일, 출석률 {att['rate_percent']}%{note}", "source": A},
            {"id": "ritual_days", "value": f"{len(days)}일", "label": "리추얼 기록",
             "detail": f"과정 {elapsed_weeks}주째까지 {len(weeks_with)}주 모두 기록 · 아침 {morning}번, 저녁 {evening}번 · 주말 {weekend}일 포함", "source": R},
            {"id": "strength_done", "value": f"{done}/{len(acts)}", "label": "강점 행동 \"실천했다\"",
             "detail": f"저녁 기록의 강점 행동 칸 {len(acts)}번 중 실천했다 {done}번, 일부 실천했다 {partial}번", "source": R},
            {"id": "tasks", "value": f"{confirmed}/{len(tasks)}", "label": "과제 최종 확인 완료",
             "detail": f"전체 {len(tasks)}개 중 {confirmed}개 확인 완료({first} ~ {last} 제출)" + (f", {rest}개 진행 중" if rest else ""), "source": S},
        ] + ([
            {"id": "defense", "value": f"{defense['stages_done']}/{defense['stages_total']}", "label": "보안 방어전 단계 완료",
             "detail": f"{defense['name']} {defense['stages_total']}단계 중 {defense['stages_done']}단계 완료", "source": defense["source"]},
        ] if defense else []) + [
            {"id": "gratitude", "value": f"{gratitude}건", "label": "감사일기",
             "detail": f"동료가 말해 준 내 장점 {peer_praise}개", "source": R},
        ],
        "pairing": {
            "scene": story["pairing"]["scene"],
            "value": f"{first3}일",
            "label": f"첫 3주({start.month}월 {start.day}일~{first3_end.month}월 {first3_end.day}일) 리추얼 기록",
            "text": story["pairing"]["text"],
            "source": f"{R}, {A}",
        },
    }


def make_candidates(ritual):
    out = {k: [] for k in ABILITIES}
    for d in sorted(ritual["days"], key=lambda d: d["date"]):
        for part in ("open", "close"):
            for s in d.get(part, []):
                key, val = split_line(s)
                if key not in FIELDS or len(val) < 12:
                    continue
                if any(w in val for w in EXCLUDE):
                    continue
                for ability, words in ABILITIES.items():
                    hits = sorted({w for w in words if w in val})
                    if not hits:
                        continue
                    cid = sha(f"{d['date']}|{key}|{val}")[:10]
                    out[ability].append({"id": cid, "date": d["date"], "field": key,
                                         "text": val, "hits": hits, "score": len(hits)})
    for ability in out:
        out[ability].sort(key=lambda c: (-c["score"], c["date"], c["field"], c["id"]))
        out[ability] = out[ability][:TOP_N]
    return out


def candidates_md(cands, as_of):
    lines = [f"# 능력별 문단 후보 (기준일 {as_of})", "",
             "사이트에 넣고 싶은 후보의 id를 content/approved.json에 적고 다시 돌리면 사이트에 들어갑니다.", ""]
    for ability, items in cands.items():
        lines.append(f"## {ability}")
        lines.append("")
        for c in items:
            lines.append(f"- id `{c['id']}` · {c['date']} · {c['field']}")
            lines.append(f"  - 문장: {c['text']}")
            lines.append(f"  - 근거: 리추얼 기록 {c['date']} '{c['field']}' 칸, 단서 낱말 {', '.join(c['hits'])}")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="숫자 칸과 문단 후보를 다시 만듭니다.")
    ap.add_argument("--inputs", default=str(BASE / "inputs"))
    ap.add_argument("--content", default=str(BASE / "content"))
    ap.add_argument("--out", default=str(BASE / "output"))
    ap.add_argument("--site", default="", help="data.js를 복사할 사이트 폴더 (선택)")
    a = ap.parse_args()

    inp, con, out = Path(a.inputs), Path(a.content), Path(a.out)
    ritual, att, tasks, defense = load_inputs(inp)
    profile = json.loads((con / "profile.json").read_text(encoding="utf-8"))
    story = json.loads((con / "story.json").read_text(encoding="utf-8"))
    ap_path = con / "approved.json"
    approved_ids = json.loads(ap_path.read_text(encoding="utf-8"))["approved"] if ap_path.exists() else []

    numbers = count_numbers(ritual, att, tasks, story, defense)
    cands = make_candidates(ritual)
    by_id = {c["id"]: (ab, c) for ab, items in cands.items() for c in items}
    missing = [i for i in approved_ids if i not in by_id]
    approved = {}
    for i in approved_ids:
        if i in by_id:
            ab, c = by_id[i]
            approved.setdefault(ab, []).append({"date": c["date"], "text": c["text"], "source": f"리추얼 기록 {c['date']} · {c['field']}"})

    out.mkdir(parents=True, exist_ok=True)
    files = {
        "numbers.json": json.dumps(numbers, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        "candidates.md": candidates_md(cands, numbers["as_of"]) + "\n",
        "data.js": "window.SITE_DATA = " + json.dumps(
            {"profile": profile, "story": story, "numbers": numbers, "approved": approved},
            ensure_ascii=False, indent=2, sort_keys=True) + ";\n",
    }
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8", newline="\n")
    manifest = "".join(f"{sha(files[n])}  {n}\n" for n in sorted(files))
    (out / "manifest.txt").write_text(manifest, encoding="utf-8", newline="\n")

    if a.site:
        shutil.copyfile(out / "data.js", Path(a.site) / "data.js")

    print(f"기준일 {numbers['as_of']} · 리추얼 {len(ritual['days'])}일 · 과제 {len(tasks)}개")
    print(f"후보 {sum(len(v) for v in cands.values())}개 · 승인 {sum(len(v) for v in approved.values())}개")
    if missing:
        print("후보 목록에 없는 승인 id:", ", ".join(missing), file=sys.stderr)
    print(manifest, end="")


if __name__ == "__main__":
    main()
