
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from pathlib import Path
import re

# -----------------------------------
# 1. 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="월별 평균기온 예측",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 평균기온 분석 및 예측")
st.write(
    "과거 기온 데이터를 분석하고 "
    "선형회귀 알고리즘을 이용하여 미래 기온을 예측합니다."
)

st.divider()

# -----------------------------------
# 2. CSV 파일 불러오기
# -----------------------------------
# 현재 파일은 pages 폴더에 있고
# CSV 파일은 상위 폴더에 있음

file_path = Path(__file__).resolve().parent.parent / "temperature.csv"

# 경로 확인
if not file_path.exists():
    file_path = Path("temperature.csv")

if not file_path.exists():
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "프로젝트 최상위 폴더에 파일을 넣어주세요."
    )
    st.stop()

# CSV 한글 인코딩 처리
try:
    df = pd.read_csv(file_path, encoding="cp949")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="utf-8-sig")

# -----------------------------------
# 3. 데이터 전처리
# -----------------------------------

required_columns = ["일시", "평균기온(℃)"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일에 필요한 열이 없습니다.")
    st.write("현재 CSV 열:", df.columns.tolist())
    st.stop()

# 날짜의 월 이름 변환
month_dict = {
    "Jan": 1, "Feb": 2, "Mar": 3,
    "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9,
    "Oct": 10, "Nov": 11, "Dec": 12
}

def parse_date(value):
    match = re.fullmatch(
        r"\s*([A-Za-z]{3})-(\d{2,4})\s*",
        str(value)
    )

    if not match:
        return pd.NaT

    month_name = match.group(1).title()
    year_text = match.group(2)

    month = month_dict.get(month_name)

    if month is None:
        return pd.NaT

    year = int(year_text)

    # 이 데이터는 2007~2026년 자료이므로
    # 두 자리 연도는 2000년대로 변환
    if len(year_text) == 2:
        year += 2000

    return pd.Timestamp(year=year, month=month, day=1)


df["날짜"] = df["일시"].apply(parse_date)

df["평균기온(℃)"] = pd.to_numeric(
    df["평균기온(℃)"],
    errors="coerce"
)

df = df.dropna(
    subset=["날짜", "평균기온(℃)"]
).copy()

df["연도"] = df["날짜"].dt.year
df["월"] = df["날짜"].dt.month

if df.empty:
    st.error("분석할 수 있는 기온 데이터가 없습니다.")
    st.stop()

# -----------------------------------
# 4. 사용자 입력
# -----------------------------------

st.subheader("📌 예측 조건 선택")

col1, col2 = st.columns(2)

with col1:
    selected_month = st.selectbox(
        "분석할 월을 선택하세요",
        options=list(range(1, 13)),
        format_func=lambda x: f"{x}월"
    )

with col2:
    selected_year = st.number_input(
        "예측할 연도를 입력하세요",
        min_value=1900,
        max_value=2100,
        value=2030,
        step=1
    )

# -----------------------------------
# 5. 선택한 월의 데이터 추출
# -----------------------------------

monthly_df = df[df["월"] == selected_month].copy()

monthly_df = monthly_df.sort_values("연도")

if len(monthly_df) < 2:
    st.error("선택한 월의 데이터가 2개 미만입니다.")
    st.stop()

X = monthly_df[["연도"]]
y = monthly_df["평균기온(℃)"]

# -----------------------------------
# 6. 선형회귀 모델 학습
# -----------------------------------

model = LinearRegression()

model.fit(X, y)

# 예측값 계산
predicted_temp = model.predict(
    pd.DataFrame({"연도": [int(selected_year)]})
)[0]

# 과거 데이터의 회귀 예측값
monthly_df["회귀예측기온"] = model.predict(X)

# 회귀계수
slope = model.coef_[0]
intercept = model.intercept_

# 결정계수
r2 = model.score(X, y)

# -----------------------------------
# 7. 예측 결과 출력
# -----------------------------------

st.divider()
st.subheader(f"🌡️ {selected_month}월 평균기온 예측 결과")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "예측 연도",
        f"{int(selected_year)}년"
    )

with col2:
    st.metric(
        "예측 평균기온",
        f"{predicted_temp:.2f} ℃"
    )

with col3:
    st.metric(
        "회귀모델 결정계수 R²",
        f"{r2:.3f}"
    )

# 데이터 범위 안내
last_year = int(monthly_df["연도"].max())

if selected_year > last_year:
    st.info(
        f"이 예측은 마지막 관측 연도인 {last_year}년 이후의 "
        "미래 예측입니다. 장기 예측일수록 오차가 커질 수 있습니다."
    )
elif selected_year < int(monthly_df["연도"].min()):
    st.warning(
        "입력한 연도가 과거 데이터 범위보다 이전입니다. "
        "회귀선을 이용한 외삽 결과입니다."
    )
else:
    st.info(
        "입력한 연도는 기존 데이터 범위 안에 있습니다. "
        "회귀모델의 추정값을 표시합니다."
    )

# -----------------------------------
# 8. 그래프 시각화
# -----------------------------------

st.divider()
st.subheader("📈 과거 평균기온과 선형회귀 예측 그래프")

fig, ax = plt.subplots(figsize=(12, 6))

# 1) 실제 과거 평균기온
ax.plot(
    monthly_df["연도"],
    monthly_df["평균기온(℃)"],
    color="royalblue",
    marker="o",
    linewidth=2,
    markersize=6,
    label="Actual Average Temperature"
)

# 2) 회귀 직선
start_year = min(
    int(monthly_df["연도"].min()),
    int(selected_year)
)

end_year = max(
    int(monthly_df["연도"].max()),
    int(selected_year)
)

line_years = np.arange(
    start_year,
    end_year + 1
)

line_predictions = model.predict(
    pd.DataFrame({"연도": line_years})
)

ax.plot(
    line_years,
    line_predictions,
    color="red",
    linestyle="--",
    linewidth=2.5,
    label="Linear Regression Line"
)

# 3) 미래 예측 지점
ax.scatter(
    [selected_year],
    [predicted_temp],
    color="darkorange",
    edgecolors="black",
    s=180,
    zorder=5,
    label="Predicted Temperature"
)

# 예측값 표시
ax.annotate(
    f"{predicted_temp:.2f} °C",
    xy=(selected_year, predicted_temp),
    xytext=(10, 15),
    textcoords="offset points",
    fontsize=12,
    fontweight="bold",
    color="darkorange"
)

# 그래프 꾸미기
ax.set_title(
    f"{selected_month} Month Average Temperature Prediction",
    fontsize=16
)

ax.set_xlabel("Year", fontsize=12)
ax.set_ylabel("Average Temperature (°C)", fontsize=12)

ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

st.pyplot(fig)

plt.close(fig)

# -----------------------------------
# 9. 회귀식 출력
# -----------------------------------

st.subheader("📐 선형회귀 알고리즘 계산 결과")

st.write(
    f"**회귀 방정식:** "
    f"평균기온 = ({slope:.4f} × 연도) + ({intercept:.4f})"
)

if slope > 0:
    st.write(
        f"선택한 월의 평균기온은 연도가 1년 증가할 때 "
        f"평균적으로 약 {slope:.4f}℃ 상승하는 경향이 있습니다."
    )
elif slope < 0:
    st.write(
        f"선택한 월의 평균기온은 연도가 1년 증가할 때 "
        f"평균적으로 약 {abs(slope):.4f}℃ 하락하는 경향이 있습니다."
    )
else:
    st.write("회귀선의 기울기가 0에 가까워 뚜렷한 변화가 없습니다.")

# -----------------------------------
# 10. 선형회귀 알고리즘 쉽게 설명
# -----------------------------------

st.divider()

st.subheader("📚 선형회귀 알고리즘이란?")

st.markdown("""
### ① 선형회귀란?

선형회귀는 과거의 데이터에 나타난 경향을 분석하여
미래의 값을 예측하는 머신러닝 알고리즘입니다.

이번 프로그램에서는 다음과 같은 관계를 학습합니다.

- X축: 연도
- Y축: 해당 월의 평균기온

예를 들어 1월을 선택하면 2008년부터 2026년까지의
1월 평균기온을 이용하여 기온 변화의 경향을 분석합니다.

### ② 어떻게 작동할까요?

1. 과거 연도별 평균기온을 점으로 표시합니다.
2. 모든 점과의 오차가 작아지는 직선을 찾습니다.
3. 이 직선을 이용하여 입력한 미래 연도의 기온을 계산합니다.

### ③ 빨간색 점선은 무엇인가요?

빨간색 점선은 선형회귀 알고리즘이 계산한 회귀 직선입니다.

과거 데이터의 전체적인 상승 또는 하락 경향을 보여줍니다.

### ④ 주황색 점은 무엇인가요?

주황색 점은 사용자가 입력한 연도의 예측 평균기온입니다.

빨간색 회귀 직선에서 해당 연도의 위치를 찾아
예측 기온을 계산한 결과입니다.

### ⑤ 결정계수 R²란?

결정계수는 회귀 직선이 실제 데이터의 변화 경향을
얼마나 설명하는지를 나타내는 값입니다.

- 1에 가까울수록 데이터의 경향을 잘 설명합니다.
- 0에 가까울수록 설명력이 낮습니다.

단, 결정계수가 높다고 미래 예측이 반드시 정확한 것은 아닙니다.
""")

# -----------------------------------
# 11. 원본 데이터 확인
# -----------------------------------

with st.expander("📋 선택한 월의 전체 과거 기온 데이터 보기"):

    display_df = monthly_df[
        ["연도", "평균기온(℃)", "회귀예측기온"]
    ].copy()

    display_df.columns = [
        "연도",
        "실제 평균기온(℃)",
        "회귀 예측기온(℃)"
    ]

    st.dataframe(
        display_df,
        use_container_width=True
    )

# -----------------------------------
# 12. 데이터 정보
# -----------------------------------

st.divider()

st.subheader("📊 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("전체 데이터", f"{len(df):,}개")

with col2:
    st.metric(
        "분석 데이터",
        f"{len(monthly_df):,}개"
    )

with col3:
    st.metric(
        "분석 기간",
        f"{monthly_df['연도'].min()}~{monthly_df['연도'].max()}"
    )

st.caption(
    "본 프로그램은 temperature.csv의 평균기온 데이터를 이용하여 "
    "선형회귀 모델을 학습하고 예측합니다."
)
