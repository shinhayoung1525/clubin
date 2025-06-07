import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
from funtion import *
import pandas as pd

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
                save_rating_supabase(
                    club_code,
                    nickname,
                    [score1, score2, score3, score4, score5],
                    review
                )
                st.success("Supabase에 저장되었습니다!")
            else:
                st.error("모든 항목을 입력해주세요.")

    rate()
if right.button("동아리 추가신청", icon="➕", use_container_width=True):
    @st.dialog("동아리 추가신청")
    def extra():
        st.subheader("동아리 추가 신청 양식", divider=True)

        club_name = st.text_input("동아리 이름")
        tag = st.multiselect(
            "동아리 테그 선택 (5개) [입력 후 추가 가능]",
        ["교내활동", "교외활동", "봉사", "자연과학", "공학", "학술", "프로그래밍", "게임", "보건", "생명", "종교", "기독동아리", "친목", "회식 많음", "미디어", "사진", "여행", "그림", "만화",
        "연극", "행사", "대회", "창작", "창업", "발표", "밴드", "음악", "운동", "축구", "베드민턴","테니스", "수영", "배구", "볼링", "헬스", "소모임", "스터디", "주식", "제태크",
        "경제", "정치", "언어", "국문","영어", "일본어"," 중국어", "책", "논문", "공부", "상시모집", "능력 필요", "초보 가능"],
        accept_new_options = True,
        max_selections=5
        )
        club_describe = st.text_input("동아리 소개")
        club_email = st.text_input("동아리 코드 받을 이메일")
        uploaded_logo = st.file_uploader("동아리 로고 (.png)", type=["png"])

        if st.button("신청 제출"):
            if not (club_name and tag and club_describe and club_email and uploaded_logo):
                st.error("모든 항목을 입력해야 신청할 수 있습니다.")
                return

            club_code = generate_unique_code()
            upload_logo(club_code, uploaded_logo)

            # DB 저장
            supabase.table("club_info").insert({
                "club_name": club_name,
                "club_code": club_code,
                "tag": ' '.join(tag),
                "club_describe": club_describe
            }).execute()

            send_email(club_email, club_code)
            st.success(f"동아리 신청이 완료되었습니다! 클럽 코드는 {club_code}이며 이메일로도 전송되었습니다.")

    extra()

render_all_club_cards()