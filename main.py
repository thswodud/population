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
selected_dong = st.sidebar.selectbox("읍·면·동 선택", dong
