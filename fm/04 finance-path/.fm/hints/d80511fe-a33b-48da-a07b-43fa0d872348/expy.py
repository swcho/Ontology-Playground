# 필요 패키지: plotly, kaleido
#   pip install plotly kaleido

# %% [markdown]
# # creditScore: string vs integer
#
# 온톨로지의 프로퍼티 타입은 "값을 어떻게 저장하는가"가 아니라
# **"이 프로퍼티로 어떤 연산이 허용되는가"**를 선언하는 계약이다.
#
# `creditScore`를 `string`으로 두면 질의 엔진은 그 값을 수로 다룰 근거가 없고,
# 비교는 **사전식(lexicographic)** 으로 떨어진다:
#
# $$\text{"90"} > \text{"700"} \quad\text{(문자 코드 } \texttt{'9'}=57 > \texttt{'7'}=55 \text{)}$$
#
# 반면 수치 비교는 $90 < 700$ 이다. 같은 데이터, 정반대의 답.
#
# 이 노트북에서 확인할 것:
# 1. 사전식 비교 vs 수치 비교의 결과가 갈린다
# 2. `> 700` 범위 필터 결과가 달라진다
# 3. 정렬 결과가 달라진다
# 4. 평균·분위수 같은 집계는 string에서 아예 불가능하다
# 5. 시각화: 신용점수 분포 + 임계값 선, string 정렬 vs int 정렬
# 6. 반대 사례: 계좌번호를 int로 만들면 선행 0이 사라진다

# %%
def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:  # VSCode 셀/Jupyter에서만 렌더링
            fig.show()
    except ImportError:
        pass


# %% [markdown]
# ## 1. 작은 고객 데이터셋
#
# 같은 `creditScore` 값을 두 가지 타입으로 담는다.
# - `score_int`: integer 모델링 (온톨로지의 올바른 선택)
# - `score_str`: string 모델링 (잘못된 선택)
#
# 마지막 두 행은 현실에서 흔한 지저분한 데이터다:
# 절단된 값 `"90"`, 스케일이 다른 소스에서 유입된 `"1000"`.

# %%
customers = [
    # (customerId, name, creditScore)
    ("C-001", "Ada", 812),
    ("C-002", "Bob", 705),
    ("C-003", "Cho", 700),
    ("C-004", "Dan", 668),
    ("C-005", "Eve", 615),
    ("C-006", "Fay", 90),  # 데이터 오류: 절단된 값
    ("C-007", "Gus", 1000),  # 데이터 오류: 다른 스케일 소스
]

rows = [
    {"customerId": cid, "name": nm, "score_int": s, "score_str": str(s)}
    for cid, nm, s in customers
]

for r in rows:
    print(f"{r['customerId']}  {r['name']:4s}  int={r['score_int']:<5d} str={r['score_str']!r}")
# 출력:
# C-001  Ada   int=812   str='812'
# C-002  Bob   int=705   str='705'
# C-003  Cho   int=700   str='700'
# C-004  Dan   int=668   str='668'
# C-005  Eve   int=615   str='615'
# C-006  Fay   int=90    str='90'
# C-007  Gus   int=1000  str='1000'

# %% [markdown]
# ## 2. 사전식 비교 vs 수치 비교
#
# 문자열 비교는 문자 코드를 왼쪽부터 훑는다. 자릿수(=크기)를 전혀 모른다.

# %%
pairs = [(90, 700), (800, 90), (1000, 812), (705, 700), (68, 668)]

print(f"{'a':>5} {'b':>5} | {'a<b (int)':>10} | {'a<b (str)':>10} | 일치?")
print("-" * 52)
for a, b in pairs:
    num = a < b
    lex = str(a) < str(b)
    print(f"{a:>5} {b:>5} | {str(num):>10} | {str(lex):>10} | {'OK' if num == lex else '<<< 불일치'}")
# 출력:
#     a     b |  a<b (int) |  a<b (str) | 일치?
# ----------------------------------------------------
#    90   700 |       True |      False | <<< 불일치
#   800    90 |      False |       True | <<< 불일치
#  1000   812 |      False |       True | <<< 불일치
#   705   700 |      False |      False | OK
#    68   668 |       True |      False | <<< 불일치
#
# 5개 쌍 중 4개가 불일치. 자릿수가 같은 705/700만 우연히 일치한다.
# (자릿수가 모두 같을 때만 사전식 == 수치 순서가 성립한다는 뜻)

# %%
# 문자 코드 단위로 무슨 일이 벌어지는지 직접 확인
print("'9' ->", ord("9"), " '7' ->", ord("7"))
print("'90' < '700' 판정은 첫 글자에서 끝난다:", ord("9"), "<", ord("7"), "=", ord("9") < ord("7"))
print("따라서 '90' > '700' 이다:", "90" > "700")
# 출력:
# '9' -> 57  '7' -> 55
# '90' < '700' 판정은 첫 글자에서 끝난다: 57 < 55 = False
# 따라서 '90' > '700' 이다: True

# %% [markdown]
# ## 3. 범위 필터 `creditScore > 700`
#
# 실제 대출 심사는 임계값 질의다:
#
# ```gql
# MATCH (c:Customer) WHERE c.creditScore > 700 RETURN c.name
# ```
#
# integer면 의도대로 동작한다. string이면 "첫 글자가 `'7'`보다 큰 문자로 시작하는 값"을
# 뽑는 전혀 다른 질의가 된다 — 그리고 **에러 없이** 조용히 틀린다.

# %%
THRESHOLD = 700

int_hits = [r["name"] for r in rows if r["score_int"] > THRESHOLD]
str_hits = [r["name"] for r in rows if r["score_str"] > str(THRESHOLD)]

print("integer 필터 (> 700) :", int_hits)
print("string  필터 (> '700'):", str_hits)
print()
print("string 필터에만 잡힌 오탐(false positive):", sorted(set(str_hits) - set(int_hits)))
print("string 필터가 놓친 누락(false negative)  :", sorted(set(int_hits) - set(str_hits)))
# 출력:
# integer 필터 (> 700) : ['Ada', 'Bob', 'Gus']
# string  필터 (> '700'): ['Ada', 'Bob', 'Fay']
#
# string 필터에만 잡힌 오탐(false positive): ['Fay']
# string 필터가 놓친 누락(false negative)  : ['Gus']

# %% [markdown]
# `Fay`(점수 90)는 우량 고객으로 통과했고, `Gus`(점수 1000)는 탈락했다.
# 두 건 모두 **대출 심사 오판**이다. 예외도, 경고도 없다.
#
# ### CFPB 차주 위험 프로파일로 버케팅해보기
#
# 실무의 등급 구간은 전부 $score \ge K$ 형태다:
#
# $$\text{tier}(s) = \begin{cases}
# \text{superprime} & s \ge 720 \\
# \text{prime} & 660 \le s < 720 \\
# \text{near-prime} & 620 \le s < 660 \\
# \text{subprime} & 580 \le s < 620 \\
# \text{deep subprime} & s < 580
# \end{cases}$$

# %%
def tier(score: int) -> str:
    if score >= 720:
        return "superprime"
    if score >= 660:
        return "prime"
    if score >= 620:
        return "near-prime"
    if score >= 580:
        return "subprime"
    return "deep subprime"


for r in rows:
    print(f"{r['name']:4s} {r['score_int']:>5} -> {tier(r['score_int'])}")

print()
try:
    tier(rows[0]["score_str"])  # string으로는 구간 판정 자체가 불가능
except TypeError as e:
    print("string으로 tier() 호출:", type(e).__name__, "-", e)
# 출력:
# Ada    812 -> superprime
# Bob    705 -> prime
# Cho    700 -> prime
# Dan    668 -> prime
# Eve    615 -> subprime
# Fay     90 -> deep subprime
# Gus   1000 -> superprime
#
# string으로 tier() 호출: TypeError - '>=' not supported between instances of 'str' and 'int'

# %% [markdown]
# ## 4. 정렬 (`ORDER BY creditScore DESC`)
#
# "우량 고객 상위 3명"을 뽑는 질의. 타입에 따라 명단이 바뀐다.

# %%
by_int = sorted(rows, key=lambda r: r["score_int"], reverse=True)
by_str = sorted(rows, key=lambda r: r["score_str"], reverse=True)

print(f"{'#':>2}  {'int 정렬':<16} {'str 정렬':<16}")
print("-" * 40)
for i, (a, b) in enumerate(zip(by_int, by_str), 1):
    print(f"{i:>2}  {a['name'] + ' (' + str(a['score_int']) + ')':<16} {b['name'] + ' (' + b['score_str'] + ')':<16}")

print()
print("TOP 3 (int):", [r["name"] for r in by_int[:3]])
print("TOP 3 (str):", [r["name"] for r in by_str[:3]])
# 출력:
#  #  int 정렬          str 정렬
# ----------------------------------------
#  1  Gus (1000)       Fay (90)
#  2  Ada (812)        Ada (812)
#  3  Bob (705)        Bob (705)
#  4  Cho (700)        Cho (700)
#  5  Dan (668)        Dan (668)
#  6  Eve (615)        Eve (615)
#  7  Fay (90)         Gus (1000)
#
# TOP 3 (int): ['Gus', 'Ada', 'Bob']
# TOP 3 (str): ['Fay', 'Ada', 'Bob']

# %% [markdown]
# ## 5. 집계: 평균·분위수는 string에서 불가능
#
# `AVG`, `MIN/MAX`, 분위수는 수치 타입만의 능력이다.
# string에서는 왜곡되거나(min/max) 아예 타입 에러가 난다(sum/avg).

# %%
import statistics

ints = [r["score_int"] for r in rows]
strs = [r["score_str"] for r in rows]

print("int  AVG    :", round(statistics.mean(ints), 1))
print("int  MEDIAN :", statistics.median(ints))
print("int  MIN/MAX:", min(ints), "/", max(ints))
print("int  분위수 (25/50/75):", [round(q) for q in statistics.quantiles(ints, n=4)])
print()
print("str  MIN/MAX:", min(strs), "/", max(strs), "  <- 사전식이라 의미가 뒤집힘")
try:
    statistics.mean(strs)
except TypeError as e:
    print("str  AVG    : TypeError -", e)
# 출력:
# int  AVG    : 655.7
# int  MEDIAN : 700
# int  MIN/MAX: 90 / 1000
# int  분위수 (25/50/75): [615, 700, 812]
#
# str  MIN/MAX: 1000 / 90   <- 사전식이라 의미가 뒤집힘
# str  AVG    : TypeError - can't convert type 'str' to numerator/denominator

# %% [markdown]
# `min(strs)`가 `'1000'`, `max(strs)`가 `'90'`이다.
# 최저 신용점수가 1000, 최고가 90이라는 보고서가 나온다.
#
# 히스토그램 관점에서도 결정적 차이가 있다. string은 **순서 없는 명목형(nominal)** 축이라
# 값마다 독립 카테고리가 되고, "600~650 구간" 같은 버킷 자체를 만들 수 없다.
# 질의 엔진 입장에서도 B-tree 인덱스 범위 스캔과 수치 분포 통계를 쓸 수 없어
# 실행 계획이 전체 스캔으로 떨어진다.

# %% [markdown]
# ## 6. 시각화
#
# 좀 더 현실적인 분포(FICO 300~850)를 만들어 히스토그램에 임계값 선을 얹고,
# 옆에 "string 정렬 vs int 정렬" 비교를 붙인다.

# %%
import random

random.seed(42)

# FICO 도메인 300~850 안에 들어오는 합성 신용점수 분포 (고신용 쪽으로 치우침)
population = [
    max(300, min(850, round(random.gauss(710, 75)))) for _ in range(1200)
]
print("n =", len(population))
print("min/max :", min(population), "/", max(population))
print("mean    :", round(statistics.mean(population), 1))
print("> 700 비율:", f"{sum(1 for s in population if s > 700) / len(population):.1%}")
# 출력:
# n = 1200
# min/max : 473 / 850
# mean    : 707.0
# > 700 비율: 54.0%

# %%
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#   (점수, 라벨, 색, 라벨을 얹을 높이)  -- 높이를 번갈아 두어 라벨 겹침 방지
THRESHOLDS = [
    (580, "580 FHA 최소", "#c0392b", 86),
    (620, "620 모기지", "#e67e22", 78),
    (660, "660 prime", "#16a085", 86),
    (720, "720 superprime", "#2980b9", 78),
]

fig = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.62, 0.38],
    subplot_titles=(
        "creditScore 분포 (integer) + 대출 심사 임계값",
        "정렬 결과: string(사전식) vs integer(수치)",
    ),
)

# --- 좌: 히스토그램 + 임계값 선 ---
fig.add_trace(
    go.Histogram(
        x=population,
        xbins=dict(start=300, end=850, size=10),
        marker=dict(color="#7f8c8d", line=dict(width=0)),
        name="고객 수",
        hovertemplate="점수 %{x}<br>%{y}명<extra></extra>",
        showlegend=False,
    ),
    row=1,
    col=1,
)

for x, label, color, ypos in THRESHOLDS:
    fig.add_vline(x=x, line=dict(color=color, width=2, dash="dash"), row=1, col=1)
    fig.add_annotation(
        x=x,
        y=ypos,
        text=label,
        showarrow=False,
        xanchor="left",
        xshift=3,
        font=dict(size=10, color=color),
        bgcolor="rgba(255,255,255,0.75)",
        row=1,
        col=1,
    )

fig.update_xaxes(title_text="creditScore (300–850)", range=[300, 870], row=1, col=1)
fig.update_yaxes(title_text="고객 수", range=[0, 95], row=1, col=1)

# --- 우: 정렬 비교 (같은 7개 값, 두 가지 순서) ---
names_int = [f"{r['name']} ({r['score_int']})" for r in by_int][::-1]
vals_int = [r["score_int"] for r in by_int][::-1]
names_str = [f"{r['name']} ({r['score_str']})" for r in by_str][::-1]
vals_str = [r["score_int"] for r in by_str][::-1]

fig.add_trace(
    go.Bar(
        y=list(range(7)),
        x=vals_str,
        orientation="h",
        name="string 정렬 순서",
        marker_color="#e74c3c",
        opacity=0.85,
        text=names_str,
        textposition="auto",
        insidetextanchor="start",
        textfont=dict(size=10),
        cliponaxis=False,
        hovertemplate="string 정렬 %{customdata}위: %{text}<extra></extra>",
        customdata=list(range(7, 0, -1)),
    ),
    row=1,
    col=2,
)
fig.add_trace(
    go.Bar(
        y=list(range(7)),
        x=vals_int,
        orientation="h",
        name="integer 정렬 순서",
        marker_color="#2980b9",
        opacity=0.85,
        text=names_int,
        textposition="auto",
        insidetextanchor="start",
        textfont=dict(size=10),
        cliponaxis=False,
        hovertemplate="integer 정렬 %{customdata}위: %{text}<extra></extra>",
        customdata=list(range(7, 0, -1)),
    ),
    row=1,
    col=2,
)

fig.update_xaxes(title_text="creditScore 값", range=[0, 1250], row=1, col=2)
fig.update_yaxes(showticklabels=False, title_text="정렬 순위 (위 = 1위)", row=1, col=2)

fig.update_layout(
    title=dict(
        text="프로퍼티 타입은 연산 능력의 선언: string은 사전식, integer는 수치",
        font=dict(size=16),
        x=0.5,
        xanchor="center",
        y=0.97,
    ),
    barmode="group",
    bargap=0.15,
    template="plotly_white",
    width=1150,
    height=560,
    legend=dict(orientation="h", yanchor="top", y=-0.20, x=0.60),
    margin=dict(t=110, b=120),
)

_show(fig)

# %%
import pathlib

out = pathlib.Path(__file__).parent / "expy.png" if "__file__" in dir() else pathlib.Path("expy.png")
fig.write_image(str(out), scale=2)
print("saved:", out)
# 출력:
# saved: /Users/.../.fm/hints/d80511fe-a33b-48da-a07b-43fa0d872348/expy.png

# %% [markdown]
# 좌측: `> 700` 같은 임계값 필터는 **수치 축 위의 한 지점**으로만 표현된다.
# string 축이라면 값들이 순서 없는 카테고리로 흩어져 이 선을 그을 자리가 없다.
#
# 우측: 같은 7개 값인데 `Fay(90)`가 string 정렬에서 1위로, `Gus(1000)`가 최하위로 간다.

# %% [markdown]
# ## 7. 반대 사례: 숫자처럼 보여도 string이어야 하는 것
#
# 판별 기준은 "생김새"가 아니라 **"덧셈·평균·크기 비교가 의미를 갖는가"**다.
# `accountNumber`, `ssn`, `zipCode`는 숫자로만 이루어져 있어도 string이 맞다.
# integer로 바꾸면 **선행 0이 되돌릴 수 없이 사라진다.**

# %%
accounts = ["0012345678", "0000004521", "9876543210", "0100200300"]

print(f"{'원본 (string)':<14} {'int 변환':>12}  {'다시 문자열':<12} 손상?")
print("-" * 52)
for a in accounts:
    n = int(a)
    back = str(n)
    print(f"{a:<14} {n:>12}  {back:<12} {'<<< 계좌 불일치' if back != a else 'OK'}")
# 출력:
# 원본 (string)      int 변환  다시 문자열   손상?
# ----------------------------------------------------
# 0012345678         12345678  12345678     <<< 계좌 불일치
# 0000004521             4521  4521         <<< 계좌 불일치
# 9876543210       9876543210  9876543210   OK
# 0100200300        100200300  100200300    <<< 계좌 불일치

# %%
# 무의미한 산술이 "조용히 성공"하는 문제
print("AVG(accountNumber) =", round(statistics.mean(int(a) for a in accounts), 1))
print("  -> 문법적으로는 되지만 의미가 전혀 없다. 대시보드에 '평균 계좌번호'가 뜬다.")
print()
print("우편번호도 동일:", "02134", "->", int("02134"), "(Boston 우편번호 손상)")
print()
print("SSN은 하이픈 때문에 애초에 캐스팅도 안 된다:")
try:
    int("123-45-6789")
except ValueError as e:
    print("  ValueError -", e)
# 출력:
# AVG(accountNumber) = 2497273427.2
#   -> 문법적으로는 되지만 의미가 전혀 없다. 대시보드에 '평균 계좌번호'가 뜬다.
#
# 우편번호도 동일: 02134 -> 2134 (Boston 우편번호 손상)
#
# SSN은 하이픈 때문에 애초에 캐스팅도 안 된다:
#   ValueError - invalid literal for int() with base 10: '123-45-6789'

# %% [markdown]
# ## 8. 정리표
#
# | 프로퍼티 | 타입 | 근거 (필요한 연산) |
# |---|---|---|
# | `creditScore` | **integer** | 범위 필터·정렬·평균·분위수·버케팅 (300–850 유계 스케일) |
# | `balance`, `principal`, `apr` | decimal | 산술 + 소수 정밀도 |
# | `term` | integer (months) | 기간 비교·산술 |
# | `timestamp` | datetime | 시각 정밀도 (사기 탐지) |
# | `accountNumber`, `ssn`, `*Id` | **string** | 식별자. 선행 0 보존, 산술 무의미 |
#
# **핵심**: 타입은 저장 형식이 아니라 계약이다.
# `creditScore: integer`는 질의 엔진에게 "비교·범위·집계 가능"을 알려주고,
# `accountNumber: string`은 "이건 라벨이니 산술하지 말라"를 알려준다.
# 둘 다 타입의 순기능이다.
