import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

# 1) TOP 10 진입 데이터 추출
if "순위" in data.columns:
    top10_data = data[data["순위"] <= 10]
else:
    top10_data = data

# 2) 영화별 TOP 10 등재 일수 계산
movie_days_count = top10_data.groupby("영화명")["기준일자"].nunique()

# 3) TOP 10 등재 일수가 20일 이상인 영화만 필터링
movies_over_20days = movie_days_count[movie_days_count >= 20].index

# 4) 조건을 만족하는 영화 중 최대 누적 관객수 기준 상위 5개 선정
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
        "최소 20일 이상 TOP 10 상위권을 지킨 '장기 흥행작' 중 "
        "최종 누적 관객수가 가장 높았던 상위 5개 영화의 날짜별 관객 누적 속도를 비교할 수 있습니다."
    )
else:
    st.warning("조건을 만족하는 영화 데이터가 존재하지 않습니다.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. 메인 화면 - 구역 4: 전체 박스오피스(TOP 10) 일별 관객수 총합 및 7일 이동평균
# -----------------------------------------------------------------------------
st.header("📉 4. 전체 박스오피스 관객수 추이 및 7일 이동평균")

# 1) TOP 10 영화 대상 데이터 추출
if "순위" in data.columns:
    top10_daily = data[data["순위"] <= 10]
else:
    top10_daily = data

# 2) 기준일자별 TOP 10 영화의 해당일관객수 총합계 구하기
daily_sum_df = (
    top10_daily.groupby("기준일자")["해당일관객수"]
    .sum()
    .reset_index()
    .sort_values("기준일자")
)

# 3) 7일 이동평균(Rolling Mean) 계산
daily_sum_df["7일이동평균"] = daily_sum_df["해당일관객수"].rolling(window=7, min_periods=1).mean()

if not daily_sum_df.empty:
    fig4 = go.Figure()

    # 원본 일별 관객수 합계 (연한 색상)
    fig4.add_trace(
        go.Scatter(
            x=daily_sum_df["기준일자"],
            y=daily_sum_df["해당일관객수"],
            mode="lines",
            name="일별 관객수 합계 (원본)",
            line=dict(color="rgba(180, 180, 180, 0.5)", width=1.5),
            hovertemplate="날짜: %{x|%Y-%m-%d}<br>일별 관객수: %{y:,}명<extra></extra>"
        )
    )

    # 7일 이동평균선 (진하고 두꺼운 색상)
    fig4.add_trace(
        go.Scatter(
            x=daily_sum_df["기준일자"],
            y=daily_sum_df["7일이동평균"],
            mode="lines",
            name="7일 이동평균",
            line=dict(color="#1f77b4", width=3),
            hovertemplate="날짜: %{x|%Y-%m-%d}<br>7일 이동평균: %{y:,.0f}명<extra></extra>"
        )
    )

    fig4.update_layout(
        title="일자별 TOP 10 영화 관객수 합계 및 7일 이동평균 추이",
        xaxis_title="기준일자",
        yaxis_title="관객수 (명)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig4, use_container_width=True)

    st.info(
        "💡 **이 그래프로 알 수 있는 것:** "
        "주말과 평일 간의 관객수 변동(요일 효과)으로 인한 노이즈를 7일 이동평균선으로 완화하여, "
        "전체 영화 시장 관객 규모의 실제 성수기·비수기 흐름과 장기적인 트렌드를 명확하게 파악할 수 있습니다."
    )
else:
    st.warning("분석할 박스오피스 데이터가 존재하지 않습니다.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. 메인 화면 - 구역 5: 월별 전체 관객수 합계 (막대그래프)
# -----------------------------------------------------------------------------
st.header("📊 5. 월별 전체 관객수 합계")

if not daily_sum_df.empty:
    daily_sum_df["연월"] = daily_sum_df["기준일자"].dt.strftime("%Y-%m")

    monthly_sum_df = (
        daily_sum_df.groupby("연월")["해당일관객수"]
        .sum()
        .reset_index()
        .sort_values("연월")
    )

    fig5 = px.bar(
        monthly_sum_df,
        x="연월",
        y="해당일관객수",
        title="월별 박스오피스 전체 관객수 합계",
        labels={"연월": "조회 월", "해당일관객수": "월별 총 관객수 (명)"},
        text_auto=",.0f",
        hover_data={"연월": True, "해당일관객수": ":,d"}
    )

    fig5.update_layout(
        xaxis_title="월 (YYYY-MM)",
        yaxis_title="월별 총 관객수 (명)",
        xaxis=dict(type="category")
    )

    st.plotly_chart(fig5, use_container_width=True)

    st.info(
        "💡 **이 그래프로 알 수 있는 것:** "
        "월 단위 총 관객수 규모를 직관적으로 비교하여 여름/겨울 방학 및 연말연시 등의 영화 시장 성수기와 "
        "비수기 간의 전체 관객 유입량 차이를 명확히 파악할 수 있습니다."
    )
else:
    st.warning("분석할 박스오피스 데이터가 존재하지 않습니다.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 10. 메인 화면 - 구역 6: 캘린더 히트맵 (주차 x 요일별 일관객수)
# -----------------------------------------------------------------------------
st.header("🗓️ 6. 일별 관객수 캘린더 히트맵")

if not daily_sum_df.empty:
    heatmap_df = daily_sum_df.copy()

    # 1) 요일 이름 및 순서 정의 (월요일 ~ 일요일)
    days_kr = ["월", "화", "수", "목", "금", "토", "일"]
    heatmap_df["요일_num"] = heatmap_df["기준일자"].dt.dayofweek
    heatmap_df["요일"] = heatmap_df["요일_num"].apply(lambda x: days_kr[x])

    # 2) 주차(연-주차) 컬럼 및 날짜 문자열(YYYY-MM-DD) 컬럼 생성
    heatmap_df["연주차"] = heatmap_df["기준일자"].dt.strftime("%Y-W%W")
    heatmap_df["날짜_str"] = heatmap_df["기준일자"].dt.strftime("%Y-%m-%d")

    # 3) 피벗 테이블 생성 (x: 연주차, y: 요일, z: 관객수 / customdata: YYYY-MM-DD)
    pivot_val = heatmap_df.pivot(index="요일", columns="연주차", values="해당일관객수")
    pivot_date = heatmap_df.pivot(index="요일", columns="연주차", values="날짜_str")

    # 4) 화면상 y축 맨 위에 '월요일', 맨 아래에 '일요일'이 오도록 인덱스 순서 재정렬
    # (Plotly Heatmap은 y축 첫 번째 요소를 맨 아래에 그리므로 역순 배치)
    pivot_val = pivot_val.reindex(reversed(days_kr))
    pivot_date = pivot_date.reindex(reversed(days_kr))

    # 5) Plotly 히트맵 생성
    fig6 = go.Figure(
        data=go.Heatmap(
            z=pivot_val.values,
            x=pivot_val.columns,
            y=pivot_val.index,
            customdata=pivot_date.values,
            colorscale="YlOrRd",  # 관객수가 많을수록 붉고 진하게 표시
            hovertemplate="<b>날짜: %{customdata}</b><br>요일: %{y}요일<br>관객수: %{z:,}명<extra></extra>",
            xgap=2,
            ygap=2
        )
    )

    fig6.update_layout(
        title="주차 및 요일별 박스오피스 일관객수 캘린더 히트맵",
        xaxis_title="연도-주차",
        yaxis_title="요일",
        xaxis=dict(type="category")
    )

    st.plotly_chart(fig6, use_container_width=True)

    st.info(
        "💡 **이 그래프로 알 수 있는 것:** "
        "주차별·요일별 관객수 분포를 캘린더 형태로 확인하여, 연중 어떤 주차의 주말/평일에 관객 집중도가 극대화되었는지 "
        "시각적으로 한눈에 비교할 수 있습니다."
    )
else:
    st.warning("분석할 박스오피스 데이터가 존재하지 않습니다.")
