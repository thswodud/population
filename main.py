import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정 (타이틀 및 레이아웃)
st.set_page_config(
    page_title="동네별 인구 피라미드", page_icon="📊", layout="centered"
)

# 데이터 출처 URL (GitHub raw 원본 파일 주소)
DATA_URL = "https://raw.githubusercontent.com/thswodud/population/main/202609_202609_%EC%97%B0%EB%A0%B9%EB%B3%84%EC%9D%B8%EA%B5%AC%ED%98%84%ED%99%A9_%EC%9B%94%EA%B0%84.csv"


# 캐싱을 사용해 데이터를 매번 새로 불러오지 않도록 성능 최적화
@st.cache_data
def load_data():
    # CP949(EUC-KR) 또는 UTF-8 인코딩 처리
    try:
        df = pd.read_csv(DATA_URL, encoding="cp949")
    except Exception:
        df = pd.read_csv(DATA_URL, encoding="utf-8")
    return df


# 메인 화면 제목 및 설명
st.title("🏡 우리 동네 인구 피라미드")
st.caption(
    "원하는 동네(시도 ➔ 시군구 ➔ 읍면동)를 선택하여 연령별 남녀 인구 구성을 확인해보세요."
)

# 데이터 로딩 상태 표시
with st.spinner("데이터를 읽어오는 중입니다..."):
    df = load_data()

# 1. 가장 최신 연도 추출 및 필터링
latest_year = df["연도"].max()
df_latest = df[df["연도"] == latest_year].copy()

st.sidebar.header("📍 지역 선택")

# 2. 계층형 드롭다운 (시도 -> 시군구 -> 동)
# (1) 시도 선택
sido_list = sorted(df_latest["시도"].dropna().unique())
selected_sido = st.sidebar.selectbox("시·도 선택", sido_list)

# (2) 선택한 시도에 해당하는 시군구 목록 필터링
df_sido = df_latest[df_latest["시도"] == selected_sido]
sigungu_list = sorted(df_sido["시군구"].dropna().unique())
selected_sigungu = st.sidebar.selectbox("시·군·구 선택", sigungu_list)

# (3) 선택한 시군구에 해당하는 동 목록 필터링
df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]
dong_list = sorted(df_sigungu["동"].dropna().unique())
selected_dong = st.sidebar.selectbox("읍·면·동 선택", dong_list)

# 선택한 지역의 1개 데이터 행 가져오기
target_data = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]

# 3. 나이 라벨 리스트 생성 (0세, 1세, ..., 99세, 100세 이상)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 4. 남/여 인구수 추출
male_pop = []
female_pop = []

for age in age_labels:
    male_col = f"남_{age}"
    female_col = f"여_{age}"

    # 컬럼이 존재할 경우 값 추출 (천단위 콤마나 문자열 예외 처리 포함)
    m_val = target_data.get(male_col, 0)
    f_val = target_data.get(female_col, 0)

    # 숫자로 변환
    male_pop.append(int(str(m_val).replace(",", "")) if pd.notnull(m_val) else 0)
    female_pop.append(
        int(str(f_val).replace(",", "")) if pd.notnull(f_val) else 0
    )

# 남성 인구수는 왼쪽 배치를 위해 음수로 변환
male_pop_neg = [-val for val in male_pop]

# 5. Plotly 가로 막대그래프 생성
fig = go.Figure()

# (1) 남성 막대그래프 (왼쪽 - 음수)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#6BAED6"),  # 포근한 연파랑
        hoverinfo="text",
        text=[f"남성 ({age}): {val:,}명" for age, val in zip(age_labels, male_pop)],
    )
)

# (2) 여성 막대그래프 (오른쪽 - 양수)
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#FC9272"),  # 포근한 연주황/코랄
        hoverinfo="text",
        text=[
            f"여성 ({age}): {val:,}명" for age, val in zip(age_labels, female_pop)
        ],
    )
)

# 최대 인구수 계산 (X축 대칭을 위함)
max_val = max(max(male_pop), max(female_pop)) if male_pop and female_pop else 100
x_limit = int(max_val * 1.15)  # 여유 공간 15% 추가

# 6. 레이아웃 설정 및 세로축 순서 고정
fig.update_layout(
    title=dict(
        text=f"<b>{selected_sido} {selected_sigungu} {selected_dong}</b> 인구 피라미드 ({latest_year}년)",
        font=dict(size=18),
        x=0.5,
        xanchor="center",
    ),
    barmode="overlay",
    bargap=0.1,
    height=850,
    margin=dict(l=60, r=40, t=60, b=40),
    plot_bgcolor="rgba(250,250,250,1)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    # X축 설정: 음수 표기를 양수로 바꾸어 보기 좋게 눈금 설정
    xaxis=dict(
        title="인구수 (명)",
        range=[-x_limit, x_limit],
        tickvals=[-x_limit // 2, 0, x_limit // 2],
        ticktext=[
            f"{abs(x_limit // 2):,}명",
            "0",
            f"{abs(x_limit // 2):,}명",
        ],
        showgrid=True,
        gridcolor="#E0E0E0",
    ),
    # Y축 설정: 나이 라벨을 '0세'부터 '100세 이상' 순서대로 맨 아래에서 위로 고정
    yaxis=dict(
        title="나이",
        type="category",
        categoryorder="array",
        categoryarray=age_labels,  # 0세가 맨 아래, 100세 이상이 맨 위로 배치
        showgrid=False,
    ),
)

# 그래프 화면 출력
st.plotly_chart(fig, use_container_width=True)

# 주요 통계 요약 카드
col1, col2, col3 = st.columns(3)
total_m = sum(male_pop)
total_f = sum(female_pop)
col1.metric("총 남성 인구", f"{total_m:,} 명")
col2.metric("총 여성 인구", f"{total_f:,} 명")
col3.metric("총 인구수", f"{(total_m + total_f):,} 명")
