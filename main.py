import streamlit as st
st.title('나의 첫 웹 서비스 만들기')
a=st.text_input('이름을 입력하세용')
b=st. selectbox('좋아하는 음식을 선택하세요',['초밥','마라탕','마라샹궈',])
if st.button('인사말 생성'):
  st.write('반갑습니다')
  st.info(a+'님, 안녕하세요!')
