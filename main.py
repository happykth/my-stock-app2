import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ────────────────────────────────────────────────
# 기본 페이지 설정
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="주가 조회 서비스",
    page_icon="📈",
    layout="wide",
)

# ────────────────────────────────────────────────
# 제목과 소개
# ────────────────────────────────────────────────
st.title("📈 우리 동네 주가 조회기")
st.markdown(
    """
    종목 코드를 입력하면 **최근 1년간의 주가 흐름**을 그래프로 보여드려요.  
    예시: `005930.KS` (삼성전자), `AAPL` (애플), `035420.KS` (네이버)
    """
)

st.divider()

# ────────────────────────────────────────────────
# 종목 코드 입력창
# ────────────────────────────────────────────────
ticker_input = st.text_input(
    "🔍 종목 코드를 입력해주세요",
    value="005930.KS",
    help="한국 주식은 코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙여주세요. 미국 주식은 코드만 입력하면 돼요.",
)

# 입력값 앞뒤 공백 제거 + 대문자로 변환 (사용자가 소문자로 입력해도 잘 동작하도록)
ticker = ticker_input.strip().upper()

# ────────────────────────────────────────────────
# 데이터 불러오기 함수 (캐시를 사용해서 반복 호출을 줄여줌)
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)  # 1시간 동안 결과를 저장해둠
def load_stock_data(code: str):
    """yfinance로 최근 1년치 주가 데이터를 가져오는 함수"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    stock = yf.Ticker(code)
    df = stock.history(start=start_date, end=end_date)

    # 회사 이름도 같이 가져와보고, 실패하면 코드 자체를 이름으로 사용
    try:
        company_name = stock.info.get("longName", code)
    except Exception:
        company_name = code

    return df, company_name


# ────────────────────────────────────────────────
# 메인 로직: 종목 코드가 입력되었을 때만 실행
# ────────────────────────────────────────────────
if ticker:
    with st.spinner("주가 데이터를 불러오는 중이에요..."):
        try:
            df, company_name = load_stock_data(ticker)
        except Exception as e:
            df = None
            company_name = None
            st.error(f"데이터를 불러오는 중 오류가 발생했어요: {e}")

    # 데이터가 비어있거나 없으면 안내 메시지 표시
    if df is None or df.empty:
        st.warning("해당 종목의 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요 🙏")
    else:
        st.subheader(f"🏢 {company_name} ({ticker})")

        # ── 지표 계산 ──────────────────────────────
        current_price = df["Close"].iloc[-1]          # 가장 최근 종가 = 현재가
        start_price = df["Close"].iloc[0]              # 1년 전 종가
        price_change = current_price - start_price      # 1년간 가격 변화
        percent_change = (price_change / start_price) * 100  # 등락률(%)

        # 통화 단위 결정: 한국 종목이면 원, 아니면 달러로 표시
        is_korean_stock = ticker.endswith(".KS") or ticker.endswith(".KQ")
        currency_symbol = "원" if is_korean_stock else "$"

        # ── 지표 카드 표시 ─────────────────────────
        col1, col2, col3 = st.columns(3)

        with col1:
            if is_korean_stock:
                st.metric(label="💰 현재가", value=f"{current_price:,.0f} {currency_symbol}")
            else:
                st.metric(label="💰 현재가", value=f"{currency_symbol}{current_price:,.2f}")

        with col2:
            st.metric(
                label="📊 1년 등락률",
                value=f"{percent_change:+.2f}%",
                delta=f"{price_change:+,.0f} {currency_symbol}" if is_korean_stock else f"{currency_symbol}{price_change:+,.2f}",
            )

        with col3:
            highest_price = df["Close"].max()
            lowest_price = df["Close"].min()
            if is_korean_stock:
                st.metric(label="📈 1년 최고/최저", value=f"{highest_price:,.0f} / {lowest_price:,.0f} {currency_symbol}")
            else:
                st.metric(label="📈 1년 최고/최저", value=f"{currency_symbol}{highest_price:,.2f} / {currency_symbol}{lowest_price:,.2f}")

        st.divider()

        # ── Plotly 꺾은선 그래프 ───────────────────
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name="종가",
                line=dict(color="#FF8C42", width=2.5),  # 따뜻한 주황색 라인
                fill="tozeroy",
                fillcolor="rgba(255, 140, 66, 0.1)",  # 은은한 채우기 효과
            )
        )

        fig.update_layout(
            title=f"{company_name} 최근 1년 주가 추이",
            xaxis_title="날짜",
            yaxis_title=f"종가 ({currency_symbol})",
            template="plotly_white",
            hovermode="x unified",
            height=500,
            font=dict(family="Arial, sans-serif", size=13),
            plot_bgcolor="rgba(255, 250, 245, 0.5)",  # 살짝 따뜻한 배경색
        )

        st.plotly_chart(fig, use_container_width=True)

        # ── 최근 데이터 표 (참고용, 접어두기) ──────
        with st.expander("📋 최근 거래일 데이터 보기"):
            recent_df = df.tail(10)[["Open", "High", "Low", "Close", "Volume"]].copy()
            recent_df.columns = ["시가", "고가", "저가", "종가", "거래량"]
            st.dataframe(recent_df.sort_index(ascending=False), use_container_width=True)

else:
    st.info("👆 위 입력창에 종목 코드를 입력하면 주가 그래프가 나타나요!")

# ────────────────────────────────────────────────
# 하단 안내
# ────────────────────────────────────────────────
st.divider()
st.caption("데이터 출처: Yahoo Finance (yfinance) · 투자 판단은 본인 책임이며, 이 앱은 참고용 정보를 제공할 뿐입니다.")
