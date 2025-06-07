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

#===================== Font Setting ======================#
font_path = 'font/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

#===================== Supabase Upload ===================#
def upload_logo_to_supabase(club_code: str, file):
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    file_path = f"{club_code}.png"
    supabase.storage.from_("logos").upload(
        file=file,
        path=file_path,
        file_options={"content-type": "image/png", "upsert": True}
    )
    return f"{st.secrets['supabase']['url']}/storage/v1/object/public/logos/{file_path}"

def upload_logo(club_code, uploaded_file):
    file_data = uploaded_file.getvalue()
    path = f"{club_code}.png"
    bucket = supabase.storage.from_("logos")
    try:
        bucket.remove([path])
    except Exception:
        pass
    bucket.upload(path=path, file=file_data, file_options={"content-type": "image/png"})
    return f"{st.secrets['supabase']['url']}/storage/v1/object/public/logos/{path}"

def get_logo_url(club_code: str) -> str:
    base_url = st.secrets["supabase"]["url"]
    return f"{base_url}/storage/v1/object/public/logos/{club_code}.png"

#===================== Supabase Client ===================#
supabase: Client = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

#===================== Utility ===========================#
def generate_unique_code():
    existing = supabase.table("club_info").select("club_code").execute().data
    used = {row["club_code"] for row in existing}
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in used:
            return code

def send_email(to_email, club_code):
    msg = MIMEText(f"안녕하세요!\n요청하신 동아리 등록이 완료되었습니다.\n클럽 코드: {club_code}.\n\n\n추가로 문의사항이 있으시면 {st.secrets['email']}로 문의 부탁드립니다.")
    msg["Subject"] = "Club:IN 동아리 등록 코드 안내"
    msg["From"] = st.secrets["email"]["username"]
    msg["To"] = to_email
    with smtplib.SMTP(st.secrets["email"]["smtp_server"], st.secrets["email"]["smtp_port"]) as server:
        server.starttls()
        server.login(st.secrets["email"]["username"], st.secrets["email"]["password"])
        server.send_message(msg)

#===================== Club Card =========================#
def club_card(club_name, club_describe, tag, stats, club_code, key):
    club1 = st.container(border=True, key=f"club-container-{key}")
    with club1:
        club1col1, club1col2 = st.columns([2, 1])
        with club1col1:
            club1col1col1, club1col2col2 = st.columns([2, 3])
            try:
                club1col1col1.image(get_logo_url(club_code))
            except:
                club1col1col1.write("🚫로고 추가 예정🚫")
            club1col2col2.markdown(
                f":red-badge[{tag[0]}] :orange-badge[{tag[1]}] :green-badge[{tag[2]}] :blue-badge[{tag[3]}] :gray-badge[{tag[4]}]"
            )
            club1col2col2.title(f"{club_name}")
        club1col1.write("동아리 소개👇")
        with club1col1.container(border=True):
            st.markdown(f"{club_describe}")
        with club1col2:
            labels = ['친목', '재무건전성', '회원 수', '회칙', '내외부 활동']
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
    if club1col2.button("동아리 상세정보", icon="📝", use_container_width=True, key=f"detail-{key}"):
        @st.dialog("동아리 상세정보")
        def extra():
            info, rate_all = st.columns(2)

            if info.button("동아리 정보", icon="💡", use_container_width=True):
                st.subheader("📘 동아리 정보")
                st.markdown(f"{club_describe}")

            if rate_all.button("동아리 리뷰", icon="😃", use_container_width=True):
                st.subheader("⭐ 동아리 리뷰")

                # Supabase에서 리뷰 불러오기
                supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
                response = supabase.table("ratings").select("*").eq("club_code", club_code).execute()
                reviews = response.data

                if not reviews:
                    st.info("아직 등록된 리뷰가 없습니다.")
                else:
                    # 표 만들기
                    review_data = []
                    for row in reviews:
                        nickname = row["nickname"]
                        avg_score = np.mean([row[f"score{i+1}"] for i in range(5)])
                        review = row["review"]
                        review_data.append({
                            "닉네임": nickname,
                            "⭐ 평균 별점": f"{avg_score:.1f} / 5.0",
                            "리뷰": review
                        })

                    st.dataframe(pd.DataFrame(review_data), use_container_width=True)

        extra()
    return club1

#===================== 캐시된 데이터 로딩 =========================#
@st.cache_data(ttl=100)
def get_club_info_df():
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    response = supabase.table("club_info").select("*").execute()
    return pd.DataFrame(response.data)

@st.cache_data(ttl=100)
def get_all_avg_scores():
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    response = supabase.table("ratings").select("*").execute()
    ratings = response.data
    score_dict = {}
    if ratings:
        df = pd.DataFrame(ratings)
        grouped = df.groupby("club_code")
        for club_code, group in grouped:
            scores = group[[f"score{i+1}" for i in range(5)]].mean().tolist()
            score_dict[club_code] = scores
    return score_dict

def clean_invalid_supabase_ratings(valid_codes, supabase):
    response = supabase.table("ratings").select("id, club_code").execute()
    data = response.data
    if not data:
        return
    invalid_ids = [row["id"] for row in data if row["club_code"] not in valid_codes]
    for chunk in [invalid_ids[i:i + 50] for i in range(0, len(invalid_ids), 50)]:
        supabase.table("ratings").delete().in_("id", chunk).execute()

#===================== 동아리 카드 렌더링 =========================#
def render_all_club_cards():
    supabase = create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])
    club_info_df = club_info_df[club_info_df["accept"] == "O"]
    all_avg_scores = get_all_avg_scores()
    valid_codes = club_info_df["club_code"].unique().tolist()
    clean_invalid_supabase_ratings(valid_codes, supabase)

    search_col, tag_col = st.columns([3, 3])
    keyword = search_col.text_input("동아리 이름 검색 🔎")
    all_tags_raw = club_info_df["tag"].tolist()
    all_tags = sorted(set(tag for tags in all_tags_raw for tag in tags.split()))
    selected_tags = tag_col.multiselect("테그로 동아리 검색 🔎", all_tags)

    for i, row in club_info_df.iterrows():
        club_name = row["club_name"]
        club_code = row["club_code"]
        tags_str = row["tag"]
        club_describe = row["club_describe"]
        tag_list = tags_str.split()

        if keyword.strip() and keyword.strip() not in club_name:
            continue
        if selected_tags and not any(tag in tag_list for tag in selected_tags):
            continue

        averages = all_avg_scores.get(club_code, [0, 0, 0, 0, 0])
        club_card(club_name, club_describe, tag_list, averages, club_code, key=f"card-{i}")

#===================== 평가 저장 =========================#
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


def send_contact_email(message_title,sender_email, sender_tel, message_body):
    try:
        # 이메일 내용
        msg = MIMEText(
            f"[Club:IN 문의 도착]\n\n보낸 사람 이메일: {sender_email}\n보낸 사람 전화번호:{sender_tel}\n\n제목:{message_title}\n내용:\n{message_body}"
        )
        msg["Subject"] = f"📩 Club:IN 문의가 도착했습니다 | {message_title}"
        msg["From"] = st.secrets["email"]["username"]  # 관리자 계정
        msg["To"] = st.secrets["email"]["username"]    # 관리자에게 발송

        # SMTP 연결
        with smtplib.SMTP(st.secrets["email"]["smtp_server"], st.secrets["email"]["smtp_port"]) as server:
            server.starttls()
            server.login(
                st.secrets["email"]["username"],
                st.secrets["email"]["password"]
            )
            server.sendmail(
                from_addr=st.secrets["email"]["username"],
                to_addrs=[st.secrets["email"]["username"]],
                msg=msg.as_string()
            )

        st.success("문의사항이 성공적으로 전송되었습니다! 🙌", icon="📨")

    except Exception as e:
        st.error(f"문의사항 전송 실패: {e}", icon="❌")