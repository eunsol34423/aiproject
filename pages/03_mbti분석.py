
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="국가별 MBTI 분포",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 국가별 MBTI 분포 분석")
st.write(
    "국가를 선택하면 해당 국가의 MBTI 16개 유형별 비율을 "
    "높은 순서대로 막대그래프로 보여줍니다."
)

MBTI_TYPES = [
    "INFJ", "ISFJ", "INTP", "ISFP",
    "ENTP", "INFP", "ENTJ", "ISTP",
    "INTJ", "ESFP", "ESTJ", "ENFP",
    "ESTP", "ISTJ", "ENFJ", "ESFJ"
]

# --------------------------------------------------
# 2. CSV 파일 경로 설정
# --------------------------------------------------
# 현재 PY 파일은 pages 폴더에 있고
# CSV 파일은 상위 폴더에 있음

BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "countriesMBTI_16types.csv"

# --------------------------------------------------
# 3. 데이터 불러오기
# --------------------------------------------------
@st.cache_data
def load_data(file_path):

    data = pd.read_csv(file_path)

    data.columns = data.columns.str.strip()

    required_columns = ["Country"] + MBTI_TYPES

    missing = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"CSV에 필요한 컬럼이 없습니다: {missing}"
        )

    data["Country"] = (
        data["Country"].astype(str).str.strip()
    )

    for col in MBTI_TYPES:
        data[col] = pd.to_numeric(
            data[col], errors="coerce"
        )

    if data[required_columns].isna().any().any():
        raise ValueError(
            "CSV에 빈 값 또는 숫자가 아닌 값이 있습니다."
        )

    if (data[MBTI_TYPES] < 0).any().any():
        raise ValueError(
            "MBTI 비율에 음수가 포함되어 있습니다."
        )

    if data["Country"].duplicated().any():
        raise ValueError(
            "중복 국가명이 있습니다."
        )

    return data


# --------------------------------------------------
# 4. 데이터 로딩
# --------------------------------------------------
if not CSV_PATH.exists():

    st.error(
        f"CSV 파일을 찾을 수 없습니다.\n\n"
        f"확인 경로: {CSV_PATH}"
    )

    st.stop()

try:

    df = load_data(str(CSV_PATH))

except Exception as e:

    st.error(f"데이터 로딩 오류: {e}")

    st.stop()


# --------------------------------------------------
# 5. 국가 선택
# --------------------------------------------------
st.sidebar.header("🌍 국가 선택")

countries = sorted(
    df["Country"].unique().tolist()
)

default_index = (
    countries.index("South Korea")
    if "South Korea" in countries
    else 0
)

selected_country = st.sidebar.selectbox(
    "분석할 국가를 선택하세요.",
    countries,
    index=default_index
)

# --------------------------------------------------
# 6. 선택 국가 데이터 추출
# --------------------------------------------------
country_data = df[
    df["Country"] == selected_country
].iloc[0]

chart_data = pd.DataFrame({

    "MBTI": MBTI_TYPES,

    "비율(%)": [
        float(country_data[t]) * 100
        for t in MBTI_TYPES
    ]

})

# 높은 비율부터 정렬
chart_data = chart_data.sort_values(
    "비율(%)",
    ascending=False
).reset_index(drop=True)


# --------------------------------------------------
# 7. 그래프 색상 설정
# --------------------------------------------------
# 1위: 빨간색
# 2위~16위: 핑크색에서 연한 핑크색으로

pink_palette = [
    "#F06292",
    "#F27FA5",
    "#F48FB1",
    "#F5A2BE",
    "#F6B2CA",
    "#F7BED2",
    "#F8C9DA",
    "#F9D2E0",
    "#F9D9E5",
    "#FAE0E9",
    "#FAE6ED",
    "#FBEAF0",
    "#FCEEF3",
    "#FCF1F5",
    "#FDF5F7"
]

bar_colors = (
    ["#E53935"]
    + pink_palette[:len(chart_data) - 1]
)


# --------------------------------------------------
# 8. 주요 결과 표시
# --------------------------------------------------
top_mbti = chart_data.iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric(
    "선택 국가",
    selected_country
)

col2.metric(
    "가장 높은 MBTI",
    top_mbti["MBTI"]
)

col3.metric(
    "1위 비율",
    f'{top_mbti["비율(%)"]:.2f}%'
)


# --------------------------------------------------
# 9. MBTI 막대그래프
# --------------------------------------------------
st.subheader(
    f"📊 {selected_country} MBTI 유형별 비율"
)

fig = go.Figure()

fig.add_trace(

    go.Bar(

        x=chart_data["MBTI"],

        y=chart_data["비율(%)"],

        marker=dict(
            color=bar_colors
        ),

        text=[
            f"{v:.2f}%"
            for v in chart_data["비율(%)"]
        ],

        textposition="outside",

        hovertemplate=(
            "<b>%{x}</b><br>"
            "비율: %{y:.2f}%"
            "<extra></extra>"
        )

    )

)

fig.update_layout(

    title=f"{selected_country} MBTI Distribution",

    xaxis_title="MBTI 유형",

    yaxis_title="비율 (%)",

    yaxis=dict(
        rangemode="tozero"
    ),

    showlegend=False,

    height=560,

    plot_bgcolor="white",

    paper_bgcolor="white",

    font=dict(
        family="Arial",
        size=13
    ),

    margin=dict(
        t=50,
        b=40,
        l=30,
        r=30
    )

)

st.plotly_chart(
    fig,
    use_container_width=True
)


# --------------------------------------------------
# 10. 색상 안내
# --------------------------------------------------
st.markdown(
    """
    🔴 **1위:** 빨간색

    🌸 **2위~16위:** 진한 핑크에서 연한 핑크 순서
    """
)


# --------------------------------------------------
# 11. 상세 데이터
# --------------------------------------------------
with
