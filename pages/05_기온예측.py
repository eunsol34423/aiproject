
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="기온 예측 AI 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 평균기온 AI 예측 프로그램")

st.markdown("""
과거 기온 데이터를 활용하여 3가지 머신러닝 회귀 알고리즘을 학습하고
미래의 평균기온을 예측합니다.
""")

st.divider()


# ==========================================
# 2. CSV 파일 불러오기
# ==========================================

# 현재 파이썬 파일은 pages 폴더에 있음
# temperature.csv는 상위 폴더에 있음

file_path = (
    Path(__file__).resolve().parent.parent
    / "temperature.csv"
)

if not file_path.exists():
    st.error(
        "temperature.csv 파일을 찾을 수 없습니다. "
        "프로젝트 최상위 폴더에 파일을 넣어주세요."
    )
    st.stop()


try:
    df = pd.read_csv(file_path, encoding="cp949")
except UnicodeDecodeError:
    df = pd.read_csv(file_path, encoding="utf-8-sig")


# ==========================================
# 3. 데이터 전처리
# ==========================================

required_columns = ["일시", "평균기온(℃)"]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해주세요.")
    st.write(df.columns.tolist())
    st.stop()


month_dict = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12
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

    if len(year_text) == 2:
        year += 2000

    return pd.Timestamp(
        year=year,
        month=month,
        day=1
    )


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
    st.error("분석할 데이터가 없습니다.")
    st.stop()


# ==========================================
# 4. 사용자 입력
# ==========================================

st.subheader("📌 분석 조건 선택")

col1, col2 = st.columns(2)

with col1:

    selected_month = st.selectbox(
        "분석할 월",
        list(range(1, 13)),
        format_func=lambda x: f"{x}월"
    )

with col2:

    selected_year = st.number_input(
        "예측할 연도",
        min_value=1900,
        max_value=2100,
        value=2030,
        step=1
    )

selected_year = int(selected_year)


# ==========================================
# 5. 알고리즘 선택
# ==========================================

st.subheader("🤖 회귀 알고리즘 선택")

algorithm_names = [
    "선형회귀",
    "다항회귀",
    "랜덤 포레스트 회귀"
]

selected_algorithm = st.selectbox(
    "사용할 예측 알고리즘을 선택하세요",
    algorithm_names
)

st.caption(
    "아래 비교 그래프에서는 세 알고리즘의 결과를 "
    "모두 확인할 수 있습니다."
)


# ==========================================
# 6. 선택한 월 데이터 추출
# ==========================================

monthly_df = df[
    df["월"] == selected_month
].copy()

monthly_df = monthly_df.sort_values("연도")

monthly_df = (
    monthly_df.groupby("연도", as_index=False)
    ["평균기온(℃)"].mean()
)

if len(monthly_df) < 4:
    st.error(
        "회귀 알고리즘을 비교하려면 "
        "선택한 월의 데이터가 최소 4개 필요합니다."
    )
    st.stop()


# 연도 데이터를 상대적인 숫자로 변환
# 예: 2007년은 0, 2008년은 1

base_year = int(monthly_df["연도"].min())

X = (
    monthly_df[["연도"]].values.astype(float)
    - base_year
)

y = monthly_df["평균기온(℃)"].values


# 예측 연도도 동일한 기준 사용
future_X = np.array([
    [selected_year - base_year]
], dtype=float)


# ==========================================
# 7. 세 가지 알고리즘 정의
# ==========================================

def create_models():

    models = {

        "선형회귀": LinearRegression(),

        "다항회귀": make_pipeline(
            PolynomialFeatures(
                degree=2,
                include_bias=False
            ),
            LinearRegression()
        ),

        "랜덤 포레스트 회귀": RandomForestRegressor(
            n_estimators=300,
            max_depth=3,
            min_samples_leaf=2,
            random_state=42
        )

    }

    return models


models = create_models()


# ==========================================
# 8. 세 가지 알고리즘 학습
# ==========================================

predictions = {}
historical_predictions = {}
validation_results = {}

# 미래 예측 및 과거 데이터 학습 결과

for name, model in models.items():

    model.fit(X, y)

    # 미래 기온 예측
    future_prediction = model.predict(
        future_X
    )[0]

    predictions[name] = future_prediction

    # 과거 데이터의 학습 결과
    historical_predictions[name] = (
        model.predict(X)
    )


# ==========================================
# 9. 시간 순서에 따른 성능 검증
# ==========================================

# 과거 데이터 일부로 학습하고
# 이후 연도의 데이터로 검증

split_index = max(
    2,
    int(len(X) * 0.8)
)

if split_index >= len(X):
    split_index = len(X) - 1

X_train = X[:split_index]
y_train = y[:split_index]

X_test = X[split_index:]
y_test = y[split_index:]


validation_models = create_models()

for name, model in validation_models.items():

    model.fit(X_train, y_train)

    test_prediction = model.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        test_prediction
    )

    r2 = r2_score(
        y_test,
        test_prediction
    )

    validation_results[name] = {
        "MAE": mae,
        "R2": r2
    }


# ==========================================
# 10. 선택한 알고리즘 결과
# ==========================================

selected_prediction = predictions[
    selected_algorithm
]

st.divider()

st.subheader(
    f"🌡️ {selected_month}월 예측 결과"
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "예측 연도",
        f"{selected_year}년"
    )

with col2:

    st.metric(
        "선택한 알고리즘",
        selected_algorithm
    )

with col3:

    st.metric(
        "예측 평균기온",
        f"{selected_prediction:.2f} ℃"
    )


last_year = int(monthly_df["연도"].max())

if selected_year > last_year:

    st.info(
        f"마지막 관측 연도는 {last_year}년입니다. "
        "그 이후의 기온을 예측하고 있습니다."
    )

elif selected_year < base_year:

    st.warning(
        "입력한 연도가 과거 데이터 범위보다 이전입니다. "
        "외삽 결과이므로 주의해서 해석하세요."
    )


# ==========================================
# 11. 세 알고리즘 한눈에 비교
# ==========================================

st.divider()

st.subheader("📊 세 가지 알고리즘 예측 결과 비교")

comparison_df = pd.DataFrame({
    "알고리즘": algorithm_names,
    "예측 평균기온(℃)": [
        predictions[name]
        for name in algorithm_names
    ],
    "검증 MAE(℃)": [
        validation_results[name]["MAE"]
        for name in algorithm_names
    ],
    "검증 R²": [
        validation_results[name]["R2"]
        for name in algorithm_names
    ]
})

comparison_df["예측 평균기온(℃)"] = (
    comparison_df["예측 평균기온(℃)"].round(2)
)

comparison_df["검증 MAE(℃)"] = (
    comparison_df["검증 MAE(℃)"].round(3)
)

comparison_df["검증 R²"] = (
    comparison_df["검증 R²"].round(3)
)

st.dataframe(
    comparison_df,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "MAE는 낮을수록 검증 오차가 작습니다. "
    "R²는 높을수록 검증 데이터의 변화 설명력이 높습니다. "
    "검증 데이터는 시간 순서에 따라 과거 학습 자료의 뒤쪽 20%를 사용합니다."
)


# ==========================================
# 12. 세 알고리즘 통합 그래프
# ==========================================

st.divider()

st.subheader(
    f"📈 {selected_month}월 세 가지 회귀 알고리즘 비교 그래프"
)

start_year = min(
    base_year,
    selected_year
)

end_year = max(
    last_year,
    selected_year
)

line_years = np.arange(
    start_year,
    end_year + 1
)

line_X = (
    line_years.reshape(-1, 1) - base_year
).astype(float)


fig, ax = plt.subplots(figsize=(14, 7))


# 실제 평균기온
ax.scatter(
    monthly_df["연도"],
    monthly_df["평균기온(℃)"],
    color="black",
    s=65,
    label="실제 평균기온",
    zorder=5
)

# 알고리즘별 색상
colors = {
    "선형회귀": "red",
    "다항회귀": "green",
    "랜덤 포레스트 회귀": "purple"
}

styles = {
    "선형회귀": "-",
    "다항회귀": "--",
    "랜덤 포레스트 회귀": "-."
}


# 세 가지 알고리즘의 회귀선
for name, model in models.items():

    line_prediction = model.predict(line_X)

    ax.plot(
        line_years,
        line_prediction,
        color=colors[name],
        linestyle=styles[name],
        linewidth=2.5,
        label=f"{name} 추세선"
    )

    # 예측 지점
    ax.scatter(
        [selected_year],
        [predictions[name]],
        color=colors[name],
        s=120,
        marker="D",
        edgecolors="black",
        zorder=6,
        label=f"{name} 예측값"
    )


# 선택한 알고리즘 예측값 강조
ax.scatter(
    [selected_year],
    [selected_prediction],
    s=300,
    facecolors="none",
    edgecolors="orange",
    linewidths=3,
    zorder=8
)

ax.axvline(
    selected_year,
    color="gray",
    linestyle=":",
    alpha=0.7,
    label="예측 연도"
)

ax.set_title(
    f"{selected_month}월 평균기온 - 3가지 알고리즘 비교",
    fontsize=16
)

ax.set_xlabel("연도", fontsize=12)
ax.set_ylabel("평균기온(℃)", fontsize=12)

ax.grid(
    True,
    alpha=0.3
)

ax.legend(
    loc="best",
    fontsize=9
)

fig.tight_layout()

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(fig)


# ==========================================
# 13. 선택 알고리즘별 상세 결과
# ==========================================

st.divider()

st.subheader("🔍 선택한 알고리즘 상세 분석")

selected_model = models[selected_algorithm]

st.write(
    f"**선택한 알고리즘: {selected_algorithm}**"
)

st.metric(
    "검증 평균절대오차(MAE)",
    f"{validation_results[selected_algorithm]['MAE']:.3f} ℃"
)

st.metric(
    "검증 결정계수(R²)",
    f"{validation_results[selected_algorithm]['R2']:.3f}"
)


# 알고리즘별 설명
explanations = {

    "선형회귀": """
    ### 선형회귀

    - 과거 연도와 평균기온의 관계를 직선으로 표현합니다.
    - 데이터 전체의 오차가 작아지는 직선을 찾습니다.
    - 빨간색 실선이 직선 형태의 예측 추세입니다.
    - 장기적인 상승 또는 하락 경향을 파악하는 데 유용합니다.
    """,

    "다항회귀": """
    ### 다항회귀

    - 선형회귀를 확장한 알고리즘입니다.
    - 연도와 기온 사이의 관계를 곡선으로 표현합니다.
    - 과거 기온 변화가 직선 형태가 아닐 때 유용합니다.
    - 이번 프로그램에서는 2차 다항식을 사용합니다.
    - 초록색 점선이 곡선 형태의 예측 추세입니다.
    """,

    "랜덤 포레스트 회귀": """
    ### 랜덤 포레스트 회귀

    - 여러 개의 의사결정나무를 만들어 결과를 결합합니다.
    - 각 나무의 예측값을 평균하여 최종 결과를 만듭니다.
    - 복잡하고 비선형적인 데이터 관계를 학습할 수 있습니다.
    - 보라색 점선이 랜덤 포레스트의 예측 추세입니다.
    - 학습 범위 밖의 미래 연도에서는 새로운 추세를
      만들어 외삽하지 못하는 특징이 있습니다.
    """
}

st.markdown(
    explanations[selected_algorithm]
)


# ==========================================
# 14. 알고리즘 세 가지 작동 원리
# ==========================================

st.divider()

st.subheader("📚 세 가지 회귀 알고리즘 쉽게 이해하기")

with st.expander("① 선형회귀 작동 원리"):

    st.markdown("""
    과거 기온 데이터의 점들을 가장 잘 설명하는
    직선을 찾는 방법입니다.

    예를 들어 시간이 지날수록 기온이 상승하는
    경향이 있다면 상승하는 직선을 만들어냅니다.

    **핵심:** 직선으로 미래 기온을 예측합니다.
    """)

with st.expander("② 다항회귀 작동 원리"):

    st.markdown("""
    선형회귀처럼 직선만 사용하는 것이 아니라
    곡선을 이용하여 데이터의 변화를 분석합니다.

    기온이 일정하게 상승하거나 하락하지 않고
    곡선 형태의 변화가 있을 때 활용할 수 있습니다.

    **핵심:** 곡선으로 미래 기온을 예측합니다.
    """)

with st.expander("③ 랜덤 포레스트 회귀 작동 원리"):

    st.markdown("""
    여러 개의 의사결정나무가 각각 예측한 결과를
    모아서 평균을 계산합니다.

    하나의 나무에만 의존하지 않고 여러 나무의
    결과를 결합한다는 특징이 있습니다.

    **핵심:** 여러 나무의 예측 결과를 결합합니다.

    주의할 점은 과거 데이터의 범위를 벗어난 미래 연도에서는
    새로운 기온 상승 또는 하락 추세를 예측하기 어렵다는 것입니다.
    """)


# ==========================================
# 15. 실제 데이터와 예측 데이터 확인
# ==========================================

st.divider()

st.subheader("📋 월별 실제 기온 및 알고리즘 예측 데이터")

result_df = monthly_df[
    ["연도", "평균기온(℃)"]
].copy()

result_df.columns = [
    "연도",
    "실제 평균기온(℃)"
]

for name in algorithm_names:

    result_df[name + " 예측"] = np.round(
        historical_predictions[name],
        2
    )

st.dataframe(
    result_df,
    use_container_width=True,
    hide_index=True
)


# ==========================================
# 16. 최종 데이터 정보
# ==========================================

st.divider()

st.subheader("📊 분석 데이터 정보")

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "전체 데이터",
        f"{len(df):,}개"
    )

with col2:

    st.metric(
        "선택 월 데이터",
        f"{len(monthly_df):,}개"
    )

with col3:

    st.metric(
        "분석 기간",
        f"{base_year}~{last_year}"
    )


st.caption(
    "본 프로그램은 temperature.csv의 평균기온 자료를 이용하며 "
    "세 가지 머신러닝 회귀 알고리즘을 비교합니다. "
    "모델의 예측값은 실제 기상예보와 다를 수 있습니다."
)



