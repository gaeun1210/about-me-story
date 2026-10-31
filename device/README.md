# 계속 새로 쓰는 장치 (build.py)

새 기록을 넣으면 사이트의 **숫자 칸**과 **능력별 문단 후보**를 다시 만듭니다.
AI를 부르지 않고 파이썬 표준 라이브러리만 쓰므로, 같은 입력이면 언제 돌려도 같은 결과가 나옵니다.
API 키나 비밀번호는 필요 없습니다.

## 돌리는 방법 (3단계)

1. `inputs/` 폴더의 세 파일을 새 기록으로 바꿉니다.
   - `ritual.json`: 대시보드에서 내려받은 리추얼 기록 파일을 그대로 넣습니다.
   - `defense.json`(선택): 메모리얼 파크의 방어전 단계 수를 옮겨 적습니다.
   - `attendance.json`: 「내 출석 기록」의 훈련일·출석·결석·출석률과 기준일(`as_of`)을 옮겨 적습니다.
   - `assignments.csv`: 「내 제출 현황」의 과제를 한 줄에 하나씩 적습니다.
2. 이 폴더에서 명령 창을 열고 실행합니다(Python 3.8 이상).
   ```
   python build.py --site ..
   ```
   Windows에서 `python`을 찾을 수 없다고 나오면 `py build.py --site ..`로 실행합니다. `--site`에는 `index.html`이 있는 사이트 폴더를 적습니다(공개 저장소에서는 `..`, 제출 ZIP에서는 함께 둔 사이트 폴더).
3. `output/candidates.md`에서 사이트에 넣을 후보의 id를 골라 `content/approved.json`에 적고, 2단계를 한 번 더 돌립니다.
   승인한 문장만 사이트의 `data.js`에 들어갑니다.

## 무엇이 나오나요

| 파일 | 내용 |
|---|---|
| `output/numbers.json` | 숫자 칸(값·설명·출처)과 고난 장면에 짝지은 숫자 |
| `output/candidates.md` | 자기조절력·대인관계력·자기동기력별 후보 5개씩(날짜·칸 이름·근거 낱말·id) |
| `output/data.js` | 사이트가 읽는 데이터(이름·한 줄 소개·이야기·숫자·승인된 문장) |
| `output/manifest.txt` | 위 세 파일의 SHA-256. 두 번 돌린 결과가 같은지 비교할 때 씁니다 |

## 같은 결과인지 확인하기

```
python build.py
copy output\manifest.txt first.txt      (macOS·리눅스: cp output/manifest.txt first.txt)
python build.py
fc first.txt output\manifest.txt        (macOS·리눅스: diff first.txt output/manifest.txt)
```
"차이가 없습니다"(또는 아무것도 출력되지 않음)가 나오면 통과입니다.

## 직접 쓰는 파일 (`content/`)

- `profile.json`: 이름, 한 줄 소개, 연락 이메일, 대표작(13번 앱은 공개 후 `link`를 채움)
- `story.json`: 이야기 본편. 첫 문장과 마지막 문장은 본인이 직접 씁니다
- `approved.json`: 사이트에 넣기로 승인한 후보 id

## 지켜지는 것

- 동료가 쓴 칸(동료가 말해 준 장점, 동료가 나눈 감사)은 후보에 넣지 않습니다.
- 건강처럼 사적인 낱말이 들어간 문장은 후보에서 뺍니다(`EXCLUDE` 목록).
- 리추얼 기록 속 다른 사람 이름은 이미 "(이름 가림)"으로 가려져 있습니다.

## 공개 저장소에 대해

공개 저장소에는 리추얼 원본(`inputs/ritual.json`)과 후보 목록(`output/candidates.md`)을 올리지 않습니다. 개인 기록이 담겨 있기 때문입니다. 직접 돌릴 때는 대시보드에서 받은 리추얼 파일을 `inputs/ritual.json`으로 넣으면 됩니다.
