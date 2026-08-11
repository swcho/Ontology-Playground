# 필요 패키지: pandas, plotly, kaleido
# 실행: python3 expy.py  (Jupyter percent script 형식)

# %% [markdown]
# # Work-Order의 startDate / dueDate — 왜 둘 다 필요한가
#
# Smart Manufacturing 온톨로지의 `Work-Order`는 다음 속성을 갖는다.
#
# | Property | Type | Identifier? |
# |---|---|---|
# | `workOrderId` | string | ✓ |
# | `priority` | string | |
# | `status` | string | |
# | `startDate` | date | |
# | `dueDate` | date | |
#
# 날짜가 **두 개**인 이유는 하나의 값으로는 표현할 수 없는 두 축을 동시에 얻기 위해서다.
#
# - `startDate` → **기간(duration)** 의 시작점. 계획 리드타임을 만든다.
# - `dueDate` → **약속(commitment)** 의 끝점. 지연 여부의 기준선을 만든다.
#
# 두 값이 함께 있어야 **일정 준수(schedule adherence)** 를 계산할 수 있다.
#
# $$\text{leadTime} = \text{dueDate} - \text{startDate}$$
# $$\text{slack} = \text{dueDate} - \text{today}$$
# $$\text{lateness} = \text{completedDate} - \text{dueDate}$$
# $$\text{adherence} = \frac{|\{wo : \text{completedDate} \le \text{dueDate}\}|}{|\{wo : \text{status}=\text{completed}\}|}$$

# %%
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _show(fig):
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            fig.show()
    except ImportError:
        pass


# 재현 가능한 결과를 위해 '오늘'을 고정한다 (datetime.now() 사용 금지)
TODAY = date(2026, 3, 16)
print("TODAY =", TODAY)
# 출력: TODAY = 2026-03-16

# %% [markdown]
# ## 1. Work-Order 인스턴스 만들기
#
# `assigned_to` 관계로 각 작업지시가 어떤 `Machine`에 배정됐는지도 함께 표현한다.
# `completedDate`는 온톨로지 속성은 아니지만, 실적(actual)을 계획(plan)과 대조하기 위한 관측값으로 둔다.

# %%
work_orders = [
    # (workOrderId, machine, priority, status, startDate, dueDate, completedDate)
    ("WO-1001", "CNC-01", "high", "completed", date(2026, 3, 2), date(2026, 3, 6), date(2026, 3, 5)),
    ("WO-1002", "CNC-01", "medium", "completed", date(2026, 3, 3), date(2026, 3, 9), date(2026, 3, 12)),
    ("WO-1003", "PRESS-02", "high", "completed", date(2026, 3, 4), date(2026, 3, 10), date(2026, 3, 10)),
    ("WO-1004", "PRESS-02", "low", "completed", date(2026, 3, 1), date(2026, 3, 13), date(2026, 3, 18)),
    ("WO-1005", "LATHE-03", "high", "in_progress", date(2026, 3, 11), date(2026, 3, 15), None),
    ("WO-1006", "LATHE-03", "medium", "in_progress", date(2026, 3, 12), date(2026, 3, 20), None),
    ("WO-1007", "CNC-01", "low", "in_progress", date(2026, 3, 14), date(2026, 3, 27), None),
]

df = pd.DataFrame(
    work_orders,
    columns=["workOrderId", "machine", "priority", "status", "startDate", "dueDate", "completedDate"],
)
print(df.to_string(index=False))
# 출력:
# workOrderId  machine priority      status  startDate    dueDate completedDate
#     WO-1001   CNC-01     high   completed 2026-03-02 2026-03-06    2026-03-05
#     WO-1002   CNC-01   medium   completed 2026-03-03 2026-03-09    2026-03-12
#     WO-1003 PRESS-02     high   completed 2026-03-04 2026-03-10    2026-03-10
#     WO-1004 PRESS-02      low   completed 2026-03-01 2026-03-13    2026-03-18
#     WO-1005 LATHE-03     high in_progress 2026-03-11 2026-03-15          None
#     WO-1006 LATHE-03   medium in_progress 2026-03-12 2026-03-20          None
#     WO-1007   CNC-01      low in_progress 2026-03-14 2026-03-27          None

# %% [markdown]
# ## 2. 두 날짜로부터 파생되는 지표들
#
# - **leadTime** = `dueDate - startDate` → 계획된 작업 기간(일)
# - **slack** = `dueDate - TODAY` → 남은 여유일 (음수면 이미 마감 초과)
# - **elapsed** = `TODAY - startDate` → 경과일
# - **progressRatio** = $\dfrac{\text{elapsed}}{\text{leadTime}}$ → 시간축 소진률. **두 날짜가 있어야만** 정의된다.

# %%
def days(a, b):
    """b 기준 a까지의 일수 (a - b)."""
    return (a - b).days


df["leadTime"] = [days(d, s) for s, d in zip(df.startDate, df.dueDate)]
df["slack"] = [days(d, TODAY) for d in df.dueDate]
df["elapsed"] = [days(TODAY, s) for s in df.startDate]
df["progressRatio"] = (df["elapsed"] / df["leadTime"]).round(2)

print(df[["workOrderId", "status", "leadTime", "elapsed", "slack", "progressRatio"]].to_string(index=False))
# 출력:
# workOrderId      status  leadTime  elapsed  slack  progressRatio
#     WO-1001   completed         4       14    -10           3.50
#     WO-1002   completed         6       13     -7           2.17
#     WO-1003   completed         6       12     -6           2.00
#     WO-1004   completed        12       15     -3           1.25
#     WO-1005 in_progress         4        5     -1           1.25
#     WO-1006 in_progress         8        4      4           0.50
#     WO-1007 in_progress        13        2     11           0.15

# %% [markdown]
# ## 3. 일정 준수(schedule adherence) 판정
#
# - 완료된 작업지시: `completedDate <= dueDate` 이면 **on_time**, 아니면 **late** (`lateness` 일 초과)
# - 진행 중 작업지시: `slack < 0` 이면 이미 **at_risk(overdue)**, 아니면 **on_track**
#
# 준수율은 완료 건 기준으로 계산한다.
#
# $$\text{adherence} = \frac{\#\text{on\_time}}{\#\text{completed}}$$

# %%
def classify(row):
    if row.status == "completed":
        late_days = days(row.completedDate, row.dueDate)
        return ("on_time" if late_days <= 0 else "late"), late_days
    return ("on_track" if row.slack >= 0 else "overdue"), None


df[["adherence", "lateness"]] = [classify(r) for r in df.itertuples()]
print(df[["workOrderId", "priority", "status", "dueDate", "completedDate", "adherence", "lateness"]].to_string(index=False))
# 출력:
# workOrderId priority      status    dueDate completedDate adherence lateness
#     WO-1001     high   completed 2026-03-06    2026-03-05   on_time     -1.0
#     WO-1002   medium   completed 2026-03-09    2026-03-12      late      3.0
#     WO-1003     high   completed 2026-03-10    2026-03-10   on_time      0.0
#     WO-1004      low   completed 2026-03-13    2026-03-18      late      5.0
#     WO-1005     high in_progress 2026-03-15          None   overdue      NaN
#     WO-1006   medium in_progress 2026-03-20          None  on_track      NaN
#     WO-1007      low in_progress 2026-03-27          None  on_track      NaN

# %%
done = df[df.status == "completed"]
rate = (done.adherence == "on_time").mean()
print(f"완료 {len(done)}건 중 정시 {int((done.adherence == 'on_time').sum())}건 → schedule adherence = {rate:.0%}")
print(f"평균 지연일(late 건만) = {done.loc[done.adherence == 'late', 'lateness'].mean():.1f}일")
# 출력: 완료 4건 중 정시 2건 → schedule adherence = 50%
# 출력: 평균 지연일(late 건만) = 4.0일

# %% [markdown]
# ## 4. `priority`와 결합 — 생산 계획 질의
#
# > Work orders have both `startDate` and `dueDate` — enabling schedule adherence calculations.
# > Combined with `priority`, this powers production planning queries.
#
# 예: **"high 우선순위인데 마감이 임박(slack이 작은)한 작업지시부터 처리하라"** 같은
# 디스패칭 규칙은 `priority` + `slack`(=dueDate 기반) 두 축이 모두 있어야 성립한다.
# 이는 스케줄링 이론의 *Critical Ratio* / *Minimum Slack* 규칙과 같다.
#
# $$\text{CR} = \frac{\text{dueDate} - \text{today}}{\text{잔여 작업일}}$$

# %%
prio_rank = {"high": 0, "medium": 1, "low": 2}
queue = df[df.status == "in_progress"].copy()
queue["prio_rank"] = queue.priority.map(prio_rank)
queue = queue.sort_values(["prio_rank", "slack"])
print("디스패칭 순서 (priority → slack):")
print(queue[["workOrderId", "priority", "slack", "adherence"]].to_string(index=False))
# 출력: 디스패칭 순서 (priority → slack):
# workOrderId priority  slack adherence
#     WO-1005     high     -1   overdue
#     WO-1006   medium      4  on_track
#     WO-1007      low     11  on_track

# %%
by_prio = (
    done.assign(on_time=lambda d: d.adherence == "on_time")
    .groupby("priority")
    .agg(n=("workOrderId", "count"), adherence=("on_time", "mean"), avg_lead=("leadTime", "mean"))
)
print(by_prio.to_string())
# 출력:
#           n  adherence  avg_lead
# priority
# high      2        1.0       5.0
# low       1        0.0      12.0
# medium    1        0.0       6.0

# %% [markdown]
# ## 5. 날짜가 하나뿐이라면? — 반례
#
# | 가진 것 | 계산 가능 | 계산 **불가능** |
# |---|---|---|
# | `startDate`만 | 언제 착수했는가, 경과일 | 기간, 지연 여부, slack, 준수율 |
# | `dueDate`만 | 지연 여부(완료일이 있다면) | 계획 기간, 진행률, 작업 부하(load) |
# | 둘 다 | 기간 · slack · 진행률 · 준수율 · 간트 차트 | — |
#
# 아래에서 확인해 보자. 두 작업지시는 **dueDate가 같지만** 계획 기간이 3배 차이난다.

# %%
a = df[df.workOrderId == "WO-1003"].iloc[0]  # 3/4 ~ 3/10
b = df[df.workOrderId == "WO-1004"].iloc[0]  # 3/1 ~ 3/13
print(f"{a.workOrderId}: due={a.dueDate}, leadTime={a.leadTime}일")
print(f"{b.workOrderId}: due={b.dueDate}, leadTime={b.leadTime}일")
print("→ dueDate만 보면 두 작업의 '무게'(설비 점유 기간)를 구분할 수 없다.")
print("→ startDate만 보면 어느 쪽이 지연인지 판단할 기준선이 없다.")
# 출력: WO-1003: due=2026-03-10, leadTime=6일
# 출력: WO-1004: due=2026-03-13, leadTime=12일
# 출력: → dueDate만 보면 두 작업의 '무게'(설비 점유 기간)를 구분할 수 없다.
# 출력: → startDate만 보면 어느 쪽이 지연인지 판단할 기준선이 없다.

# %% [markdown]
# ## 6. 간트 차트 — 구간(startDate→dueDate)과 마감선(dueDate)
#
# 막대는 `startDate`~`dueDate` 계획 구간, ◆ 마커는 `dueDate`,
# ✕ 마커는 실제 `completedDate`다. 마감선 오른쪽에 ✕가 찍히면 지연이다.

# %%
plot_df = df.copy()
plot_df["start_dt"] = pd.to_datetime(plot_df.startDate)
plot_df["due_dt"] = pd.to_datetime(plot_df.dueDate)
plot_df["label"] = plot_df.workOrderId + " (" + plot_df.machine + ", " + plot_df.priority + ")"
plot_df = plot_df.sort_values("start_dt", ascending=False)

color_map = {"on_time": "#2E7D32", "late": "#C62828", "on_track": "#1565C0", "overdue": "#EF6C00"}

fig = px.timeline(
    plot_df,
    x_start="start_dt",
    x_end="due_dt",
    y="label",
    color="adherence",
    color_discrete_map=color_map,
    hover_data={"leadTime": True, "slack": True, "progressRatio": True, "start_dt": False, "due_dt": False},
    title="Work-Order 계획 구간(startDate→dueDate)과 일정 준수",
)
fig.update_traces(width=0.5)

# dueDate 마커
fig.add_trace(
    go.Scatter(
        x=plot_df.due_dt,
        y=plot_df.label,
        mode="markers",
        marker=dict(symbol="diamond", size=12, color="#37474F"),
        name="dueDate (마감)",
    )
)

# 실제 완료일 마커
fin = plot_df[plot_df.completedDate.notna()]
fig.add_trace(
    go.Scatter(
        x=pd.to_datetime(fin.completedDate),
        y=fin.label,
        mode="markers",
        marker=dict(symbol="x", size=12, color="#B71C1C"),
        name="completedDate (실적)",
    )
)

# 오늘 기준선 (kaleido 직렬화를 위해 ISO 문자열로 전달)
_today_iso = TODAY.isoformat()
fig.add_vline(x=_today_iso, line_width=2, line_dash="dash", line_color="#6A1B9A")
fig.add_annotation(
    x=_today_iso, y=1.03, yref="paper", text=f"TODAY {_today_iso}", showarrow=False, font=dict(color="#6A1B9A")
)

fig.update_yaxes(title="")
fig.update_xaxes(title="date")
fig.update_layout(
    height=460,
    width=1000,
    legend_title_text="adherence",
    margin=dict(l=10, r=10, t=80, b=40),
)

_show(fig)

import os

_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expy.png")
fig.write_image(_out, scale=2)
print("saved:", _out)
# 출력: saved: .../expy.png

# %% [markdown]
# ## 정리
#
# - `startDate`는 **기간**을, `dueDate`는 **약속**을 표현한다. 하나만으로는 둘 중 하나가 소실된다.
# - 두 날짜가 있어야 `leadTime`, `slack`, `progressRatio`, `lateness`, **schedule adherence**가 계산된다.
# - `priority`와 결합하면 *"우선순위 높고 slack 작은 순서로 처리"* 같은
#   생산 계획/디스패칭 질의를 온톨로지 위에서 곧바로 표현할 수 있다.
# - 온톨로지 설계 관점: 이벤트/일정 엔티티는 **구간(interval)** 을 표현할 수 있게
#   시작·종료 두 속성을 쌍으로 두는 것이 기본 패턴이다.
