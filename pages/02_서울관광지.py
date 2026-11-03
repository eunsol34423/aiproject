
import streamlit as st
import folium
from streamlit_folium import st_folium

# 페이지 설정
st.set_page_config(
    page_title="서울 관광지 TOP 10",
    page_icon="🗺️",
    layout="wide"
)

# 관광지 데이터
ATTRACTIONS = [
    {
        "rank": 1,
        "name": "경복궁 (Gyeongbokgung Palace)",
        "lat": 37.5796,
        "lon": 126.9770,
        "desc": "조선 왕조의 대표 궁궐입니다. 근위병 교대식과 한복 체험으로 유명합니다."
    },
    {
        "rank": 2,
        "name": "명동 (Myeongdong)",
        "lat": 37.5636,
        "lon": 126.9869,
        "desc": "쇼핑, 화장품 매장, 길거리 음식이 모여 있는 활기찬 관광지입니다."
    },
    {
        "rank": 3,
        "name": "N서울타워 (N Seoul Tower)",
        "lat": 37.5512,
        "lon": 126.9882,
        "desc": "남산의 대표 전망 명소로 서울 도심의 아름다운 전경을 볼 수 있습니다."
    },
    {
        "rank": 4,
        "name": "북촌 한옥마을 (Bukchon Hanok Village)",
        "lat": 37.5826,
        "lon": 126.9830,
        "desc": "전통 한옥이 이어지는 역사적인 마을입니다."
    },
    {
        "rank": 5,
        "name": "창덕궁 (Changdeokgung Palace)",
        "lat": 37.5794,
        "lon": 126.9910,
        "desc": "유네스코 세계유산으로 지정된 궁궐이며 아름다운 후원이 유명합니다."
    },
    {
        "rank": 6,
        "name": "홍대 거리 (Hongdae)",
        "lat": 37.5563,
        "lon": 126.9236,
        "desc": "인디 음악, 거리 공연, 개성 있는 상점과 카페를 즐길 수 있습니다."
    },
    {
        "rank": 7,
        "name": "동대문디자인플라자 (DDP)",
        "lat": 37.5665,
        "lon": 127.0092,
        "desc": "독특한 건축물과 전시, 디자인 행사로 유명한 복합문화공간입니다."
    },
    {
        "rank": 8,
        "name": "광장시장 (Gwangjang Market)",
        "lat": 37.5700,
        "lon": 126.9997,
        "desc": "빈대떡과 김밥 등 다양한 한국 전통시장 먹거리를 경험할 수 있습니다."
    },
    {
        "rank": 9,
        "name": "청계천 (Cheonggyecheon Stream)",
        "lat": 37.5692,
        "lon": 126.9780,
        "desc": "서울 도심을 가로지르는 산책로와 물길이 있는 휴식 공간입니다."
    },
    {
        "rank": 10,
        "name": "롯데월드타워 (Lotte World Tower)",
        "lat": 37.5125,
        "lon": 127.1025,
        "desc": "서울의 대표적인 초고층 랜드마크로 서울스카이 전망대가 유명합니다."
    }
]

# 제목
st.title("🗺️ 서울 외국인 관광객 추천 명소 TOP 10")
st.write(
    "서울을 방문하는 외국인 관광객을 위한 "
    "대표 관광 명소 10곳을 지도에서 확인하세요."
)

st.info(
    "아래 순위는 공식 방문객 통계 순위가 아닌 "
    "대표 관광 명소 추천 순서입니다."
)

# 서울 지도 생성
m = folium.Map(
    location=[37.5665, 126.9780],
    zoom_start=12,
    tiles="OpenStreetMap"
)

# 관광지 마커 표시
for place in ATTRACTIONS:

    popup_html = f"""
    <div style="width:220px">
        <h4>TOP {place['rank']}</h4>
        <b>{place['name']}</b>
        <p>{place['desc']}</p>
    </div>
    """

    folium.Marker(
        location=[
            place["lat"],
            place["lon"]
        ],
        tooltip=f"TOP {place['rank']} - {place['name']}",
        popup=folium.Popup(
            popup_html,
            max_width=300
        ),
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background-color:#1769aa;
                color:white;
                border:2px solid white;
                border-radius:50%;
                width:28px;
                height:28px;
                text-align:center;
                line-height:24px;
                font-weight:bold;
                font-size:13px;
                box-shadow:0 1px 4px #555;
            ">
                {place['rank']}
            </div>
            """
        )
    ).add_to(m)

# 지도 출력
st.subheader("📍 서울 주요 관광지 지도")

st_folium(
    m,
    use_container_width=True,
    height=560,
    returned_objects=[]
)

# 지도 아래 관광지 설명
st.subheader("🏛️ 관광지 TOP 10 소개")

for start in range(0, len(ATTRACTIONS), 2):

    cols = st.columns(2)

    for col, place in zip(
        cols,
        ATTRACTIONS[start:start + 2]
    ):

        with col:

            st.markdown(
                f"### {place['rank']}. {place['name']}"
            )

            st.write(place["desc"])

            st.divider()

# 하단 안내
st.caption(
    "지도 데이터 © OpenStreetMap contributors"
)
