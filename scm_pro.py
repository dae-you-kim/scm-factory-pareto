import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px  

# ---------------------------------------------------------
# 1. 페이지 설정 및 디자인
# ---------------------------------------------------------
st.set_page_config(page_title="동국씨엠 재고 최적화 솔루션 Pro", layout="wide")

st.title("🏭 SCM Inventory Master (ABC Analysis)")
st.markdown("""
이 시스템은 다품종 데이터를 분석하여 **ABC 등급(중요도)**을 산출하고, 
등급별로 **차별화된 안전재고 전략**을 제안합니다.
""")

# ---------------------------------------------------------
# 2. 사이드바: 데이터 업로드 & 설정
# ---------------------------------------------------------
st.sidebar.header("📂 데이터 입력")

# 1) 엑셀 파일 업로드 기능 
uploaded_file = st.sidebar.file_uploader("판매 실적 파일 업로드 (Excel/CSV)", type=['xlsx', 'csv'])

# 2) 파일이 없을 때를 대비한 '샘플 데이터 생성' 버튼
if uploaded_file is None:
    st.sidebar.info("파일이 없다면 아래 샘플 생성을 누르세요.")
    if st.sidebar.button("랜덤 샘플 데이터 생성"):
        # 가상의 50개 제품 데이터 생성
        products = [f"Coil-{i:03d}" for i in range(1, 51)]
        sales = np.random.exponential(scale=100, size=50) # 지수분포 (일부는 엄청 많이 팔리고, 대부분은 적게 팔림 - 현실반영)
        df = pd.DataFrame({'제품명': products, '연간판매량': sales})
        df['단가'] = np.random.randint(100, 500, 50) * 10000 # 100~500만원
        df['매출액'] = df['연간판매량'] * df['단가']
    else:
        df = pd.DataFrame() 
else:
    # 업로드된 파일 읽기
    if uploaded_file.name.endswith('csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

# ---------------------------------------------------------
# 3. 메인 로직: ABC 분석 (Pareto Logic)
# ---------------------------------------------------------
if not df.empty:
    st.sidebar.divider()
    st.sidebar.header("⚙️ 전략 설정")
    target_sl_a = st.sidebar.slider("A등급(핵심) 목표 서비스레벨", 0.90, 0.99, 0.99)
    target_sl_c = st.sidebar.slider("C등급(비핵심) 목표 서비스레벨", 0.80, 0.95, 0.90)
    lead_time = st.sidebar.slider("평균 리드타임(일)", 1, 30, 7)

    # (1) ABC 분류 로직 구현
    # 매출액 기준 내림차순 정렬
    df = df.sort_values(by='매출액', ascending=False).reset_index(drop=True)
    
    # 누적 매출 비중 계산
    df['누적매출'] = df['매출액'].cumsum()
    df['누적비중'] = df['누적매출'] / df['매출액'].sum()

    # 등급 매기기 (누적 70%까지 A, 90%까지 B, 나머지 C)
    def classify_abc(percentage):
        if percentage <= 0.7: return 'A'
        elif percentage <= 0.9: return 'B'
        else: return 'C'

    df['등급'] = df['누적비중'].apply(classify_abc)

    # (2) 등급별 안전재고 계산 (차별화 전략)
    # A등급은 (Z값 높게), C등급은 느슨하게
    z_map = {'A': 2.33, 'B': 1.65, 'C': 1.28} # A:99%, B:95%, C:90% (기본값)
    
    # 사용자가 설정한 값으로 덮어쓰기 로직
   
    
    df['변동성(표준편차)'] = df['연간판매량'] * 0.1 # 가상의 변동성 (실무에선 실제 데이터로 계산)
    
    # 함수 매핑 (apply)
    def calc_safety_stock(row):
        if row['등급'] == 'A': z = 2.33 if target_sl_a > 0.98 else 1.65
        elif row['등급'] == 'C': z = 1.28
        else: z = 1.65
        return int(z * row['변동성(표준편차)'] * np.sqrt(lead_time/365)) # 연간데이터라 보정

    df['권장_안전재고'] = df.apply(calc_safety_stock, axis=1)

    # ---------------------------------------------------------
    # 4. 시각화 
    # ---------------------------------------------------------
    
    # [상단] 핵심 KPI
    col1, col2, col3 = st.columns(3)
    a_count = df[df['등급']=='A'].shape[0]
    total_sales = df['매출액'].sum()
    
    col1.metric("총 분석 품목 수", f"{len(df)} 개")
    col2.metric("A등급(핵심) 품목 수", f"{a_count} 개", "전체 매출의 70% 차지")
    col3.metric("총 예상 매출액", f"{total_sales/100000000:.1f} 억원")

    # [중단] 파레토 차트 (Pareto Chart)
    st.subheader("📊 ABC 파레토 분석 차트")
    # Plotly 사용 (확대/축소 됨)
    fig = px.bar(df, x='제품명', y='매출액', color='등급', 
                 title="제품별 매출 기여도 및 등급 분포",
                 color_discrete_map={'A':'red', 'B':'green', 'C':'gray'})
    st.plotly_chart(fig, use_container_width=True)

    # [하단] 상세 데이터 및 다운로드
    st.subheader("📋 등급별 관리 권고안")
    tab1, tab2 = st.tabs(["A등급 (집중관리)", "전체 데이터"])
    
    with tab1:
        st.error("🚨 아래 품목은 품절 시 매출 타격이 큽니다. 일일 재고 점검이 필요합니다.")
        st.dataframe(df[df['등급']=='A'][['제품명', '매출액', '권장_안전재고']])
        
    with tab2:
        st.dataframe(df)

else:
    st.info("👈 왼쪽 사이드바에서 '샘플 데이터 생성' 버튼을 눌러보세요!")