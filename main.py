import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="동네별 인구 피라미드", page_icon="📊", layout="centered"
)

# 데이터 출처 URL
DATA_URL = "https://raw.githubusercontent.com/thswodud/population/main/202609_202609_%EC%97%B0%EB%A0%B9%EB%B3%84%EC%9D%B8%EA%B5%AC%ED%98%84%ED%99%A9_%EC%9B%94%EA%B0%84.csv"


# 캐싱을 사용해 데이터를 매번 새로 불러오지 않도록 로딩
@st.cache_data
def load_data():
    df = None
    # 여러 인코딩 시도 (CP949, EUC-KR, UTF-8-SIG, UTF-8)
    for enc in ["cp949", "euc-kr", "utf-8-sig", "utf-8"]:
        try:
            df = pd.read_csv(DATA_URL, encoding=enc)
            # 공백으로 인한 KeyError 방지를 위해 컬럼명의 양끝 공백 제거
            df.columns = df.columns.str.strip()
            # '연도' 컬럼이 정상 인식되었는지 확인
            if "연도" in df.columns:
                break
        except Exception:
            continue

    if df is None or "연도" not in df.columns:
        # 백업: 인코딩 파싱 실패 시에도 원본을 읽은 뒤 공백 정리
        df = pd.read_csv(DATA_URL, encoding="cp949", engine="python")
        df.columns = df.columns.str.strip()

    return df


# 메인 화면 제목 및 설명
st.title("🏡 우리 동네 인구 피라미드")
st.caption(
    "원하는 동네(시도 ➔ 시군구 ➔ 읍면동)를 선택하여 연령별 남녀 인구 구성을 확인해보세요."
)

# 데이터 로딩
with st.spinner("데이터를 읽어오는 중입니다..."):
    df = load_data()

# 컬럼명에 '연도'가 포함된 대체 컬럼 찾기 (혹시 모를 BOM/특수문자 대응)
year_col = "연도"
if year_col not in df.columns:
    matched = [c for c in df.columns if "연도" in c]
    if matched:
        year_col = matched[0]
    else:
        st.error(
            f"데이터에서 '연도' 열을 찾을 수 없습니다. 현재 인식된 열 목록: {list(df.columns[:5])}"
        )
        st.stop()

# 1. 가장 최신 연도 추출 및 필터링
latest_year = df[year_col].max()
df_latest = df[df[year_col] == latest_year].copy()

st.sidebar.header("📍 지역 선택")

# 2. 계층형 드롭다운 (시도 -> 시군구 -> 동)
sido_col = [c for c in df.columns if "시도" in c][0]
sigungu_col = [c for c in df.columns if "시군구" in c][0]
dong_col = [c for c in df.columns if "동" in c and "시군구" not in c][0]

# (1) 시도 선택
sido_list = sorted(df_latest[sido_col].dropna().unique())
selected_sido = st.sidebar.selectbox("시·도 선택", sido_list)

# (2) 시군구 선택
df_sido = df_latest[df_latest[sido_col] == selected_sido]
sigungu_list = sorted(df_sido[sigungu_col].dropna().unique())
selected_sigungu = st.sidebar.selectbox("시·군·구 선택", sigungu_list)

# (3) 읍면동 선택
df_sigungu = df_sido[df_sido[sigungu_col] == selected_sigungu]
dong_list = sorted(df_sigungu[dong_col].dropna().unique())
selected_dong = st.sidebar.selectbox("읍·면·동 선택", dong_list)

# 선택한 지역의 1개 데이터 행 가져오기
target_data = df_sigungu[df_sigungu[dong_col] == selected_dong].iloc[0]

# 3. 나이 라벨 리스트 생성 (0세 ~ 100세 이상)
age_labels = [f"{i}세" for i in range(100)] + ["100세 이상"]

# 4. 남/여 인구수 추출
male_pop = []
female_pop = []


def safe_int_convert(val):
    """문자열, 콤마(,) 포함 수치를 안전하게 정수로 변환하는 함수"""
    if pd.isna(val):
        return 0
    val_str = str(val).replace(",", "").strip()
    try:
        return int(float(val_str))
    except ValueError:
        return 0


# 실제 데이터 프레임 컬럼 검색용 맵 생성 (공백/특수문자 예외 처리)
col_map = {c.replace(" ", ""): c for c in df.columns}

for age in age_labels:
    m_key = f"남_{age}".replace(" ", "")
    f_key = f"여_{age}".replace(" ", "")

    male_col = col_map.get(m_key, None)
    female_col = col_map.get(f_key, None)

    m_val = target_data[male_col] if male_col and male_col in target_data else 0
    f_val = (
        target_data[female_col] if female_col and female_col in target_data else 0
    )

    male_pop.append(safe_int_convert(m_val))
    female_pop.append(safe_int_convert(f_val))

# 남성 인구수는 왼쪽 배치를 위해 음수로 변환
male_pop_neg = [-val for val in male_pop]

# 5. Plotly 가로 막대그래프 생성
fig = go.Figure()

# (1) 남성 막대그래프
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=male_pop_neg,
        name="남성",
        orientation="h",
        marker=dict(color="#6BAED6"),
        hoverinfo="text",
        text=[f"남성 ({age}): {val:,}명" for age, val in zip(age_labels, male_pop)],
    )
)

# (2) 여성 막대그래프
fig.add_trace(
    go.Bar(
        y=age_labels,
        x=female_pop,
        name="여성",
        orientation="h",
        marker=dict(color="#FC9272"),
        hoverinfo="text",
        text=[
            f"여성 ({age}): {val:,}명" for age, val in zip(age_labels, female_pop)
        ],
    )
)

# 최대 인구수 계산 (X축 대칭용)
max_val = max(max(male_pop), max(female_pop)) if male_pop and female_pop else 100
x_limit = int(max_val * 1.15)

# 6. 레이아웃 및 Y축 순서 고정
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
    # Y축: 0세가 맨 아래, 100세 이상이 맨 위로 순서 고정
    yaxis=dict(
        title="나이",
        type="category",
        categoryorder="array",
        categoryarray=age_labels,
        showgrid=False,
    ),
)

# 차트 출력
st.plotly_chart(fig, use_container_width=True)

# 요약 카드 출력
col1, col2, col3 = st.columns(3)
total_m = sum(male_pop)
total_f = sum(female_pop)
col1.metric("총 남성 인구", f"{total_m:,} 명")
col2.metric("총 여성 인구", f"{total_f:,} 명")
col3.metric("총 인구수", f"{(total_m + total_f):,} 명")
