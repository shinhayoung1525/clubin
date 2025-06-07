import pandas as pd
import os

def save_rating(club_code, nickname, scores, review, filepath="ratings.csv"):

    data = {
        "동아리 코드": [club_code],
        "닉네임": [nickname],
        "재무건전성": [scores[0]],
        "회원 수": [scores[1]],
        "내외부 활동": [scores[2]],
        "회칙": [scores[3]],
        "친목 활동": [scores[4]],
        "리뷰": [review]
    }

    df = pd.DataFrame(data)

    if os.path.exists(filepath):
        df.to_csv(filepath, mode='a', index=False, header=False, encoding='utf-8-sig')
    else:
        df.to_csv(filepath, index=False, encoding='utf-8-sig')

def clean_invalid_ratings(rating_path="ratings.csv", club_info_path="club_info.csv"):
    """
    ratings.csv 파일에서 club_info.csv에 존재하지 않는 club_code를 가진 행을 삭제
    """
    # ratings.csv와 club_info.csv 읽기
    try:
        ratings_df = pd.read_csv(rating_path, encoding='utf-8-sig')
        club_info_df = pd.read_csv(club_info_path, encoding='utf-8-sig')
    except FileNotFoundError:
        print("파일이 존재하지 않습니다.")
        return

    # 유효한 club_code 목록
    valid_codes = set(club_info_df["club_code"])

    # 필터링: ratings.csv에서 club_code가 유효한 것만 남김
    filtered_df = ratings_df[ratings_df["동아리 코드"].isin(valid_codes)]

    # 덮어쓰기 저장
    filtered_df.to_csv(rating_path, index=False, encoding='utf-8-sig')
    print(f"유효한 평가만 {rating_path}에 저장 완료. {len(filtered_df)}건 유지됨.")