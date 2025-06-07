import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
from club_card import render_all_club_cards
from save import save_rating
import pandas as pd
from save import clean_invalid_ratings

st.set_page_config(
    page_title="동아리 평가 시스템",
    layout="wide",            # 👉 와이드 모드
    initial_sidebar_state="auto"
)
font_path = 'font/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

left, middle, right = st.columns([3,2,2])
left.header("Club:IN")
if middle.button("동아리 평가하기", icon="✍️", use_container_width=True):
    @st.dialog("동아리 평가하기")
    def rate():
        club_code = st.text_input("동아리 코드")
        nickname = st.text_input("닉네임(익명)")
        st.subheader("동아리 별점 1~5점", divider=True)
        st.write("친목 활동(협력, 소통)")
        score1 = st.feedback("stars", key="one")
        st.write("동아리 재무건전성(동아리비 사용)")
        score2 = st.feedback("stars", key="two")
        st.write("회원 수(적당한 회원 수를 유지하는지)")
        score3 = st.feedback("stars", key="three")
        st.write("회칙(동아리 규칙)")
        score4 = st.feedback("stars", key="four")
        st.write("내외부 활동")
        score5 = st.feedback("stars", key="five")
        review = st.text_input("평가(리뷰) 자유롭게 적어주세요")
        if st.button("등록"):
            if club_code and nickname and all(s is not None for s in [score1, score2, score3, score4, score5]):
                save_rating(
                    club_code,
                    nickname,
                    [score1, score2, score3, score4, score5],
                    review
                )
                st.success("성공적으로 저장되었습니다!")
                clean_invalid_ratings()
            else:
                st.error("모든 항목을 입력해주세요.")

    rate()
if right.button("동아리 추가신청", icon="➕", use_container_width=True):
    @st.dialog("동아리 추가신청 안내")
    def extra():
        st.subheader(f"동아리 추가 신청 양식",divider=True)
        st.write(f"동아리명, 동아리 인원, 로고, 소개, 테그 외 넣고 싶은 정보들")
        st.write(f"위 순서 양식에 맞춰 작성하여 아래 이메일 주소로 보내주세요.")
        st.write(f"이메일: shy030205@yonsei.ac.kr")
    extra()
# 전체 카드 렌더링
render_all_club_cards()