import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
from funtion import *
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import time
import re

st.set_page_config(
    page_title="동아리 평가 시스템",
#    layout="wide",            # 👉 와이드 모드
    initial_sidebar_state="auto"
)
font_path = 'font/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

left, help, admin, middle, right = st.columns([9, 1, 1, 6, 6])
with left:
    logo_col, title_col = st.columns([3, 5]) 
    with logo_col:
        st.image("logo/CLUBIN.png")

    title_col.title("Club:IN")

if help.button( "❓",use_container_width=True):
    @st.dialog("CLUB:IN 사용법")
    def help():
        st.subheader("동아리 평가하기", divider=True)
        st.write("1. 동아리 코드를 입력한다.")
        st.write("2. 닉네임을 입력한다. (개인정보에 주의해주세요.)")
        st.write("3. 마지막에 평가는 꼭 부탁드립니다.")
        st.write("4. 등록 버튼을 누르면 끝!")
        st.write("5. 동아리 코드를 정확하게 입력하셨다면 동아리 상세정보에서 리뷰를 확인할 수 있어요!")
        st.subheader("동아리 추가신청", divider=True)
        st.write("1. 동아리 이름을 입력한다.")
        st.write("2. 동아리를 설명하는 테그를 5개 선택한다. [꼭 5개 부탁드립니다.]")
        st.write("3. 동아리 소개 글을 적는다.")
        st.write("4. 동아리 코드를 받을 이메일을 적는다.")
        st.write("5. 동아리 코드를 올린다. [.png 만 가능]")
        st.write("6. 동아리 코드 이메일을 확인한다. [동아리 코드를 부원에게 알려주세요!]")
        st.write("*동아리 코드 이메일이 오지 않은 경우 문의하기 버튼을 눌러 문의 부탁드립니다.*")
        st.write("*궁금한 것이 있다면 편하게 문의해주세요!*")
        hh, mm, aa = st.columns([2,2,2])
        if hh.button("문의하기", key="contact_open"):
            st.session_state["show_contact"] = True

        if st.session_state.get("show_contact", False):
            st.subheader("📬 문의사항을 작성해주세요")
            sender_email = st.text_input("📧 답장 받을 이메일 주소", key="contact_email")
            sender_tel = st.text_input("☎️ 답장 받을 전화번호", key="contact_tel")
            message_title = st.text_input("제목", key="message_title")
            message = st.text_area("💬 문의 내용", height=200, key="contact_message")

            if st.button("문의 보내기", key="contact_send"):
                if not sender_email or not message:
                    st.error("모든 항목을 입력해주세요.", icon="⚠️")
                if not is_valid_email(sender_email):
                    st.error("이메일 형식이 올바르지 않습니다.")
                    return
                else:
                    send_contact_email(message_title,sender_email,sender_tel, message)
                    time.sleep(1)
                    st.session_state["show_contact"] = False
                    st.rerun()
    help()

if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False
    st.session_state.show_edit_form = False
if admin.button("🔐", use_container_width=True, key="admin_logo_button"):
    st.session_state["admin_authenticated"] = False
    st.session_state.show_edit_form = False
    if "admin_password_input" in st.session_state:
        del st.session_state["admin_password_input"]  # ✅ 입력값 삭제

    @st.dialog("🔐 관리자 인증")
    def show_admin_dialog():
        # 🔐 비밀번호 입력
        password = st.text_input("비밀번호", type="password", key="admin_password_input")

        if password == st.secrets["admin_password"]["password"]:
            st.session_state["admin_authenticated"] = True
        elif password:
            st.error("비밀번호가 올바르지 않습니다.")

        if st.session_state.get("admin_authenticated", False):
            st.success("인증 성공 ✅")
            st.markdown("### 동아리 관리 관리자 창")

            # 🧭 탭 분기
            tab1, tab2 = st.tabs(["✅ 동아리 승인 및 삭제", "✏️ 상세정보 수정"])

            # 📌 승인 및 삭제 탭
            with tab1:
                try:
                    data = supabase.table("club_info").select("club_name, club_code, accept").execute().data
                    df = pd.DataFrame(data)

                    if df.empty:
                        st.info("등록된 동아리가 없습니다.")
                    else:
                        df["accept"] = df["accept"].fillna("X")
                        original_df = df.copy()

                        edited_df = st.data_editor(
                            df,
                            use_container_width=True,
                            column_config={
                                "accept": st.column_config.SelectboxColumn("승인 여부", options=["O", "X"]),
                                "club_code": st.column_config.TextColumn("클럽 코드", disabled=True)
                            },
                            column_order=["club_name", "club_code", "accept"],
                            num_rows="dynamic"
                        )

                        deleted_df = original_df[~original_df["club_code"].isin(edited_df["club_code"])]
                        pending_deletion = {}

                        if not deleted_df.empty:
                            st.subheader("🗑️ 삭제 확인")
                            for _, row in deleted_df.iterrows():
                                with st.expander(f"{row['club_name']} 삭제 확인", expanded=True):
                                    st.warning(f"클럽 코드 {row['club_code']} 입력 시 삭제됩니다.")
                                    with st.form(key=f"delete-form-{row['club_code']}"):
                                        code_input = st.text_input("클럽 코드 입력", key=f"code-input-{row['club_code']}")
                                        confirm = st.form_submit_button("✅ 삭제 확정", type="primary")
                                        if confirm and code_input.strip().upper() == row['club_code']:
                                            pending_deletion[row['club_code']] = row['club_name']
                                            st.success("삭제 준비 완료")
                                        elif confirm:
                                            st.error("❌ 클럽 코드가 일치하지 않습니다.")

                        merged_df = edited_df.merge(
                            original_df[["club_code", "accept"]],
                            on="club_code",
                            how="left",
                            suffixes=("", "_original")
                        )
                        changed_rows = merged_df[merged_df["accept"] != merged_df["accept_original"]]

                        if st.button("📤 변경사항 최종 적용", type="primary"):
                            for _, row in changed_rows.iterrows():
                                supabase.table("club_info").update({"accept": row["accept"]}).eq("club_code", row["club_code"]).execute()
                                st.toast(f"{row['club_name']} 승인 상태 변경: {row['accept']}", icon="✅")

                            for club_code, club_name in pending_deletion.items():
                                supabase.table("club_info").delete().eq("club_code", club_code).execute()
                                st.toast(f"{club_name} 삭제됨", icon="🗑️")

                            if not changed_rows.empty or pending_deletion:
                                st.success("변경 완료! 앱을 새로고침합니다.")
                                st.cache_data.clear()
                                st.rerun()

                except Exception as e:
                    st.exception(e)

            # ✏️ 상세정보 수정 탭
            with tab2:
                df = get_club_info_df()

                selected_club = st.selectbox("수정할 동아리를 선택하세요", df["club_name"], key="selected_club")
                club_row = df[df["club_name"] == selected_club].iloc[0]

                new_describe = st.text_area("동아리 소개 (club_describe)", club_row["club_describe"], key="club_describe")
                new_member_count = st.number_input("맴버 수 (club_member_count)", min_value=0, value=int(club_row["club_member_count"] or 0), key="club_member_count")
                new_activity = st.text_area("활동 소개 (activity_details)", club_row["activity_details"] or "", key="activity_details")

                if st.button("변경사항 적용", type="primary"):
                    response = supabase.table("club_info").update({
                        "club_describe": new_describe,
                        "club_member_count": new_member_count,
                        "activity_details": new_activity
                    }).eq("club_code", club_row["club_code"]).execute()

                    if response and response.data:
                        st.success(f"✅ '{selected_club}' 동아리 정보가 성공적으로 수정되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 수정에 실패했습니다. 응답이 비어있습니다.")

    show_admin_dialog()

if middle.button("동아리 평가하기", icon="✍️", use_container_width=True):
    @st.dialog("동아리 평가하기")
    def rate():
        club_code = st.text_input("동아리 코드", key="input_code")
        nickname = st.text_input("닉네임(익명)", key="input_name")
        st.subheader("동아리 별점 1~5점", divider=True)

        st.write("친목 활동(협력, 소통)")
        score1 = st.feedback("stars", key="score1")
        st.write("동아리 재무건전성(동아리비 사용)")
        score2 = st.feedback("stars", key="score2")
        st.write("회원 수(적당한 회원 수를 유지하는지)")
        score3 = st.feedback("stars", key="score3")
        st.write("회칙(동아리 규칙)")
        score4 = st.feedback("stars", key="score4")
        st.write("내외부 활동")
        score5 = st.feedback("stars", key="score5")

        review = st.text_input("평가(리뷰) 자유롭게 적어주세요", key="input_review")

        if st.button("등록", key="submit_rating"):
            if club_code and nickname and all(s is not None for s in [score1, score2, score3, score4, score5]):
                save_rating_supabase(
                    club_code,
                    nickname,
                    [score1+1, score2+1, score3+1, score4+1, score5+1],
                    review
                )
                st.success("리뷰가 저장되었습니다!")

                for key in ["input_code", "input_name", "input_review", "score1", "score2", "score3", "score4", "score5"]:
                    if key in st.session_state:
                        del st.session_state[key]

                st.rerun()

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
        ["교내활동", "교외활동", "정기활동", "봉사", "자연과학", "공학", "학술", "프로그래밍", "게임", "보건", "생명", 
         "종교", "기도회", "예배", "기도모임", "교회" , "패션", "친목", "토론", "일러스트", "회식 많음", "미디어", "영화","사진", "촬영","편집","여행", 
         "청춘", "그림", "만화", "겨울 스포츠", "전시회", "연극", "행사", "대회", "창작", "창업", "평화","프로젝트","발표", "밴드", "음악",
         "악기","공연", "응원","치어리딩", "춤", "운동", "축구", "베드민턴", "야구", "탁구",
         "테니스", "수영", "배구", "볼링", "헬스", "농구", "클라이밍", "태권도","유도", "검도", "소모임", "스터디", "주식", "제태크",
         "경제", "정치", "언어", "국문","영어", "일본어"," 중국어", "책", "논문", "공부", "상시모집", 
         "능력 필요", "초보 가능"],
        accept_new_options = True
        )
        club_member_count = st.slider("동아리 부원수", 0, 100, 25)
        club_describe = st.text_area("동아리 소개")
        activity_details = st.text_area("중요한 동아리 활동 소개개")
        club_email = st.text_input("동아리 코드 받을 이메일")
        uploaded_logo = st.file_uploader("동아리 로고 (.png)", type=["png"])
        st.write(f"동아리의 수상 경력 및 활동 일정, 모집 글 등 추가하고 싶으신 내용이 있으시다면 이메일(내용 포함) 부탁드립니다!")
        st.write(f"이메일: yon.club.in@gmail.com")
        if st.button("신청 제출"):
            if not (club_name and tag and club_describe and club_email and uploaded_logo):
                st.error("모든 항목을 입력해야 신청할 수 있습니다.")
                return

            if len(tag) != 5:
                st.error("태그는 꼭 5개 골라주세요.")
                return
            if not is_valid_email(club_email):
                st.error("이메일 형식이 올바르지 않습니다.")
                return
            if is_duplicate_club_name(club_name):
                st.error("같은 이름의 동아리가 이미 등록되어 있습니다.")
                return

            club_code = generate_unique_code()
            upload_logo(club_code, uploaded_logo)

            # DB 저장
            supabase.table("club_info").insert({
                "club_name": club_name,
                "club_code": club_code,
                "tag": ' '.join(tag),
                "club_describe": club_describe,
                "accept" : "X",
                "club_member_count" : club_member_count,
                "activity_details" : activity_details
            }).execute()

            send_email(club_email, club_code, club_name)
            st.success(f"{club_name} 동아리 신청이 완료되었습니다! 클럽 코드는 {club_code}이며 이메일로도 전송되었습니다.")

    extra()

render_all_club_cards()