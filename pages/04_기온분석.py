
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import calendar

# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="월별 기온 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 월별 기온 분석")
st.markdown(
    "월을 선택하여 연도별 최고기온과 최저기온을 비교해 보세요."
)

# ==========================================
# 2. CSV 파일 불러오기
# ==========================================
@st.cache_data
def load_data():

    # pages 폴더의 상위 폴더 경로
    base_dir = Path(__file__).resolve().parent.parent

    # 상위 폴더의 CSV 파일 경로
    file_path = base_dir / "temperature.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"CSV 파일을 찾을 수 없습니다: {file_path}"
        )

    # 한글 인코딩 자동 대응
    encodings = ["cp949", "utf-8-sig", "utf-8"]

    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding
            )
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        raise ValueError("CSV 파일의 인코딩을 확인해주세요.")

    # 컬럼명 공백 제거
    df.columns = df.columns.str.strip()

    # 필수 컬럼 확인
    required_columns = [
        "일시",
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV에 필요한 컬럼이 없습니다: {missing_columns}"
        )

    # ======================================
    # 3. 날짜 데이터 변환
    # ======================================

    month_map = {
        name: number
        for number, name in enumerate(
            calendar.month_abbr
        )
        if name
    }

    years = []
    months = []

    century = 1900
    previous_year = None

    for value in df["일시"].astype(str):

        month_text, year_text = value.strip().split("-")

        yy = int(year_text)

        # 99년에서 00년으로 넘어갈 때 세기 변경
        if (
            previous_year is not None
            and yy < previous_year
        ):
            century += 100

        full_year = century + yy

        years.append(full_year)
        months.append(
            month_map[month_text.title()]
        )

        previous_year = yy

    df["연도"] = years
    df["월"] = months

    # ======================================
    # 4. 기온 데이터 숫자 변환
    # ======================================

    temperature_columns = [
        "최고기온(℃)",
        "최저기온(℃)"
    ]

    for col in temperature_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


# ==========================================
# 5. 데이터 불러오기 및 오류 처리
# ==========================================
try:
    df = load_data()

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# ==========================================
# 6. 월 선택
# ==========================================
st.subheader("📅 분석할 월 선택")

month_names = [
    "1월", "2월", "3월", "4월",
    "5월", "6월", "7월", "8월",
    "9월", "10월", "11월", "12월"
]

selected_month = st.selectbox(
    "분석하고 싶은 월을 선택하세요.",
    options=list(range(1, 13)),
    format_func=lambda x: month_names[x - 1],
    index=0
)


# ==========================================
# 7. 선택한 월의 데이터 추출
# ==========================================
month_df = df[
    df["월"] == selected_month
].copy()

month_df = month_df.sort_values("연도")

chart_df = month_df[
    ["연도", "최고기온(℃)", "최저기온(℃)"]
].dropna(
    subset=["연도"]
)


# ==========================================
# 8. 그래프 작성
# ==========================================
if chart_df.empty:

    st.warning("선택한 월의 데이터가 없습니다.")

else:

    st.subheader(
        f"📊 {selected_month} 연도별 기온 변화"
    )

    fig = go.Figure()

    # --------------------------------------
    # 최고기온: 핫핑크
    # --------------------------------------
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
                color="#FF1493",
                size=6
            ),
            connectgaps=False,
            hovertemplate=(
                "%{x}년<br>"
                "최고기온: %{y}℃"
                "<extra></extra>"
            )
        )
    )

    # --------------------------------------
    # 최저기온: 하늘색
    # --------------------------------------
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
                color="#87CEEB",
                size=6
            ),
            connectgaps=False,
            hovertemplate=(
                "%{x}년<br>"
                "최저기온: %{y}℃"
                "<extra></extra>"
            )
        )
    )

    # --------------------------------------
    # 그래프 제목 및 축 설정
    # --------------------------------------
    fig.update_layout(

        title=dict(
            text="월별 기온 분석",
            x=0.5,
            xanchor="center",
            font=dict(size=25)
        ),

        xaxis=dict(
            title="연도",
            showgrid=True,
            dtick=5,
            tickformat="d"
        ),

        yaxis=dict(
            title="온도 (℃)",
            showgrid=True,
            zeroline=True
        ),

        # 범례 표시
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

        # 한글 폰트 설정
        font=dict(
            family=(
                "Malgun Gothic, "
                "Apple SD Gothic Neo, "
                "Noto Sans KR, sans-serif"
            ),
            size=13
        ),

        margin=dict(
            l=60,
            r=30,
            t=100,
            b=60
        )
    )

    # --------------------------------------
    # 그래프 출력
    # --------------------------------------
    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ======================================
    # 9. 기온 데이터 확인
    # ======================================
    st.subheader("📋 선택한 월의 기온 데이터")

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

    # ======================================
    # 10. 데이터 요약
    # ======================================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "분석 월",
            f"{selected_month}월"
        )

    with col2:
        st.metric(
            "최고기온",
            f"{chart_df['최고기온(℃)'].max():.1f}℃"
        )

    with col3:
        st.metric(
            "최저기온",
            f"{chart_df['최저기온(℃)'].min():.1f}℃"
        )

    st.caption(
        f"분석 데이터: {len(chart_df)}건"
    )
