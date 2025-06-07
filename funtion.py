import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
import pandas as pd
from supabase import create_client, Client
import os
import smtplib
from email.mime.text import MIMEText
import random, string

font_path = 'font/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

def upload_logo_to_supabase(club_code: str, file):
    supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

    # Supabase Storage에 업로드
    file_path = f"{club_code}.png"
    supabase.storage.from_("logos").upload(
        file=file,
        path=file_path,
        file_options={"content-type": "image/png", "upsert": True}  # upsert 허용
    )

    # 공개 URL 생성
    public_url = f"{st.secrets['supabase']['url']}/storage/v1/object/public/logos/{file_path}"
    return public_url

supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

def generate_unique_code():
    existing = supabase.table("club_info").select("club_code").execute().data
    used = {row["club_code"] for row in existing}
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in used:
            return code

def upload_logo(club_code, uploaded_file):
    file_data = uploaded_file.getvalue()
    path = f"{club_code}.png"
    bucket = supabase.storage.from_("logos")

    # 🔁 기존에 파일이 있으면 먼저 삭제 (덮어쓰기 효과)
    try:
        bucket.remove([path])
    except Exception:
        pass  # 삭제 실패해도 무시 (파일 없을 수도 있음)

    # ✅ 새 파일 업로드
    bucket.upload(
        path=path,
        file=file_data,
        file_options={"content-type": "image/png"}
    )

    return f"{st.secrets['supabase']['url']}/storage/v1/object/public/logos/{path}"

def send_email(to_email, club_code):
    msg = MIMEText(f"안녕하세요!\n요청하신 동아리 등록이 완료되었습니다.\n클럽 코드: {club_code}")
    msg["Subject"] = "Club:IN 동아리 등록 코드 안내"
    msg["From"] = st.secrets["email"]["username"]
    msg["To"] = to_email

    with smtplib.SMTP(st.secrets["email"]["smtp_server"], st.secrets["email"]["smtp_port"]) as server:
        server.starttls()
        server.login(st.secrets["email"]["username"], st.secrets["email"]["password"])
        server.send_message(msg)


def get_logo_url(club_code: str) -> str:
    base_url = st.secrets["supabase"]["url"]
    return f"{base_url}/storage/v1/object/public/logos/{club_code}.png"



#===========================================================================#

def club_card(club_name, club_describe, tag, stats,club_code, key):
    club1 = st.container(border=True, key=f"club-container-{key}")
    with club1:
        club1col1, club1col2 = st.columns([2,1])
        with club1col1:
            club1col1col1, club1col2col2 = st.columns([2,3])   
            try:
                club1col1col1.image(get_logo_url(club_code))
            except:
                club1col1col1.write("🚫로고 추가 예정🚫")
            club1col2col2.write(f"{tag}")
            club1col2col2.markdown(
        f":red-badge[{tag[0]}] :orange-badge[{tag[1]}] :green-badge[{tag[2]}] :blue-badge[{tag[3]}] :gray-badge[{tag[4]}]"
        )
            club1col2col2.title(f"{club_name}")
        club1col1.write("동아리 소개👇")
        with club1col1.container(border=True):
            st.markdown(f"{club_describe}")
        with club1col2:
            labels  = ['친목', '재무건전성', '회원 수', '회칙', '내외부 활동']

            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
            stats += stats[:1]
            angles += angles[:1]

            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
            ax.yaxis.grid(True, color='gray', linewidth=1.5, linestyle='solid')
            ax.xaxis.grid(True, color='gray', linewidth=1.5, linestyle='solid')
            ax.plot(angles, stats, color='blue', linewidth=2)
            ax.fill(angles, stats, color='skyblue', alpha=0.4)
            ax.set_yticks(range(1, 6))
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, fontproperties=font_prop)
            st.pyplot(fig)

    if club1col2.button("동아리 상세설명", icon="📝", use_container_width=True,key=f"detail-{key}"):
        @st.dialog("동아리 상세설명")
        def extra():
            st.write("동아리 상세설명")
        extra()
    return(club1)

def render_all_club_cards(info_path="club_info.csv"):
    # ✅ Supabase 연결
    supabase: Client = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )

    # ✅ 평균 점수 계산 함수
    def get_average_scores(club_code):
        response = supabase.table("ratings").select("*").eq("club_code", club_code).execute()
        data = response.data
        if not data:
            return [0, 0, 0, 0, 0]
        arr = np.array([[row[f"score{i+1}"] for i in range(5)] for row in data])
        return arr.mean(axis=0).tolist()

    # ✅ 유효하지 않은 평가 제거 함수
    def clean_invalid_supabase_ratings(valid_codes):
        response = supabase.table("ratings").select("id, club_code").execute()
        data = response.data
        if not data:
            return
        invalid_ids = [row["id"] for row in data if row["club_code"] not in valid_codes]
        for chunk in [invalid_ids[i:i+50] for i in range(0, len(invalid_ids), 50)]:
            supabase.table("ratings").delete().in_("id", chunk).execute()
        if invalid_ids:
            st.warning(f"유효하지 않은 평가 {len(invalid_ids)}건 삭제됨")

    # ✅ club_info.csv 불러오기
    try:
        response = supabase.table("club_info").select("*").execute()
        club_info_df = pd.DataFrame(response.data)
    except FileNotFoundError:
        st.error("club_info table 오류가 있습니다.")
        return

    # ✅ 유효한 club_code 기준으로 Supabase 데이터 정리
    valid_codes = club_info_df["club_code"].unique().tolist()
    clean_invalid_supabase_ratings(valid_codes)

    # ✅ 검색 및 필터 UI
    search_col, tag_col = st.columns([3, 3])
    keyword = search_col.text_input("동아리 이름 검색 🔎")
    selected_tags = tag_col.multiselect(
        "테그로 동아리 검색 🔎",
        ["자연과학", "공학", "프로그래밍", "음악", "학술", "운동"]
    )

    # ✅ 각 동아리 카드 생성
    for i, row in club_info_df.iterrows():
        club_name = row["club_name"]
        club_code = row["club_code"]
        tags_str = row["tag"]
        club_describe = row["club_describe"]

        tag_list = tags_str.split()
        keyword_match = keyword.strip() in club_name if keyword.strip() else True
        tag_match = any(tag in tag_list for tag in selected_tags) if selected_tags else True

        if not (keyword_match and tag_match):
            continue

        averages = get_average_scores(club_code)

        club_card(club_name, club_describe, tag_list, averages,club_code, key=f"card-{i}")

def save_rating_supabase(club_code, nickname, scores, review):
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase: Client = create_client(url, key)

    data = {
        "club_code": club_code,
        "nickname": nickname,
        "score1": scores[0],
        "score2": scores[1],
        "score3": scores[2],
        "score4": scores[3],
        "score5": scores[4],
        "review": review,
    }

    supabase.table("ratings").insert(data).execute()