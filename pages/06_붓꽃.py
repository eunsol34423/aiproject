
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pathlib import Path
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# --------------------------------
# 1. 페이지 설정
# --------------------------------

st.set_page_config(
    page_title="붓꽃 품종 예측",
    page_icon="🌸",
    layout="wide"
)

st.title("🌸 붓꽃 품종 예측 프로그램")
st.write(
    "꽃잎의 길이와 너비를 입력하면 "
    "머신러닝 알고리즘으로 붓꽃 품종을 예측합니다."
)

# --------------------------------
# 2. CSV 파일 불러오기
# --------------------------------

@st.cache_data
def load_data():

    # 현재 파일은 pages 폴더,
    # CSV 파일은 상위 폴더에 위치
    csv_path = (
        Path(__file__).resolve().parent.parent
        / "Iris.csv"
    )

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Iris.csv 파일을 찾을 수 없습니다: {csv_path}"
        )

    # 한글 인코딩 대응
    try:
        data = pd.read_csv(csv_path, encoding="cp949")
    except UnicodeDecodeError:
        data = pd.read_csv(csv_path, encoding="utf-8-sig")

    return data


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일 오류: {e}")
    st.stop()


# 필요한 열 확인
required_columns = [
    "꽃잎 길이",
    "꽃잎 너비",
    "품종"
]

if not all(col in df.columns for col in required_columns):
    st.error("CSV 파일의 열 이름을 확인해주세요.")
    st.stop()

# 분석에 필요한 데이터만 사용
df = df[required_columns].dropna()

# --------------------------------
# 3. 입력 데이터 범위 확인
# --------------------------------

length_min = float(df["꽃잎 길이"].min())
length_max = float(df["꽃잎 길이"].max())

width_min = float(df["꽃잎 너비"].min())
width_max = float(df["꽃잎 너비"].max())

st.subheader("📌 꽃잎 입력 가능 범위")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "꽃잎 길이",
        f"{length_min} ~ {length_max}"
    )

with col2:
    st.metric(
        "꽃잎 너비",
        f"{width_min} ~ {width_max}"
    )

st.info(
    "입력 범위는 첨부한 Iris.csv의 "
    "실제 최솟값과 최댓값을 기준으로 합니다."
)

# --------------------------------
# 4. KNN 머신러닝 모델 생성
# --------------------------------

X = df[["꽃잎 길이", "꽃잎 너비"]]
y = df["품종"]

# 표준화 + KNN 분류기
model = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5))
])

# 전체 데이터로 학습
model.fit(X, y)

# --------------------------------
# 5. 사용자 입력
# --------------------------------

st.subheader("🌱 예측할 붓꽃 정보 입력")

input_col1, input_col2 = st.columns(2)

with input_col1:
    petal_length = st.number_input(
        "꽃잎 길이",
        min_value=length_min,
        max_value=length_max,
        value=5.0,
        step=0.1
    )

with input_col2:
    petal_width = st.number_input(
        "꽃잎 너비",
        min_value=width_min,
        max_value=width_max,
        value=1.5,
        step=0.1
    )

# --------------------------------
# 6. 품종 예측
# --------------------------------

if st.button("🔍 붓꽃 품종 예측하기", type="primary"):

    user_data = pd.DataFrame({
        "꽃잎 길이": [petal_length],
        "꽃잎 너비": [petal_width]
    })

    prediction = model.predict(user_data)[0]

    probabilities = model.predict_proba(user_data)[0]
    classes = model.named_steps["knn"].classes_

    st.success(f"예측된 붓꽃 품종: {prediction}")

    st.subheader("품종 예측 결과")

    result_df = pd.DataFrame({
        "품종": classes,
        "예측 비율": probabilities * 100
    })

    result_df["예측 비율"] = (
        result_df["예측 비율"].round(1)
    )

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "예측 비율은 가장 가까운 5개 데이터 중 "
        "각 품종이 차지하는 비율입니다."
    )

    # --------------------------------
    # 7. 산점도 그래프
    # --------------------------------

    st.subheader("📊 붓꽃 품종 분포 및 입력 위치")

    fig = go.Figure()

    # 품종별 기존 데이터 표시
    colors = {
        "Iris-setosa": "blue",
        "Iris-versicolor": "green",
        "Iris-virginica": "red"
    }

    for species in sorted(df["품종"].unique()):

        species_df = df[df["품종"] == species]

        fig.add_trace(
            go.Scatter(
                x=species_df["꽃잎 길이"],
                y=species_df["꽃잎 너비"],
                mode="markers",
                name=species,
                marker=dict(
                    size=9,
                    color=colors.get(species, "gray"),
                    opacity=0.65
                )
            )
        )

    # 사용자가 입력한 위치를 노란색 별로 표시
    fig.add_trace(
        go.Scatter(
            x=[petal_length],
            y=[petal_width],
            mode="markers",
            name="사용자 입력값",
            marker=dict(
                symbol="star",
                size=24,
                color="yellow",
                line=dict(
                    color="black",
                    width=2
                )
            )
        )
    )

    fig.update_layout(
        title="꽃잎 길이와 꽃잎 너비에 따른 붓꽃 분포",
        xaxis_title="꽃잎 길이",
        yaxis_title="꽃잎 너비",
        template="plotly_white",
        height=600,
        legend_title="붓꽃 품종"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------
    # 8. 입력값 설명
    # --------------------------------

    st.subheader("📝 입력 데이터")

    st.write(f"꽃잎 길이: {petal_length}")
    st.write(f"꽃잎 너비: {petal_width}")
    st.write(f"예측 품종: {prediction}")

# --------------------------------
# 9. 알고리즘 설명
# --------------------------------

st.divider()

st.subheader("🤖 사용한 머신러닝 알고리즘")

st.markdown("""
### KNN (K-최근접 이웃 알고리즘)

1. 기존 붓꽃 데이터를 학습합니다.
2. 사용자가 꽃잎 길이와 너비를 입력합니다.
3. 입력값과 기존 데이터 사이의 거리를 계산합니다.
4. 가장 가까운 5개의 데이터를 찾습니다.
5. 가장 많이 등장한 품종을 예측합니다.

**표준화(StandardScaler)를 사용하는 이유**

꽃잎 길이와 너비의 측정 범위가 다를 수 있으므로
두 변수의 크기를 비슷한 기준으로 맞춘 후 거리를 계산합니다.
""")
