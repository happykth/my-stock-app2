import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    종목 코드를 입력하면 **원하는 기간의 주가 흐름**을 그래프로 보여드려요.
    두 종목을 나란히 비교할 수도 있어요!  
    예시: `005930.KS` (삼성전자), `AAPL` (애플), `035420.KS` (네이버)
    """
)

st.divider()

# ────────────────────────────────────────────────
# 종목 코드 입력창 2개 (나란히 배치)
# ────────────────────────────────────────────────
input_col1, input_col2 = st.columns(2)

with input_col1:
    ticker_input_1 = st.text_input(
        "🔍 종목 1 코드를 입력해주세요",
        value="005930.KS",
        help="한국 주식은 코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙여주세요. 미국 주식은 코드만 입력하면 돼요.",
    )

with input_col2:
    ticker_input_2 = st.text_input(
        "🔍 종목 2 코드를 입력해주세요 (선택)",
        value="",
        help="비교하고 싶은 두 번째 종목이 있다면 입력해주세요. 비워두면 종목 1만 표시돼요.",
    )

# 입력값 앞뒤 공백 제거 + 대문자로 변환 (사용자가 소문자로 입력해도 잘 동작하도록)
ticker_1 = ticker_input_1.strip().upper()
ticker_2 = ticker_input_2.strip().upper()

st.write("")  # 약간의 여백

# ────────────────────────────────────────────────
# 조회 기간 선택 버튼 (1개월 · 6개월 · 1년 · 5년)
# ────────────────────────────────────────────────
# 세션 상태에 선택된 기간을 저장해서 버튼을 눌러도 값이 유지되게 함
if "selected_period" not in st.session_state:
    st.session_state.selected_period = "1년"

PERIOD_OPTIONS = {
    "1개월": 30,
    "6개월": 182,
    "1년": 365,
    "5년": 365 * 5,
}

st.write("📅 **조회 기간 선택**")
period_cols = st.columns(len(PERIOD_OPTIONS))

for col, period_label in zip(period_cols, PERIOD_OPTIONS.keys()):
    with col:
        # 현재 선택된 기간이면 강조된 버튼(primary)으로 표시
        button_type = "primary" if st.session_state.selected_period == period_label else "secondary"
        if st.button(period_label, use_container_width=True, type=button_type):
            st.session_state.selected_period = period_label

selected_days = PERIOD_OPTIONS[st.session_state.selected_period]

st.divider()

# ────────────────────────────────────────────────
# 데이터 불러오기 함수 (캐시를 사용해서 반복 호출을 줄여줌)
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)  # 1시간 동안 결과를 저장해둠
def load_stock_data(code: str, days: int):
    """yfinance로 지정한 기간만큼 주가 데이터를 가져오는 함수"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    stock = yf.Ticker(code)
    df = stock.history(start=start_date, end=end_date)

    # 회사 이름도 같이 가져와보고, 실패하면 코드 자체를 이름으로 사용
    try:
        company_name = stock.info.get("longName", code)
    except Exception:
        company_name = code

    return df, company_name


def is_korean_ticker(code: str) -> bool:
    """한국 종목 코드인지(.KS, .KQ) 판단하는 함수"""
    return code.endswith(".KS") or code.endswith(".KQ")


def format_price(value: float, korean: bool) -> str:
    """통화 단위에 맞게 가격을 문자열로 포맷팅하는 함수"""
    if korean:
        return f"{value:,.0f} 원"
    return f"${value:,.2f}"


# ────────────────────────────────────────────────
# 한 종목의 데이터를 화면에 표시하는 함수
# (종목 1, 종목 2 모두 이 함수를 재사용함)
# ────────────────────────────────────────────────
def render_stock_section(ticker: str, days: int):
    with st.spinner(f"{ticker} 데이터를 불러오는 중이에요..."):
        try:
            df, company_name = load_stock_data(ticker, days)
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했어요: {e}")
            return

    if df is None or df.empty:
        st.warning("해당 종목의 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요 🙏")
        return

    st.subheader(f"🏢 {company_name} ({ticker})")

    korean = is_korean_ticker(ticker)

    # ── 상단 지표 계산 ──────────────────────────
    current_price = df["Close"].iloc[-1]             # 가장 최근 종가 = 현재가
    start_price = df["Close"].iloc[0]                  # 기간 시작 시점 종가
    price_change = current_price - start_price          # 기간 내 가격 변화
    percent_change = (price_change / start_price) * 100  # 등락률(%)

    top_col1, top_col2 = st.columns(2)
    with top_col1:
        st.metric(label="💰 현재가", value=format_price(current_price, korean))
    with top_col2:
        st.metric(
            label=f"📊 {st.session_state.selected_period} 등락률",
            value=f"{percent_change:+.2f}%",
            delta=format_price(price_change, korean),
        )

    # ── 그래프 ──────────────────────────────────
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
        title=f"{company_name} ({st.session_state.selected_period}) 주가 추이",
        xaxis_title="날짜",
        yaxis_title=f"종가 ({'원' if korean else '$'})",
        template="plotly_white",
        hovermode="x unified",
        height=420,
        font=dict(family="Arial, sans-serif", size=13),
        plot_bgcolor="rgba(255, 250, 245, 0.5)",  # 살짝 따뜻한 배경색
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── 그래프 아래 최고가 · 최저가 · 평균가 카드 ──
    highest_price = df["Close"].max()
    lowest_price = df["Close"].min()
    average_price = df["Close"].mean()

    bottom_col1, bottom_col2, bottom_col3 = st.columns(3)
    with bottom_col1:
        st.metric(label="🔼 최고가", value=format_price(highest_price, korean))
    with bottom_col2:
        st.metric(label="🔽 최저가", value=format_price(lowest_price, korean))
    with bottom_col3:
        st.metric(label="➗ 평균가", value=format_price(average_price, korean))

    # ── 최근 데이터 표 (참고용, 접어두기) ──────
    with st.expander("📋 최근 거래일 데이터 보기"):
        recent_df = df.tail(10)[["Open", "High", "Low", "Close", "Volume"]].copy()
        recent_df.columns = ["시가", "고가", "저가", "종가", "거래량"]
        st.dataframe(recent_df.sort_index(ascending=False), use_container_width=True)


# ────────────────────────────────────────────────
# 두 종목을 하나의 그래프에 겹쳐 그리는 함수
# (단위/통화가 다를 수 있으므로 왼쪽·오른쪽 두 개의 y축을 사용)
# ────────────────────────────────────────────────
def render_comparison_section(ticker_a: str, ticker_b: str, days: int):
    with st.spinner("두 종목 데이터를 불러오는 중이에요..."):
        try:
            df_a, name_a = load_stock_data(ticker_a, days)
        except Exception as e:
            st.error(f"{ticker_a} 데이터를 불러오는 중 오류가 발생했어요: {e}")
            return
        try:
            df_b, name_b = load_stock_data(ticker_b, days)
        except Exception as e:
            st.error(f"{ticker_b} 데이터를 불러오는 중 오류가 발생했어요: {e}")
            return

    if df_a is None or df_a.empty:
        st.warning(f"{ticker_a} 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요 🙏")
        return
    if df_b is None or df_b.empty:
        st.warning(f"{ticker_b} 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요 🙏")
        return

    korean_a = is_korean_ticker(ticker_a)
    korean_b = is_korean_ticker(ticker_b)

    st.subheader(f"🏢 {name_a} ({ticker_a})  vs  🏢 {name_b} ({ticker_b})")

    # ── 하나의 그래프에 두 종목을 겹쳐 그리기 (보조 y축 사용) ──
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df_a.index,
            y=df_a["Close"],
            mode="lines",
            name=f"{name_a} ({'원' if korean_a else '$'})",
            line=dict(color="#FF8C42", width=2.5),  # 따뜻한 주황색
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df_b.index,
            y=df_b["Close"],
            mode="lines",
            name=f"{name_b} ({'원' if korean_b else '$'})",
            line=dict(color="#4A90D9", width=2.5),  # 대비되는 파란색
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"{name_a} vs {name_b} ({st.session_state.selected_period}) 주가 비교",
        xaxis_title="날짜",
        template="plotly_white",
        hovermode="x unified",
        height=480,
        font=dict(family="Arial, sans-serif", size=13),
        plot_bgcolor="rgba(255, 250, 245, 0.5)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_yaxes(title_text=f"{name_a} 종가 ({'원' if korean_a else '$'})", secondary_y=False)
    fig.update_yaxes(title_text=f"{name_b} 종가 ({'원' if korean_b else '$'})", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    # ── 그래프 아래에 두 종목의 지표를 나란히 표시 ──
    metric_col_a, metric_col_b = st.columns(2)

    for col, ticker, df, name, korean in (
        (metric_col_a, ticker_a, df_a, name_a, korean_a),
        (metric_col_b, ticker_b, df_b, name_b, korean_b),
    ):
        with col:
            st.markdown(f"**{name} ({ticker})**")

            current_price = df["Close"].iloc[-1]
            start_price = df["Close"].iloc[0]
            price_change = current_price - start_price
            percent_change = (price_change / start_price) * 100

            st.metric(label="💰 현재가", value=format_price(current_price, korean))
            st.metric(
                label=f"📊 {st.session_state.selected_period} 등락률",
                value=f"{percent_change:+.2f}%",
                delta=format_price(price_change, korean),
            )

            highest_price = df["Close"].max()
            lowest_price = df["Close"].min()
            average_price = df["Close"].mean()

            st.metric(label="🔼 최고가", value=format_price(highest_price, korean))
            st.metric(label="🔽 최저가", value=format_price(lowest_price, korean))
            st.metric(label="➗ 평균가", value=format_price(average_price, korean))


# ────────────────────────────────────────────────
# 메인 로직: 입력된 종목 개수에 따라 화면 구성이 달라짐
# ────────────────────────────────────────────────
if not ticker_1 and not ticker_2:
    st.info("👆 위 입력창에 종목 코드를 입력하면 주가 그래프가 나타나요!")
elif ticker_1 and ticker_2:
    # 두 종목 모두 입력된 경우: 하나의 그래프에 겹쳐서 비교
    render_comparison_section(ticker_1, ticker_2, selected_days)
else:
    # 하나만 입력된 경우: 입력된 종목만 표시
    single_ticker = ticker_1 if ticker_1 else ticker_2
    render_stock_section(single_ticker, selected_days)

# ────────────────────────────────────────────────
# 하단 안내
# ────────────────────────────────────────────────
st.divider()
st.caption("데이터 출처: Yahoo Finance (yfinance) · 투자 판단은 본인 책임이며, 이 앱은 참고용 정보를 제공할 뿐입니다.")
