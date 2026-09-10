import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="박스오피스 데이터 분석 앱",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 1개년 박스오피스 데이터 분석")
st.markdown("KOBIS 데이터를 바탕으로 영화별 관객수 추이 및 통계를 분석합니다.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 및 전처리 (캐싱 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    
    # 1. CSV 데이터 불러오기
    df = pd.read_csv(url)
    
    # 2. 결측치(빈 값)가 포함된 행 삭제
    df = df.dropna()
    
    # 3. '기준일자' 컬럼을 날짜(datetime) 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])
    
    # 4. 숫자형 컬럼 데이터 타입 정리
    if "해당일관객수" in df.columns:
        df["해당일관객수"] = pd.to_numeric(df["해당일관객수"], errors="coerce")
    if "누적관객수" in df.columns:
        df["누적관객수"] = pd.to_numeric(df["누적관객수"], errors="coerce")
    if "순위" in df.columns:
        df["순위"] = pd.to_numeric(df["순위"], errors="coerce")
    
    # 5. 전체 데이터를 기준일자 순서대로 정렬
    df = df.sort_values("기준일자")
    
    return df

# 데이터 로딩 실행
data = load_data()

# -----------------------------------------------------------------------------
# 3. 영화 선택 목록 생성 (누적관객수 내림차순 정렬)
# -----------------------------------------------------------------------------
movie_order = (
    data.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# -----------------------------------------------------------------------------
# 4. 사이드바: 분석 옵션 선택
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 조회 조건")
selected_movie = st.sidebar.selectbox(
    "영화 선택 (누적관객수 순)",
    options=movie_order,
    index=0
)

# 선택한 영화의 데이터만 추출
filtered_df = data[data["영화명"] == selected_movie]

# -----------------------------------------------------------------------------
# 5. 메인 화면 - 구역 1: 영화별 관객수 변화 추이 (선 그래프)
# -----------------------------------------------------------------------------
st.header(f"📈 1. '{selected_movie}' 일별 관객수 추이")

if not filtered_df.empty:
    fig1 = px.line(
        filtered_df,
        x="기준일자",
        y="해당일관객수",
        title="일자별 해당일 관객수 변화",
        labels={"기준일자": "날짜", "해당일관객수": "일별 관객수 (명)"},
        markers=True,
        hover_data={"기준일자": "|%Y-%m-%d", "해당일관객수": ":,d"}
    )
    
    fig1.update_layout(
        xaxis_title="기준일자",
        yaxis_title="해당일 관객수 (명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    st.info(
        f"💡 **이 그래프로 알 수 있는 것:** "
        f"'{selected_movie}'의 개봉 이후 날짜별 일일 관객수 증감 추세와 최고 관객수를 기록한 시점을 파악할 수 있습니다."
    )
else:
    st.warning("선택한 영화의 데이터가 존재하지 않습니다.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 메인 화면 - 구역 2: 영화별 누적 관객수 변화 (영역 차트)
# -----------------------------------------------------------------------------
st.header(f"📊 2. '{selected_movie}' 누적 관객수 추이")

if not filtered_df.empty:
    fig2 = px.area(
        filtered_df,
        x="기준일자",
        y="누적관객수",
        title="일자별 누적 관객수 증가 추이",
        labels={"기준일자": "날짜", "누적관객수": "누적 관객수 (명)"},
        hover_data={"기준일자": "|%Y-%m-%d", "누적관객수": ":,d"}
    )
    
    fig2.update_layout(
        xaxis_title="기준일자",
        yaxis_title="누적 관객수 (명)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    st.info(
        f"💡 **이 그래프로 알 수 있는 것:** "
        f"'{selected_movie}'의 누적 관객수가 시간 경과에 따라 쌓여가는 속도와 흥행 성장세가 정체되는 시점을 한눈에 볼 수 있습니다."
    )
else:
    st.warning("선택한 영화의 데이터가 존재하지 않습니다.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 메인 화면 - 구역 3: 장기 흥행(20일 이상 TOP 10) 영화 중 누적 관객수 TOP 5 비교
# -----------------------------------------------------------------------------
st.header("🏆 3. 장기 흥행(TOP 10 20일 이상) TOP 5 영화 추이 비교")

# 1) TOP 10 진입 데이터 추출 (순위 컬럼이 있으면 10위 이내 필터링)
if "순위" in data.columns:
    top10_data = data[data["순위"] <= 10]
else:
    top10_data = data

# 2) 영화별 TOP 10 등재 일수 계산
movie_days_count = top10_data.groupby("영화명")["기준일자"].nunique()

# 3) TOP 10 등재 일수가 20일 이상인 영화만 필터링
movies_over_20days = movie_days_count[movie_days_count >= 20].index

# 4) 조건(20일 이상)을 만족하는 영화 중 최대 누적 관객수 기준 상위 5개 선정
top5_long_running_movies = (
    data[data["영화명"].isin(movies_over_20days)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index
    .tolist()
)

# 5) 선정된 5개 영화의 전체 데이터 추출
top5_long_df = data[data["영화명"].isin(top5_long_running_movies)]

if not top5_long_df.empty:
    # color="영화명"을 지정해 영화별 개별 색상 및 범례 생성
    fig3 = px.line(
        top5_long_df,
        x="기준일자",
        y="누적관객수",
        color="영화명",
        title="TOP 10에 20일 이상 등장한 영화 중 누적 관객수 TOP 5 성장 추이",
        labels={"기준일자": "날짜", "누적관객수": "누적 관객수 (명)", "영화명": "영화 제목"},
        markers=True,
        hover_data={"기준일자": "|%Y-%m-%d", "누적관객수": ":,d"}
    )
    
    fig3.update_layout(
        xaxis_title="기준일자",
        yaxis_title="누적 관객수 (명)",
        hovermode="x unified",
        legend_title_text="영화 제목"
    )
    
    st.plotly_chart(fig3, use_container_width=True)
    
    st.info(
        "💡 **이 그래프로 알 수 있는 것:** "
        "일시적인 깜짝 흥행에 그치지 않고 최소 20일 이상 TOP 10 상위권을 지킨 '장기 흥행작' 중 "
        "최종 누적 관객수가 가장 높았던 상위 5개 영화의 날짜별 관객 누적 속도를 비교할 수 있습니다."
    )
else:
    st.warning("조건을 만족하는 영화 데이터가 존재하지 않습니다.")
