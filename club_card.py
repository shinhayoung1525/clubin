import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.font_manager as fm
import pandas as pd
font_path = 'font/NanumGothic.ttf'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

def club_card(club_name, club_describe, tag, stats,key):
    club1 = st.container(border=True, key=f"club-container-{key}")
    with club1:
        club1col1, club1col2 = st.columns([2,1])
        with club1col1:
            club1col1col1, club1col2col2 = st.columns([2,3])
            club1col1col1.image(f"logo_test.png")
            club1col2col2.markdown(
        f":violet-badge[{tag[0]}] :orange-badge[{tag[1]}] :gray-badge[{tag[2]}]"
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

    if club1col2.button("동아리 상세설명", icon="📝", use_container_width=True):
        @st.dialog("동아리 상세설명")
        def extra():
            st.write("동아리 상세설명")
        extra()
    return(club1)

def render_all_club_cards(info_path="club_info.csv", rating_path="ratings.csv"):
    # CSV 로드
    try:
        club_info_df = pd.read_csv(info_path, encoding='utf-8-sig')
    except FileNotFoundError:
        st.error("club_info.csv 파일이 없습니다.")
        return

    try:
        ratings_df = pd.read_csv(rating_path, encoding='utf-8-sig')
    except FileNotFoundError:
        ratings_df = pd.DataFrame(columns=[
            "동아리 코드", "닉네임", "재무건전성", "회원 수", "내외부 활동", "회칙", "친목 활동", "리뷰"
        ])

    # 검색/필터 UI
    search_col, tag_col = st.columns([3, 3])
    keyword = search_col.text_input("동아리 이름 검색 🔎")
    selected_tags = tag_col.multiselect(
        "테그로 동아리 검색 🔎",
        ["자연과학", "공학", "프로그래밍", "음악", "학술", "운동"]
    )

    # 동아리별 렌더링
    for i, row in club_info_df.iterrows():
        club_name = row["club_name"]
        club_code = row["club_code"]
        tags_str = row["tag"]
        club_describe = row["club_describe"]

        # 필터 처리
        tag_list = tags_str.split()
        keyword_match = keyword.strip() in club_name if keyword.strip() else True
        tag_match = any(tag in tag_list for tag in selected_tags) if selected_tags else True

        if not (keyword_match and tag_match):
            continue  # 둘 중 하나라도 불일치 시 건너뜀

        # 최대 3개 태그로 맞추기
        tags = tag_list[:3] + [""] * (3 - len(tag_list))

        # 평균 점수 계산
        club_ratings = ratings_df[ratings_df["동아리 코드"] == club_code]
        if not club_ratings.empty:
            score_columns = ["친목 활동", "재무건전성", "회원 수", "회칙", "내외부 활동"]
            averages = club_ratings[score_columns].mean().tolist()
        else:
            averages = [0, 0, 0, 0, 0]

        club_card(club_name, club_describe, tags, averages, key=f"card-{i}")