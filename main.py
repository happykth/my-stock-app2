import streamlit as st
import yfinance as yf
import plotly.graph_objects as go


# ---------------------------------------------------------
# 기본 페이지 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="주식 한눈에 보기",
    page_icon="📈",
    layout="wide",
)


# ---------------------------------------------------------
# 따뜻한 느낌의 간단한 스타일 설정
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF9F3;
    }

    h1, h2, h3 {
        color: #5C4033;
    }

    .description {
        color: #806B5A;
        font-size: 16px;
        margin-bottom: 20px;
    }

    .metric-card {
        background-color: #FFF1E3;
        border: 1px solid #F2D4B7;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }

    .metric-title {
        color: #806B5A;
        font-size: 14px;
        margin-bottom: 6px;
    }

    .metric-value {
        color: #5C4033;
        font-size: 25px;
        font-weight: 700;
    }

    .metric-change {
        font-size: 14px;
        margin-top: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 제목과 설명
# ---------------------------------------------------------
st.title("📈 주식 한눈에 보기")

st.markdown(
    '<div class="description">'
    "종목 코드를 입력하면 최근 1년간의 주가 흐름과 현재가, "
    "1년 등락률을 쉽게 확인할 수 있어요."
    "</div>",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 종목 코드 입력
# ---------------------------------------------------------
ticker = st.text_input(
    "🔎 종목 코드",
    value="005930.KS",
    placeholder="예: 005930.KS (삼성전자), AAPL (애플)",
    help="Yahoo Finance에서 사용하는 종목 코드를 입력하세요.",
).strip()


# ---------------------------------------------------------
# 입력된 종목의 주가 데이터를 가져오는 함수
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def get_stock_data(symbol):
    """
    Yahoo Finance에서 최근 1년간 주가 데이터를 가져옵니다.

    cache_data를 사용하면 같은 종목을 반복해서 조회할 때
    불필요하게 데이터를 다시 다운로드하지 않습니다.
    """

    # yfinance로 최근 1년 데이터를 다운로드합니다.
    data = yf.download(
        symbol,
        period="1y",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    return data


# ---------------------------------------------------------
# 종목 데이터 조회
# ---------------------------------------------------------
if ticker:
    try:
        with st.spinner("주가 데이터를 불러오는 중이에요..."):
            data = get_stock_data(ticker)

        # 데이터를 찾지 못한 경우
        if data.empty:
            st.error(
                "종목 데이터를 찾지 못했어요. "
                "Yahoo Finance에서 사용하는 종목 코드를 확인해 주세요."
            )
            st.stop()

        # -------------------------------------------------
        # yfinance 버전에 따라 컬럼이 MultiIndex일 수 있으므로
        # 종가(Close) 데이터를 안전하게 가져옵니다.
        # -------------------------------------------------
        if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
            close_data = data["Close"]

            # 종목 하나만 조회했으므로 Series 형태로 변환합니다.
            if hasattr(close_data, "columns"):
                close_data = close_data.iloc[:, 0]
        else:
            close_data = data["Close"]

        # 결측값 제거
        close_data = close_data.dropna()

        if close_data.empty:
            st.error("종가 데이터를 가져오지 못했어요.")
            st.stop()

        # -------------------------------------------------
        # 현재가와 1년 전 가격 계산
        # -------------------------------------------------
        current_price = float(close_data.iloc[-1])
        first_price = float(close_data.iloc[0])

        # 1년 등락률 계산
        change_rate = ((current_price - first_price) / first_price) * 100

        # 가격 표시 형식
        price_text = f"{current_price:,.2f}"

        # 등락률에 따라 색상과 아이콘 결정
        if change_rate > 0:
            change_color = "#C65D3B"
            change_icon = "▲"
        elif change_rate < 0:
            change_color = "#4F78A8"
            change_icon = "▼"
        else:
            change_color = "#806B5A"
            change_icon = "—"

        # -------------------------------------------------
        # 지표 카드
        # -------------------------------------------------
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">현재가</div>
                    <div class="metric-value">{price_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">1년 등락률</div>
                    <div class="metric-value" style="color: {change_color};">
                        {change_icon} {change_rate:+.2f}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")

        # -------------------------------------------------
        # 최근 1년 주가 차트
        # -------------------------------------------------
        st.subheader("📊 최근 1년 주가 흐름")

        fig = go.Figure()

        # 꺾은선 그래프 추가
        fig.add_trace(
            go.Scatter(
                x=close_data.index,
                y=close_data.values,
                mode="lines",
                name="종가",
                line=dict(
                    color="#D9825B",
                    width=2.5,
                ),
                hovertemplate="%{x|%Y-%m-%d}<br>"
                "주가: %{y:,.2f}<extra></extra>",
            )
        )

        # 차트 디자인
        fig.update_layout(
            height=500,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="#FFF9F3",
            plot_bgcolor="#FFF9F3",
            hovermode="x unified",
            showlegend=False,
            xaxis=dict(
                title="날짜",
                showgrid=False,
            ),
            yaxis=dict(
                title="주가",
                gridcolor="#F0E1D2",
                zeroline=False,
            ),
            font=dict(
                color="#5C4033",
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        # -------------------------------------------------
        # 간단한 안내 문구
        # -------------------------------------------------
        st.caption(
            "※ 주가는 Yahoo Finance에서 제공하는 데이터를 기준으로 표시됩니다. "
            "실시간 가격과는 차이가 있을 수 있습니다."
        )

    except Exception as e:
        # 예상하지 못한 오류가 발생했을 때 사용자에게 안내합니다.
        st.error(
            "주가 데이터를 불러오는 중 문제가 발생했어요. "
            "종목 코드를 다시 확인해 주세요."
        )

        # 개발자가 오류 원인을 확인할 수 있도록 상세 오류를 접어서 표시합니다.
        with st.expander("오류 상세 보기"):
            st.write(str(e))
