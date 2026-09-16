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
import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.markdown("1년간 박스오피스 10위권에 든 216편 영화의 다양한 지표 분포와 관계를 탐색합니다.")
st.markdown("---")

# -----------------------------------------------------------------------------
# 2. 데이터 불러오기 및 전처리 (캐싱 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_movie_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # [장르 전처리] 세로막대 기호('|')로 여러 장르가 기재된 경우 첫 번째 장르만 추출
    df["genre"] = df["genre"].astype(str).apply(
        lambda x: x.split("|")[0].strip() if pd.notna(x) and x != "nan" else "기타"
    )
    
    # [제작 국가 전처리] 결측치 처리
    df["nation"] = df["nation"].fillna("미상")
    
    # [숫자 데이터 정리] 주요 수치 컬럼들을 정수형으로 변환
    numeric_cols = ["first_scrn", "first_show", "first_week_audi", "total_audi", "days_in_top10"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            
    return df

# 데이터 로딩 실행
df = load_movie_data()

# -----------------------------------------------------------------------------
# 3. 구역 1: 장르별 영화 편수 분포 (도넛 그래프)
# -----------------------------------------------------------------------------
st.header("🍩 1. 장르별 영화 편수 분포")

genre_counts = df["genre"].value_counts().reset_index()
genre_counts.columns = ["장르", "영화편수"]

fig1 = px.pie(
    genre_counts,
    names="장르",
    values="영화편수",
    title="장르별 영화 수 및 비율 분포",
    hole=0.4
)

fig1.update_traces(
    textinfo="percent+label",
    hovertemplate="<b>장르: %{label}</b><br>영화 편수: %{value}편<br>비율: %{percent}<extra></extra>"
)

fig1.update_layout(
    legend_title_text="영화 장르"
)

st.plotly_chart(fig1, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "최근 1년간 박스오피스 상위권에 진입한 영화 중 어떤 장르가 가장 큰 비중을 차지하는지 장르별 편수와 제작 비율을 한눈에 파악할 수 있습니다."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 4. 구역 2: 장르 및 영화별 총 관객수 분포 (트리맵)
# -----------------------------------------------------------------------------
st.header("🗺️ 2. 장르 및 영화별 총 관객수 트리맵")

fig2 = px.treemap(
    df,
    path=[px.Constant("전체 영화"), "genre", "movieNm"],
    values="total_audi",
    color="genre",
    title="장르 및 영화별 총 관객수 비중 (칸 크기 = 총 관객수)"
)

fig2.update_traces(
    hovertemplate="<b>%{label}</b><br>총 관객수: %{value:,}명<extra></extra>"
)

fig2.update_layout(
    margin=dict(t=50, l=25, r=25, b=25)
)

st.plotly_chart(fig2, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "전체 영화 시장에서 각 장르가 차지하는 관객 규모 비중과 함께, 장르 내에서 어떤 영화가 흥행을 주도했는지 상대적인 관객수 크기를 한눈에 비교할 수 있습니다."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 구역 3: 총 관객수 분포 (히스토그램)
# -----------------------------------------------------------------------------
st.header("📊 3. 총 관객수 히스토그램")

fig3 = px.histogram(
    df,
    x="total_audi",
    nbins=30,
    title="영화별 총 관객수 구간 분포",
    labels={"total_audi": "총 관객수 (명)"},
    color_discrete_sequence=["#636EFA"]
)

fig3.update_traces(
    hovertemplate="총 관객수 구간: %{x:,}명<br>영화 수: %{y}편<extra></extra>"
)

fig3.update_layout(
    xaxis_title="총 관객수 (명)",
    yaxis_title="영화 수 (편)",
    bargap=0.1
)

st.plotly_chart(fig3, use_container_width=True)

max_row = df.loc[df["total_audi"].idxmax()]
max_movie_name = max_row["movieNm"]
max_movie_audi = int(max_row["total_audi"])

under_1m_cnt = (df["total_audi"] < 1000000).sum()
total_cnt = len(df)
under_1m_pct = (under_1m_cnt / total_cnt) * 100

st.info(
    f"💡 **이 그래프로 알 수 있는 것:** "
    f"전체 {total_cnt}편 중 대다수인 {under_1m_cnt}편(약 {under_1m_pct:.1f}%)이 **관객수 100만 명 미만 구간**에 집중되어 있어 극심한 흥행 쏠림 현상을 보여줍니다. "
    f"가장 많은 관객을 모은 최고 흥행작은 **'{max_movie_name}'**(총 {max_movie_audi:,}명)입니다."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 구역 4: 개봉일 스크린수와 총 관객수의 관계 (산점도)
# -----------------------------------------------------------------------------
st.header("🎯 4. 개봉일 스크린수 vs 총 관객수 산점도")

fig4 = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    title="개봉일 스크린수와 총 관객수 간의 관계",
    labels={
        "first_scrn": "개봉일 스크린수 (개)",
        "total_audi": "총 관객수 (명)",
        "genre": "장르",
        "movieNm": "영화명"
    },
    hover_data={
        "first_scrn": ":,d",
        "total_audi": ":,d",
        "genre": True
    }
)

fig4.update_traces(marker=dict(size=9, opacity=0.8))

fig4.update_layout(
    xaxis_title="개봉일 스크린수 (개)",
    yaxis_title="총 관객수 (명)",
    legend_title_text="장르"
)

st.plotly_chart(fig4, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "개봉일 확보한 스크린수가 많을수록 최종 총 관객수도 함께 증가하는 전반적인 양의 상관관계를 볼 수 있으며, "
    "스크린 수 대비 상대적으로 높은 흥행 실적을 거둔 이례적 성과 영화나 그 반대의 사례를 장르별로 쉽게 식별할 수 있습니다."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 구역 5: 영화 10편 이상 장르별 총 관객수 분포 (박스플롯)
# -----------------------------------------------------------------------------
st.header("📦 5. 주요 장르별 총 관객수 박스플롯")

genre_counts_series = df["genre"].value_counts()
valid_genres = genre_counts_series[genre_counts_series >= 10].index
box_df = df[df["genre"].isin(valid_genres)]

fig5 = px.box(
    box_df,
    x="genre",
    y="total_audi",
    color="genre",
    hover_name="movieNm",
    points="outliers",
    title="영화 10편 이상 장르별 총 관객수 분포 및 이상치 비교",
    labels={
        "genre": "장르",
        "total_audi": "총 관객수 (명)",
        "movieNm": "영화명"
    },
    hover_data={
        "total_audi": ":,d",
        "genre": False
    }
)

fig5.update_layout(
    xaxis_title="장르 (10편 이상 등재)",
    yaxis_title="총 관객수 (명)",
    showlegend=False
)

st.plotly_chart(fig5, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "영화 제작 편수가 10편 이상인 주요 장르 간 관객수 중앙값과 스펙트럼 범위를 비교할 수 있으며, "
    "장르별 일반적인 범위를 뛰어넘어 압도적 흥행 대박을 터뜨린 점(이상치)의 영화가 무엇인지 명확하게 파악할 수 있습니다."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 8. 구역 6: 개봉일 스크린수 vs 총 관객수 vs 첫 주 관객수 (버블 차트)
# -----------------------------------------------------------------------------
st.header("🫧 6. 스크린수·총 관객수·첫 주 관객수 입체 비교 (버블 차트)")

fig6 = px.scatter(
    df,
    x="first_scrn",
    y="total_audi",
    size="first_week_audi",
    color="genre",
    hover_name="movieNm",
    size_max=45,
    title="개봉일 스크린수 vs 총 관객수 (버블 크기 = 개봉 첫 주 관객수)",
    labels={
        "first_scrn": "개봉일 스크린수 (개)",
        "total_audi": "총 관객수 (명)",
        "first_week_audi": "개봉 첫 주 관객수 (명)",
        "genre": "장르",
        "movieNm": "영화명"
    },
    hover_data={
        "first_scrn": ":,d",
        "total_audi": ":,d",
        "first_week_audi": ":,d",
        "genre": True
    }
)

fig6.update_traces(marker=dict(opacity=0.75))

fig6.update_layout(
    xaxis_title="개봉일 스크린수 (개)",
    yaxis_title="총 관객수 (명)",
    legend_title_text="장르"
)

st.plotly_chart(fig6, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "스크린수와 총 관객수의 관계 위에 '개봉 첫 주 관객수(버블 크기)' 지표를 결합하여, "
    "초반 입소문이나 개봉 첫 주 기선 제압(초반 흥행 화력)이 최종 총 관객수 형성에 어느 정도 기여했는지 다차원적으로 비교 분석할 수 있습니다."
)

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. 구역 7: 제작 국가 및 장르별 영화 편수 (선버스트 차트)
# -----------------------------------------------------------------------------
st.header("☀️ 7. 제작 국가 및 장르별 영화 편수 선버스트 차트")

# 제작 국가 -> 장르 계층별 영화 편수 집계
nation_genre_df = df.groupby(["nation", "genre"]).size().reset_index(name="영화편수")

fig7 = px.sunburst(
    nation_genre_df,
    path=["nation", "genre"],
    values="영화편수",
    color="nation",
    title="제작 국가 및 장르별 영화 편수 분포 (칸 크기 = 영화 편수)"
)

fig7.update_traces(
    hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<extra></extra>"
)

fig7.update_layout(
    margin=dict(t=50, l=25, r=25, b=25)
)

st.plotly_chart(fig7, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "제작 국가별 전체 영화 편수 점유율과 함께, 각 국가 안에서 어떤 장르의 영화가 주로 제작·개봉되었는지 다층 계층 구조(선버스트)를 통해 한눈에 파악할 수 있습니다."
)
# -----------------------------------------------------------------------------
# 10. 구역 8: 장르별 TOP 10 유지 일수(흥행 지속력) 비교
# -----------------------------------------------------------------------------
st.header("⏳ 8. 장르별 TOP 10 유지 일수(흥행 지속력) 비교")

fig8 = px.box(
    df,
    x="genre",
    y="days_in_top10",
    color="genre",
    hover_name="movieNm",
    points="all",
    title="장르별 TOP 10 진입 유지 일수 분포",
    labels={
        "genre": "장르",
        "days_in_top10": "10위권 유지 일수 (일)",
        "movieNm": "영화명"
    }
)

fig8.update_layout(
    xaxis_title="장르",
    yaxis_title="10위권 유지 일수 (일)",
    showlegend=False
)

st.plotly_chart(fig8, use_container_width=True)

st.info(
    "💡 **이 그래프로 알 수 있는 것:** "
    "각 장르별로 박스오피스 상위 10위권에 머문 날수(days_in_top10)의 중앙값과 편차를 비교하여, 어떤 장르가 단발성 흥행에 그치지 않고 장기간 순위를 유지했는지 한눈에 확인할 수 있습니다."
)
