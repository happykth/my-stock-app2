import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ==========================================
# 1. 페이지 기본 설정 및 디자인 (Warm Tone)
# ==========================================
st.set_page_config(
    page_title="주식 주가 조회기",
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
# 2. 헤더 및 입력 영역
# ==========================================
st.title("📈 주식 주가 조회기")
st.write("관심 있는 주식 종목 코드를 입력하면 최근 1년간의 주가 흐름을 한눈에 확인할 수 있습니다.")
st.caption("예시: 삼성전자 (005930.KS), SK하이닉스 (000660.KS), 애플 (AAPL), 테슬라 (TSLA), 엔비디아 (NVDA)")

# 종목 코드 입력창 (기본값: 삼성전자)
ticker_symbol = st.text_input("종목 코드를 입력하세요:", value="005930.KS").strip().upper()

# ==========================================
# 3. 데이터 수집 함수 (캐싱 적용)
# ==========================================
@st.cache_data(ttl=3600)  # 1시간(3600초) 동안 데이터를 캐싱하여 반복 조회를 빠르게 합니다.
def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        # 오늘 날짜 기준으로 정확히 1년 전 날짜 계산
        end_date = datetime.today()
        start_date = end_date - timedelta(days=365)
        
        # 주가 데이터 수집 (일일 종가 기준)
        df = ticker.history(start=start_date, end=end_date)
        
        # 종목 기본 정보 (이름, 통화 단위 등) 수집
        info = ticker.info
        
        return df, info
    except Exception:
        return None, None

# ==========================================
# 4. 주가 데이터 처리 및 화면 출력
# ==========================================
if ticker_symbol:
    # 데이터 로딩 애니메이션 표시
    with st.spinner("주가 데이터를 불러오는 중입니다..."):
        df, info = get_stock_data(ticker_symbol)

    # 데이터가 정상적으로 수집되었는지 확인
    if df is not None and not df.empty:
        # 회사 이름과 통화 단위 추출
        company_name = info.get("shortName", ticker_symbol) if info else ticker_symbol
        currency = info.get("currency", "KRW") if info else "KRW"
        
        # 통화 기호 설정
        currency_symbol = "₩" if currency == "KRW" else "$"

        # 최신 종가 및 1년 전 시작가 계산
        latest_price = df['Close'].iloc[-1]
        first_price = df['Close'].iloc[0]
        
        # 등락 금액 및 등락률 계산
        price_change = latest_price - first_price
        return_rate = (price_change / first_price) * 100

        st.divider()
        st.subheader(f"🔍 {company_name} ({ticker_symbol}) 요약")

        # ----------------------------------
        # 지표 카드 표시 (Metric Cards)
        # ----------------------------------
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="현재가",
                value=f"{currency_symbol} {latest_price:,.0f}" if currency == "KRW" else f"{currency_symbol} {latest_price:,.2f}"
            )
        
        with col2:
            st.metric(
                label="1년 등락률",
                value=f"{return_rate:+.2f}%",
                delta=f"{price_change:+,.0f} {currency}" if currency == "KRW" else f"{price_change:+,.2f} {currency}"
            )
            
        with col3:
            high_price = df['High'].max()
            st.metric(
                label="1년 최고가",
                value=f"{currency_symbol} {high_price:,.0f}" if currency == "KRW" else f"{currency_symbol} {high_price:,.2f}"
            )

        # ----------------------------------
        # Plotly 꺾은선 차트 그리기
        # ----------------------------------
        fig = go.Figure()

        # 주가 추이 선 추가
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Close'],
            mode='lines',
            name='종가',
            line=dict(color='#D97706', width=2.5),  # 따뜻한 앰버/오렌지 색상
            hovertemplate='<b>날짜:</b> %{x|%Y-%m-%d}<br><b>주가:</b> ' + currency_symbol + ' %{y:,.2f}<extra></extra>'
        ))

        # 차트 레이아웃 설정 (따뜻한 크림 톤)
        fig.update_layout(
            title=f"<b>{company_name} 최근 1년 주가 추이</b>",
            title_font=dict(size=18, color="#4A3E3D"),
            xaxis_title="날짜",
            yaxis_title=f"주가 ({currency})",
            paper_bgcolor='#FFFDF9',     # 차트 바깥 영역 배경색
            plot_bgcolor='#FFFBEB',      # 차트 안쪽 영역 배경색
            font=dict(color="#4A3E3D", size=12),
            hovermode="x unified",
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis=dict(showgrid=True, gridcolor='#FDE68A'),  # 연한 황금빛 격자선
            yaxis=dict(showgrid=True, gridcolor='#FDE68A')
        )

        # Streamlit 화면에 Plotly 차트 대화형으로 표시
        st.plotly_chart(fig, use_container_width=True)

    else:
        # 데이터 수집 실패 시 오류 안내
        st.error("⚠️ 주가 데이터를 불러올 수 없습니다. 종목 코드를 다시 확인해 주세요.")
        st.info("💡 **Tip:** 한국 주식은 종목코드 뒤에 **.KS**(코스피) 또는 **.KQ**(코스닥)를 꼭 붙여야 합니다. (예: 삼성전자 → 005930.KS, 카카오 → 035720.KS)")
