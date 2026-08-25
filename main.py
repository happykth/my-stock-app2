import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. 페이지 기본 설정 및 디자인 (Warm Tone)
# ==========================================
st.set_page_config(
    page_title="주식 주가 비교 조회기",
    page_icon="📈",
    layout="wide"
)

# 따뜻한 크림/황금색 톤의 커스텀 CSS 스타일 적용
st.markdown("""
    <style>
    /* 전체 배경을 따뜻한 크림톤으로 설정 */
    .stApp {
        background-color: #FFFDF9;
    }
    /* 지표 카드(Metric) 스타일링 */
    div[data-testid="stMetric"] {
        background-color: #FFF9E6;
        border: 1px solid #FFE494;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 헤더 영역
# ==========================================
st.title("📈 주식 주가 비교 조회기")
st.write("두 개의 관심 종목을 입력하고 원하는 기간별 주가 흐름과 상세 통계를 비교해 보세요.")
st.caption("예시: 삼성전자 (005930.KS), SK하이닉스 (000660.KS), 애플 (AAPL), 테슬라 (TSLA), 엔비디아 (NVDA)")

# ==========================================
# 3. 데이터 수집 함수 (캐싱 적용)
# ==========================================
@st.cache_data(ttl=3600)  # 1시간 동안 데이터를 캐싱
def get_stock_data(symbol, period_days):
    try:
        ticker = yf.Ticker(symbol)
        
        # 선택한 기간에 따른 시작일/종료일 계산
        end_date = datetime.today()
        start_date = end_date - timedelta(days=period_days)
        
        # 주가 데이터 수집 (일일 종가 기준)
        df = ticker.history(start=start_date, end=end_date)
        
        # 종목 기본 정보 (이름, 통화 단위 등) 수집
        info = ticker.info
        
        return df, info
    except Exception:
        return None, None

# ==========================================
# 4. 사용자 입력 영역 (종목 입력 & 기간 선택)
# ==========================================
st.subheader("⚙️ 검색 및 옵션 설정")

# 4-1. 종목 입력창 (2개 입력 가능하도록 컬럼 분할)
col_input1, col_input2 = st.columns(2)

with col_input1:
    ticker_symbol1 = st.text_input("첫 번째 종목 코드 (주황색)", value="005930.KS").strip().upper()

with col_input2:
    ticker_symbol2 = st.text_input("두 번째 종목 코드 (비교용 / 선택)", value="AAPL").strip().upper()

# 4-2. 기간 선택 버튼 (라디오 버튼)
period_options = {
    "1개월": 30,
    "6개월": 180,
    "1년": 365,
    "5년": 365 * 5
}

selected_period_label = st.radio(
    "조회 기간을 선택하세요:",
    options=list(period_options.keys()),
    index=2,  # 기본값: '1년'
    horizontal=True
)

selected_days = period_options[selected_period_label]

st.divider()

# ==========================================
# 5. 데이터 불러오기 및 차트/통계 출력
# ==========================================
if ticker_symbol1:
    with st.spinner("주가 데이터를 불러오는 중입니다..."):
        # 첫 번째 종목 데이터 가져오기
        df1, info1 = get_stock_data(ticker_symbol1, selected_days)
        
        # 두 번째 종목 데이터 가져오기 (입력했을 때만)
        df2, info2 = get_stock_data(ticker_symbol2, selected_days) if ticker_symbol2 else (None, None)

    # 첫 번째 종목 데이터 확인
    if df1 is not None and not df1.empty:
        # 종목 1 정보 정리
        name1 = info1.get("shortName", ticker_symbol1) if info1 else ticker_symbol1
        currency1 = info1.get("currency", "KRW") if info1 else "KRW"
        sym1 = "₩" if currency1 == "KRW" else "$"

        # 종목 1 지표 계산
        latest1 = df1['Close'].iloc[-1]
        first1 = df1['Close'].iloc[0]
        change1 = latest1 - first1
        rate1 = (change1 / first1) * 100

        # 종목 2 정보 및 지표 계산 (존재할 경우)
        has_symbol2 = df2 is not None and not df2.empty
        if has_symbol2:
            name2 = info2.get("shortName", ticker_symbol2) if info2 else ticker_symbol2
            currency2 = info2.get("currency", "KRW") if info2 else "KRW"
            sym2 = "₩" if currency2 == "KRW" else "$"

            latest2 = df2['Close'].iloc[-1]
            first2 = df2['Close'].iloc[0]
            change2 = latest2 - first2
            rate2 = (change2 / first2) * 100

        # ----------------------------------
        # 5-1. 상단 요약 카드로 현재가 및 등락률 출력
        # ----------------------------------
        st.subheader("📌 요약 정보")
        m_col1, m_col2 = st.columns(2)

        with m_col1:
            st.markdown(f"**🟠 {name1} ({ticker_symbol1})**")
            st.metric(
                label=f"현재가 ({selected_period_label} 등락률)",
                value=f"{sym1} {latest1:,.0f}" if currency1 == "KRW" else f"{sym1} {latest1:,.2f}",
                delta=f"{rate1:+.2f}%"
            )

        with m_col2:
            if has_symbol2:
                st.markdown(f"**🔵 {name2} ({ticker_symbol2})**")
                st.metric(
                    label=f"현재가 ({selected_period_label} 등락률)",
                    value=f"{sym2} {latest2:,.0f}" if currency2 == "KRW" else f"{sym2} {latest2:,.2f}",
                    delta=f"{rate2:+.2f}%"
                )
            elif ticker_symbol2:
                st.warning(f"⚠️ '{ticker_symbol2}' 종목 데이터를 찾을 수 없습니다.")

        # ----------------------------------
        # 5-2. Plotly 꺾은선 차트 (2개 종목 나란히)
        # ----------------------------------
        fig = go.Figure()

        # 종목 1 트레이스 추가
        fig.add_trace(go.Scatter(
            x=df1.index,
            y=df1['Close'],
            mode='lines',
            name=f"{name1} ({currency1})",
            line=dict(color='#D97706', width=2.5),  # 따뜻한 앰버/오렌지색
            hovertemplate='<b>' + name1 + '</b><br>날짜: %{x|%Y-%m-%d}<br>주가: ' + sym1 + ' %{y:,.2f}<extra></extra>'
        ))

        # 종목 2 트레이스 추가 (있을 경우)
        if has_symbol2:
            fig.add_trace(go.Scatter(
                x=df2.index,
                y=df2['Close'],
                mode='lines',
                name=f"{name2} ({currency2})",
                line=dict(color='#2563EB', width=2.5),  # 대비되는 선명한 블루
                yaxis='y2' if currency1 != currency2 else 'y', # 통화가 다르면 보조 축(Y2) 사용
                hovertemplate='<b>' + name2 + '</b><br>날짜: %{x|%Y-%m-%d}<br>주가: ' + sym2 + ' %{y:,.2f}<extra></extra>'
            ))

        # 차트 레이아웃 및 축 설정
        layout_args = dict(
            title=f"<b>주가 추이 비교 ({selected_period_label})</b>",
            title_font=dict(size=18, color="#4A3E3D"),
            xaxis_title="날짜",
            yaxis_title=f"{name1} 주가 ({currency1})",
            paper_bgcolor='#FFFDF9',
            plot_bgcolor='#FFFBEB',
            font=dict(color="#4A3E3D", size=12),
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(showgrid=True, gridcolor='#FDE68A'),
            yaxis=dict(showgrid=True, gridcolor='#FDE68A'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # 두 종목의 통화가 다를 경우 보조 축(Y2) 스타일 추가 설정
        if has_symbol2 and currency1 != currency2:
            layout_args['yaxis2'] = dict(
                title=f"{name2} 주가 ({currency2})",
                overlaying='y',
                side='right',
                showgrid=False
            )

        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)

        # ----------------------------------
        # 5-3. 그래프 하단 상세 통계 카드 (최고가/최저가/평균가)
        # ----------------------------------
        st.subheader(f"📊 {selected_period_label} 기간 상세 통계")

        stat_col1, stat_col2 = st.columns(2)

        # 종목 1 상세 통계 카드
        with stat_col1:
            st.markdown(f"#### 🟠 {name1}")
            high1 = df1['High'].max()
            low1 = df1['Low'].min()
            avg1 = df1['Close'].mean()

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.metric("최고가", f"{sym1} {high1:,.0f}" if currency1 == "KRW" else f"{sym1} {high1:,.2f}")
            with sc2:
                st.metric("최저가", f"{sym1} {low1:,.0f}" if currency1 == "KRW" else f"{sym1} {low1:,.2f}")
            with sc3:
                st.metric("평균가", f"{sym1} {avg1:,.0f}" if currency1 == "KRW" else f"{sym1} {avg1:,.2f}")

        # 종목 2 상세 통계 카드 (존재할 경우)
        with stat_col2:
            if has_symbol2:
                st.markdown(f"#### 🔵 {name2}")
                high2 = df2['High'].max()
                low2 = df2['Low'].min()
                avg2 = df2['Close'].mean()

                sc4, sc5, sc6 = st.columns(3)
                with sc4:
                    st.metric("최고가", f"{sym2} {high2:,.0f}" if currency2 == "KRW" else f"{sym2} {high2:,.2f}")
                with sc5:
                    st.metric("최저가", f"{sym2} {low2:,.0f}" if currency2 == "KRW" else f"{sym2} {low2:,.2f}")
                with sc6:
                    st.metric("평균가", f"{sym2} {avg2:,.0f}" if currency2 == "KRW" else f"{sym2} {avg2:,.2f}")

    else:
        st.error(f"⚠️ '{ticker_symbol1}' 종목 데이터를 불러올 수 없습니다. 코드를 올바르게 입력했는지 확인해 주세요.")
        st.info("💡 **Tip:** 한국 주식은 종목코드 뒤에 **.KS**(코스피) 또는 **.KQ**(코스닥)를 붙여야 합니다. (예: 삼성전자 → 005930.KS, 카카오 → 035720.KS)")
