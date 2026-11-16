
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import calendar

# --------------------------------
# 1. 페이지 설정
# --------------------------------
st.set_page_config(
    page_title="월별 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온 분석")
st.markdown("월을 선택하면 해당 월의 연도별 최고기온과 최저기온을 비교합니다.")

# --------------------------------
# 2. CSV 파일 읽기
# --------------------------------
@st.cache_data
def load_data():

    file_path = Path(__file__).resolve().parent / "temperature.csv"

    if not file_path.exists():
        st.error("temperature.csv 파일을 찾을 수 없습니다.")
        st.stop()

    # 한글 인코딩 처리
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="utf-8-sig")

    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()

    # 날짜 데이터 처리
    # 데이터 형식: Oct-07, Nov-07 ...
    month_map = {
        name: number
        for number, name in enumerate(calendar.month_abbr)
        if name
    }

    years = []
    months = []

    century = 1900
    previous_year = None

    for value in df["일시"].astype(str):

        month_text, year_text = value.split("-")

        yy = int(year_text)

        # 연도가 99에서 00으로 바뀌는 경우 세기 변경
        if previous_year is not None and yy < previous_year:
            century += 100

        full_year = century + yy

        years.append(full_year)
        months.append(month_map[month_text.title()])

        previous_year = yy

    df["연도"] = years
    df["월"] = months

    # 기온 컬럼 숫자 변환
    temp_columns = [
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in temp_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


df = load_data()

# --------------------------------
# 3. 월 선택
# --------------------------------
st.subheader("📅 분석할 월 선택")

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

selected_month = st.selectbox(
    "월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda x: month_names[x - 1],
    index=0
)

# --------------------------------
# 4. 선택한 월의 데이터 추출
# --------------------------------
month_df = df[df["월"] == selected_month].copy()

month_df = month_df.sort_values("연도")

# --------------------------------
# 5. 데이터 확인
# --------------------------------
if month_df.empty:

    st.warning("선택한 월의 데이터가 없습니다.")

else:

    st.subheader(
        f"📊 {selected_month} 연도별 기온 변화"
    )

    # 최고기온과 최저기온 데이터
    chart_df = month_df[
        ["연도", "최고기온(℃)", "최저기온(℃)"]
    ].copy()

    # --------------------------------
    # 6. 꺾은선 그래프 생성
    # --------------------------------
    fig = go.Figure()

    # 최고기온 - 핫핑크
    fig.add_trace(
        go.Scatter(
            x=chart_df["연도"],
            y=chart_df["최고기온(℃)"],
            mode="lines+markers",
            name="최고기온",
            line=dict(
                color="#FF1493",
                width=3
            ),
            marker=dict(
                size=6,
                color="#FF1493"
            ),
            connectgaps=False,
            hovertemplate=(
                "연도: %{x}년<br>"
                "최고기온: %{y}℃"
                "<extra></extra>"
            )
        )
    )

    # 최저기온 - 하늘색
    fig.add_trace(
        go.Scatter(
            x=chart_df["연도"],
            y=chart_df["최저기온(℃)"],
            mode="lines+markers",
            name="최저기온",
            line=dict(
                color="#87CEEB",
                width=3
            ),
            marker=dict(
                size=6,
                color="#87CEEB"
            ),
            connectgaps=False,
            hovertemplate=(
                "연도: %{x}년<br>"
                "최저기온: %{y}℃"
                "<extra></extra>"
            )
        )
    )

    # --------------------------------
    # 7. 그래프 제목 및 축 설정
    # --------------------------------
    fig.update_layout(

        title=dict(
            text="월별 기온 분석",
            x=0.5,
            xanchor="center",
            font=dict(
                size=25,
                family="Malgun Gothic, sans-serif"
            )
        ),

        xaxis=dict(
            title="연도",
            showgrid=True,
            tickformat="d",
            dtick=5,
            tickfont=dict(size=11)
        ),

        yaxis=dict(
            title="온도 (℃)",
            showgrid=True,
            zeroline=True
        ),

        legend=dict(
            title="기온 구분",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),

        height=600,

        hovermode="x unified",

        template="plotly_white",

        font=dict(
            family="Malgun Gothic, AppleGothic, sans-serif",
            size=13
        ),

        margin=dict(
            l=50,
            r=30,
            t=100,
            b=60
        )
    )

    # --------------------------------
    # 8. Streamlit 그래프 출력
    # --------------------------------
    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------
    # 9. 선택 월 데이터 표 출력
    # --------------------------------
    with st.expander("📋 선택한 월의 상세 데이터 보기"):

        display_df = chart_df.rename(
            columns={
                "연도": "연도",
                "최고기온(℃)": "최고기온(℃)",
                "최저기온(℃)": "최저기온(℃)"
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        f"분석 월: {selected_month} | "
        f"데이터 건수: {len(chart_df)}건"
    )
