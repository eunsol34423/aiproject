import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="국가별 MBTI 분포",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 국가별 MBTI 분포 분석")
st.write("국가를 선택하면 해당 국가의 MBTI 16개 유형 비율을 높은 순서대로 보여줍니다.")

MBTI_TYPES = [
    "INFJ", "ISFJ", "INTP", "ISFP",
    "ENTP", "INFP", "ENTJ", "ISTP",
    "INTJ", "ESFP", "ESTJ", "ENFP",
    "ESTP", "ISTJ", "ENFJ", "ESFJ"
]

# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.strip()

    required_columns = ["Country"] + MBTI_TYPES
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        raise ValueError(f"CSV에 필요한 컬럼이 없습니다: {', '.join(missing)}")

    data["Country"] = data["Country"].astype(str).str.strip()

    for column in MBTI_TYPES:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    if data[required_columns].isna().any().any():
        raise ValueError("국가명 또는 MBTI 비율에 빈 값이나 숫자가 아닌 값이 있습니다.")

    if (data[MBTI_TYPES] < 0).any().any():
        raise ValueError("MBTI 비율에 음수가 포함되어 있습니다.")

    if data["Country"].duplicated().any():
        raise ValueError("국가명이 중복되어 있습니다. CSV를 확인해 주세요.")

    return data


default_file = Path(__file__).parent / "countriesMBTI_16types.csv"
uploaded_file = st.sidebar.file_uploader(
    "다른 MBTI CSV 파일 사용하기",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()

        required_columns = ["Country"] + MBTI_TYPES
        missing = [column for column in required_columns if column not in df.columns]
        if missing:
            st.error(f"CSV에 필요한 컬럼이 없습니다: {', '.join(missing)}")
            st.stop()

        df["Country"] = df["Country"].astype(str).str.strip()
        for column in MBTI_TYPES:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        if df[required_columns].isna().any().any():
            st.error("업로드한 파일에 빈 값 또는 숫자가 아닌 값이 있습니다.")
            st.stop()
        if (df[MBTI_TYPES] < 0).any().any():
            st.error("업로드한 파일에 음수 비율이 있습니다.")
            st.stop()
        if df["Country"].duplicated().any():
            st.error("업로드한 파일에 중복 국가명이 있습니다.")
            st.stop()
    else:
        if not default_file.exists():
            st.error("countriesMBTI_16types.csv 파일을 app.py와 같은 폴더에 넣어주세요.")
            st.stop()
        df = load_data(str(default_file))

except Exception as error:
    st.error(f"데이터를 읽는 중 문제가 발생했습니다: {error}")
    st.stop()

# --------------------------------------------------
# 국가 선택
# --------------------------------------------------
countries = sorted(df["Country"].dropna().unique().tolist())

selected_country = st.selectbox(
    "국가 선택",
    countries,
    index=countries.index("South Korea") if "South Korea" in countries else 0
)

country_row = df.loc[df["Country"] == selected_country].iloc[0]

# 원본 데이터는 0~1 비율이므로 퍼센트로 변환
chart_data = pd.DataFrame({
    "MBTI": MBTI_TYPES,
    "비율(%)": [float(country_row[mbti]) * 100 for mbti in MBTI_TYPES]
})

# 높은 비율이 왼쪽/위쪽에 오도록 내림차순 정렬
chart_data = chart_data.sort_values(
    "비율(%)",
    ascending=False
).reset_index(drop=True)

# 1위는 빨간색, 2위부터는 진한 핑크에서 연한 핑크로
pink_palette = [
    "#F06292", "#F27FA5", "#F48FB1", "#F5A2BE",
    "#F6B2CA", "#F7BED2", "#F8C9DA", "#F9D2E0",
    "#F9D9E5", "#FAE0E9", "#FAE6ED", "#FBEAF0",
    "#FCEEF3", "#FCF1F5", "#FDF5F7"
]
bar_colors = ["#E53935"] + pink_palette[:len(chart_data) - 1]

# --------------------------------------------------
# 결과 표시
# --------------------------------------------------
top_mbti = chart_data.iloc[0]

col1, col2, col3 = st.columns(3)
col1.metric("선택 국가", selected_country)
col2.metric("가장 높은 유형", top_mbti["MBTI"])
col3.metric("1위 비율", f'{top_mbti["비율(%)"]:.2f}%')

st.subheader(f"📊 {selected_country}의 MBTI 유형별 비율")

fig = go.Figure(
    data=[
        go.Bar(
            x=chart_data["MBTI"],
            y=chart_data["비율(%)"],
            marker=dict(color=bar_colors),
            text=[f"{value:.2f}%" for value in chart_data["비율(%)"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>비율: %{y:.2f}%<extra></extra>"
        )
    ]
)

fig.update_layout(
    xaxis_title="MBTI 유형",
    yaxis_title="비율(%)",
    yaxis=dict(rangemode="tozero"),
    showlegend=False,
    height=560,
    margin=dict(t=35, b=35, l=20, r=20)
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "색상 기준: 1위는 빨간색, 2위부터는 진한 핑크에서 연한 핑크 순서입니다. "
    "비율은 CSV 원본 값에 100을 곱해 백분율(%)로 표시합니다."
)

with st.expander("선택한 국가의 상세 비율 보기"):
    display_data = chart_data.copy()
    display_data["비율(%)"] = display_data["비율(%)"].map(lambda x: f"{x:.2f}%")
    st.dataframe(display_data, use_container_width=True, hide_index=True)

# 원본 데이터 다운로드
download_df = df.copy()
download_df[MBTI_TYPES] = download_df[MBTI_TYPES] * 100
st.download_button(
    label="📥 전체 국가 데이터 다운로드 (CSV)",
    data=download_df.to_csv(index=False).encode("utf-8-sig"),
    file_name="countries_mbti_percent.csv",
    mime="text/csv"
)

st.sidebar.markdown("---")
st.sidebar.caption(f"데이터 국가 수: {len(df)}개")
st.sidebar.caption("Streamlit Cloud 배포용")
