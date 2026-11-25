
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="서울 강수량 분석",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ 서울시 계절별 강수량 분석")
st.write("서울시 1950~2025년 계절별 강수량 데이터 분석 대시보드")

# ==========================================
# 2. 데이터 불러오기
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "rainfall.csv"

@st.cache_data
def load_data():

    last_error = None

    for encoding in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            data = pd.read_csv(
                FILE_PATH,
                skiprows=7,
                encoding=encoding
            )
            return data
        except UnicodeDecodeError as e:
            last_error = e

    raise ValueError(f"CSV 인코딩 오류: {last_error}")


if not FILE_PATH.exists():
    st.error("rainfall.csv 파일을 찾을 수 없습니다.")
    st.stop()

try:
    df = load_data()

    df = df.iloc[:, :3].copy()
    df.columns = ["년계절", "지점", "강수량"]

    df["년계절"] = df["년계절"].astype(str).str.strip()

    df["연도"] = pd.to_numeric(
        df["년계절"].str.extract(r"(\d{4})")[0],
        errors="coerce"
    )

    df["계절"] = df["년계절"].str.extract(
        r"(봄|여름|가을|겨울)"
    )

    df["강수량"] = pd.to_numeric(
        df["강수량"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["연도", "계절", "강수량"]
    )

    df["연도"] = df["연도"].astype(int)

except Exception as e:
    st.error(f"데이터 처리 오류: {e}")
    st.stop()


# ==========================================
# 3. 계절 색상
# ==========================================
season_order = ["봄", "여름", "가을", "겨울"]

season_colors = {
    "봄": "#FF69B4",
    "여름": "#FFD700",
    "가을": "#A0522D",
    "겨울": "#1E90FF"
}

# ==========================================
# 4. 데이터 기본 정보
# ==========================================
st.subheader("📌 데이터 기본 정보")

c1, c2, c3 = st.columns(3)

c1.metric(
    "시작 연도",
    f"{df['연도'].min()}년"
)

c2.metric(
    "마지막 연도",
    f"{df['연도'].max()}년"
)

c3.metric(
    "전체 자료 수",
    f"{len(df):,}개"
)

st.divider()

# ==========================================
# 5. 연도 선택
# ==========================================
st.subheader("📅 분석할 연도 선택")

years = sorted(df["연도"].unique())

selected_year = st.selectbox(
    "연도를 선택하세요",
    years,
    index=len(years) - 1
)

year_df = df[
    df["연도"] == selected_year
].copy()

# ==========================================
# 6. 선택 연도 계절별 강수량 그래프
# ==========================================
st.subheader(
    f"🌈 {selected_year}년 계절별 강수량"
)

fig1 = px.bar(
    year_df,
    x="계절",
    y="강수량",
    color="계절",
    text="강수량",
    category_orders={
        "계절": season_order
    },
    color_discrete_map=season_colors,
    title=f"{selected_year}년 서울 계절별 강수량"
)

fig1.update_traces(
    texttemplate="%{text:.1f}mm",
    textposition="outside"
)

fig1.update_layout(
    showlegend=False,
    xaxis_title="계절",
    yaxis_title="강수량(mm)",
    height=430
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# ==========================================
# 7. 계절별 평균 강수량
# ==========================================
st.divider()

st.subheader("📊 계절별 평균 강수량")

season_avg = (
    df.groupby("계절")["강수량"]
    .mean()
    .reindex(season_order)
    .dropna()
    .reset_index()
)

fig2 = px.bar(
    season_avg,
    x="계절",
    y="강수량",
    color="계절",
    text="강수량",
    color_discrete_map=season_colors,
    category_orders={
        "계절": season_order
    },
    title="전체 기간 계절별 평균 강수량"
)

fig2.update_traces(
    texttemplate="%{text:.1f}mm",
    textposition="outside"
)

fig2.update_layout(
    showlegend=False,
    xaxis_title="계절",
    yaxis_title="평균 강수량(mm)",
    height=430
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# 평균 강수량 숫자 표시
cols = st.columns(4)

for i, season in enumerate(season_order):

    value = season_avg.loc[
        season_avg["계절"] == season,
        "강수량"
    ]

    if not value.empty:
        cols[i].metric(
            f"{season} 평균",
            f"{value.iloc[0]:,.1f}mm"
        )

# ==========================================
# 8. 계절별 평균 강수량 순위
# ==========================================
st.subheader("🏆 계절별 평균 강수량 순위")

ranking = season_avg.sort_values(
    "강수량",
    ascending=False
).reset_index(drop=True)

ranking.index = ranking.index + 1
ranking.index.name = "순위"

st.dataframe(
    ranking.style.format({
        "강수량": "{:,.1f}mm"
    }),
    use_container_width=True
)

# ==========================================
# 9. 추가 기능 1
# 연도별 총 강수량 TOP 10
# ==========================================
st.divider()

st.subheader("🏆 연도별 총 강수량 TOP 10")

st.write(
    "네 계절의 자료가 모두 존재하는 연도만 합산합니다."
)

# 네 계절이 모두 존재하는 연도만 선택
complete_years = (
    df.groupby("연도")["계절"]
    .nunique()
)

complete_years = complete_years[
    complete_years == 4
].index

annual_df = df[
    df["연도"].isin(complete_years)
]

annual_total = (
    annual_df.groupby("연도")["강수량"]
    .sum()
    .reset_index()
)

top10 = annual_total.nlargest(
    10,
    "강수량"
).sort_values(
    "강수량",
    ascending=True
)

fig3 = px.bar(
    top10,
    x="강수량",
    y="연도",
    orientation="h",
    text="강수량",
    title="계절별 강수량 합계가 가장 많았던 연도 TOP 10",
    labels={
        "연도": "연도",
        "강수량": "연간 총 강수량(mm)"
    }
)

fig3.update_traces(
    marker_color="#FF8C42",
    texttemplate="%{text:.1f}mm",
    textposition="outside"
)

fig3.update_layout(
    height=500
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

st.caption(
    f"비교 가능한 완전한 연도: {len(complete_years)}개"
)

# ==========================================
# 10. 추가 기능 2
# 계절별 장기 강수량 변화 추이
# ==========================================
st.divider()

st.subheader("📈 1950~2025년 계절별 강수량 변화")

st.write(
    "각 계절의 강수량이 장기간 어떻게 변화했는지 비교합니다."
)

trend_df = df.copy()

fig4 = px.line(
    trend_df,
    x="연도",
    y="강수량",
    color="계절",
    markers=True,
    category_orders={
        "계절": season_order
    },
    color_discrete_map=season_colors,
    title="연도별 계절 강수량 변화 추이"
)

fig4.update_layout(
    xaxis_title="연도",
    yaxis_title="강수량(mm)",
    height=550,
    hovermode="x unified",
    legend_title="계절"
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

# ==========================================
# 11. 분석 마무리
# ==========================================
st.divider()

st.subheader("🔍 분석 결과 요약")

wettest_season = season_avg.loc[
    season_avg["강수량"].idxmax()
]

driest_season = season_avg.loc[
    season_avg["강수량"].idxmin()
]

wettest_year = annual_total.loc[
    annual_total["강수량"].idxmax()
]

a, b = st.columns(2)

a.metric(
    "평균 강수량이 가장 많은 계절",
    wettest_season["계절"],
    f"{wettest_season['강수량']:.1f}mm"
)

b.metric(
    "평균 강수량이 가장 적은 계절",
    driest_season["계절"],
    f"{driest_season['강수량']:.1f}mm"
)

st.success(
    f"완전한 계절 자료 기준으로 강수량 합계가 가장 많았던 연도는 "
    f"{int(wettest_year['연도'])}년이며, "
    f"총 {wettest_year['강수량']:,.1f}mm입니다."
)

st.caption(
    "자료: 첨부된 서울 지점 계절별 강수량 CSV"
)

