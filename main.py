import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 페이지의 제목, 아이콘, 레이아웃을 설정합니다.
st.set_page_config(
    page_title="따뜻한 주식 알리미",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 웹앱 전체의 가독성과 따뜻한 분위기를 연출하기 위한 커스텀 스타일링입니다.
st.markdown("""
<style>
    /* 배경색을 따뜻하고 편안한 미색 톤으로 설정 */
    .stApp {
        background-color: #FAF9F6;
    }
    /* 카드 컴포넌트에 은은한 그림자와 부드러운 테두리 적용 */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #F0EAE1;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }
</style>
""", unsafe_allow_html=True)

# 앱 상단 제목 및 서비스 소개 문구
st.title("📈 한눈에 보는 따뜻한 주식 알리미")
st.markdown("""
궁금한 주식 종목의 **티커 코드**를 입력해 보세요. 
최근 1년 동안의 주가 흐름과 현재 상태를 따뜻하고 보기 쉽게 정리해 드립니다! ✨
""")

st.divider()

# 사용자로부터 주식 종목 코드를 입력받는 검색창입니다.
st.subheader("🔍 종목 검색")
col_input, col_help = st.columns([3, 1])

with col_input:
    # 기본값으로 삼성전자(005930.KS)를 지정합니다.
    ticker_input = st.text_input(
        label="주식 종목 코드를 입력하세요",
        value="005930.KS",
        placeholder="예: 005930.KS, AAPL, TSLA",
        label_visibility="collapsed"
    )

with col_help:
    st.caption("💡 **입력 팁**\n- 한국 코스피: `005930.KS`\n- 한국 코스닥: `068270.KQ`\n- 미국 주식: `AAPL`, `NVDA`")

# 입력된 코드가 있을 때 yfinance로 데이터 조회를 시작합니다.
if ticker_input:
    # 공백 제거 및 대문자 변환
    ticker = ticker_input.strip().upper()
    
    with st.spinner(f"'{ticker}' 데이터를 따뜻하게 가져오는 중입니다... ☕"):
        try:
            # yfinance를 사용하여 해당 종목의 객체를 생성합니다.
            stock_data = yf.Ticker(ticker)
            
            # 최근 1년(1y)간의 일별 데이터를 가져옵니다.
            df = stock_data.history(period="1y")

            # 데이터가 비어 있는지 검사합니다.
            if df.empty:
                st.warning(f"⚠️ **'{ticker}'** 종목의 주가 정보를 찾을 수 없습니다. 종목 코드를 다시 확인해 주세요.")
            else:
                # 최근 종가와 1년 전 첫 거래일 종가를 추출합니다.
                latest_price = df['Close'].iloc[-1]
                first_price = df['Close'].iloc[0]
                
                # 변동 금액 및 변동률(%)을 계산합니다.
                price_change = latest_price - first_price
                percentage_change = (price_change / first_price) * 100

                # 통화 단위 표시 구분 (한국 주식인 경우 원, 외화인 경우 $)
                is_korean = ticker.endswith(".KS") or ticker.endswith(".KQ")
                currency_symbol = "원" if is_korean else "$"
                
                # 금액 포맷팅 (원화는 정수 단위 위주, 달러는 소수점 2자리)
                if is_korean:
                    fmt_latest = f"{latest_price:,.0f}{currency_symbol}"
                    fmt_change = f"{price_change:+,.0f}{currency_symbol}"
                else:
                    fmt_latest = f"{currency_symbol}{latest_price:,.2f}"
                    fmt_change = f"{currency_symbol}{price_change:+,.2f}"

                st.markdown("### 📊 주요 지표")
                m_col1, m_col2, m_col3 = st.columns(3)

                with m_col1:
                    st.metric(
                        label="현재가 (최근 종가)",
                        value=fmt_latest
                    )

                with m_col2:
                    st.metric(
                        label="1년 전 대비 변동 금액",
                        value=fmt_change,
                        delta=fmt_change
                    )

                with m_col3:
                    st.metric(
                        label="1년 등락률",
                        value=f"{percentage_change:+.2f}%",
                        delta=f"{percentage_change:+.2f}%"
                    )

                st.markdown("### 📉 최근 1년 주가 추이")
                
                # Plotly를 활용해 부드럽고 따뜻한 느낌의 라인 차트를 생성합니다.
                fig = go.Figure()

                # 주가 꺾은선 그리기
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df['Close'],
                        mode='lines',
                        name='종가',
                        line=dict(color='#E07A5F', width=2.5), # 따뜻한 테라코타/코랄 오렌지 색상
                        fill='tozeroy',
                        fillcolor='rgba(224, 122, 95, 0.08)', # 아래 영역 은은하게 채우기
                        hovertemplate="<b>날짜</b>: %{x|%Y-%m-%d}<br><b>주가</b>: %{y:,.2f}<extra></extra>"
                    )
                )

                # 그래프 내부 레이아웃 및 디자인 설정
                fig.update_layout(
                    title=dict(
                        text=f"<b>{ticker}</b> 1년 주가 차트",
                        font=dict(size=18, color="#3D405B")
                    ),
                    xaxis=dict(
                        title="날짜",
                        showgrid=True,
                        gridcolor="#F0EAE1",
                        zeroline=False
                    ),
                    yaxis=dict(
                        title=f"주가 ({currency_symbol})",
                        showgrid=True,
                        gridcolor="#F0EAE1",
                        zeroline=False
                    ),
                    hovermode="x unified",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(255,255,255,0.7)",
                    margin=dict(l=20, r=20, t=50, b=20)
                )

                # Streamlit에 Plotly 차트를 출력합니다.
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("🌱 초보자를 위한 작은 도움말"):
                    st.markdown("""
                    - **현재가**: 시장 거래 기준 가장 최근에 마감된 주가(종가)입니다.
                    - **1년 등락률**: 정확히 1년 전 거래일 종가 대비 현재 주가가 몇 % 상승 또는 하락했는지를 보여줍니다.
                    - **차트 활용법**: 마우스를 그래프 위에 올리면 특정 날짜의 정확한 주가를 확인할 수 있습니다.
                    """)

        except Exception as e:
            st.error(f"데이터를 조회하는 중 알 수 없는 오류가 발생했습니다: {e}")

st.divider()
st.caption("💡 본 앱에서 제공하는 정보는 투자 참고용이며, 투자 결과에 대한 책임은 본인에게 있습니다. (출처: Yahoo Finance)")
