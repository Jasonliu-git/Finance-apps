import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

st.set_page_config(
    page_title="台股分析 Demo",
    page_icon="📈",
    layout="wide"
)

# ----------------------------
# Helper
# ----------------------------
def normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if s.isdigit():
        return f"{s}.TW"
    return s

def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c if isinstance(c, str) else c[0] for c in df.columns]
    return df

@st.cache_data(ttl=3600)
def load_data_by_range(symbol: str, start_date, end_date) -> pd.DataFrame:
    df = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False
    )
    if df is None or df.empty:
        return pd.DataFrame()

    df = flatten_columns(df)
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["DailyReturnPct"] = df["Close"].pct_change() * 100
    df["Volatility20"] = df["DailyReturnPct"].rolling(20).std()
    df.reset_index(inplace=True)
    return df

@st.cache_data(ttl=3600)
def load_10y_data(symbol: str) -> pd.DataFrame:
    df = yf.download(
        symbol,
        period="10y",
        auto_adjust=False,
        progress=False
    )
    if df is None or df.empty:
        return pd.DataFrame()

    df = flatten_columns(df)
    df["MA60"] = df["Close"].rolling(60).mean()
    df["MA250"] = df["Close"].rolling(250).mean()
    df.reset_index(inplace=True)
    return df

def build_main_chart(df: pd.DataFrame, chart_type: str, show_ma20: bool, show_ma60: bool):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3]
    )

    if chart_type == "K線":
        fig.add_trace(
            go.Candlestick(
                x=df["Date"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="K線"
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name="收盤價"
            ),
            row=1, col=1
        )

    if show_ma20 and "MA20" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MA20"],
                mode="lines",
                name="MA20"
            ),
            row=1, col=1
        )

    if show_ma60 and "MA60" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MA60"],
                mode="lines",
                name="MA60"
            ),
            row=1, col=1
        )

    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="成交量"
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=720,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h")
    )
    return fig

def build_10y_chart(df10: pd.DataFrame):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df10["Date"],
            y=df10["Close"],
            mode="lines",
            name="10年收盤價"
        )
    )

    if "MA60" in df10.columns:
        fig.add_trace(
            go.Scatter(
                x=df10["Date"],
                y=df10["MA60"],
                mode="lines",
                name="MA60"
            )
        )

    if "MA250" in df10.columns:
        fig.add_trace(
            go.Scatter(
                x=df10["Date"],
                y=df10["MA250"],
                mode="lines",
                name="MA250"
            )
        )

    fig.update_layout(
        height=520,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h"),
        title="十年股價走勢"
    )
    return fig

def calc_reference_zone(current_close: float, low_10y: float, high_10y: float):
    """
    教育用途的觀察區間（不是投資建議）：
    - 低檔觀察價：10年區間 25%
    - 中位參考價：10年區間 50%
    - 高檔觀察價：10年區間 75%
    """
    if pd.isna(low_10y) or pd.isna(high_10y) or high_10y <= low_10y:
        return None

    price_range = high_10y - low_10y
    low_zone = low_10y + 0.25 * price_range
    mid_zone = low_10y + 0.50 * price_range
    high_zone = low_10y + 0.75 * price_range
    percentile = ((current_close - low_10y) / price_range) * 100

    if percentile <= 25:
        status = "目前接近十年低檔區（教育用途觀察）"
    elif percentile >= 75:
        status = "目前接近十年高檔區（教育用途觀察）"
    else:
        status = "目前位於十年中間區間（教育用途觀察）"

    return {
        "low_zone": low_zone,
        "mid_zone": mid_zone,
        "high_zone": high_zone,
        "percentile": percentile,
        "status": status
    }

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.header("設定")

preset = st.sidebar.selectbox(
    "股票代號",
    ["2330", "2317", "2454", "2303", "0050", "自訂"]
)

if preset == "自訂":
    raw_symbol = st.sidebar.text_input("輸入股票代號", value="2330")
else:
    raw_symbol = preset

symbol = normalize_symbol(raw_symbol)

today = date.today()
default_start = today - timedelta(days=365)

start_date = st.sidebar.date_input("開始日期", value=default_start)
end_date = st.sidebar.date_input("結束日期", value=today)

chart_type = st.sidebar.selectbox("圖表類型", ["折線", "K線"])
show_ma20 = st.sidebar.checkbox("顯示 MA20", value=True)
show_ma60 = st.sidebar.checkbox("顯示 MA60", value=True)

if start_date >= end_date:
    st.error("開始日期必須早於結束日期")
    st.stop()

# ----------------------------
# Load data
# ----------------------------
df = load_data_by_range(symbol, start_date, end_date)
df10 = load_10y_data(symbol)

st.title("台股分析 Demo")
st.caption("教育展示用途，非投資建議。提供歷史區間、十年高低點與觀察價區間。")

if df.empty:
    st.warning(f"查無區間資料：{symbol}")
    st.stop()

if df10.empty:
    st.warning(f"查無十年資料：{symbol}")
    st.stop()

latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else latest
current_close = latest["Close"]
prev_close = prev["Close"]
change = current_close - prev_close
change_pct = (change / prev_close * 100) if prev_close else 0

period_return = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
period_high = df["High"].max()
period_low = df["Low"].min()
avg_volume = df["Volume"].mean()

high_10y = df10["High"].max()
low_10y = df10["Low"].min()
ref_zone = calc_reference_zone(current_close, low_10y, high_10y)

# ----------------------------
# KPI row 1
# ----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("最新收盤價", f"{current_close:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
c2.metric("區間報酬率", f"{period_return:+.2f}%")
c3.metric("區間最高 / 最低", f"{period_high:,.2f} / {period_low:,.2f}")
c4.metric("平均成交量", f"{avg_volume:,.0f}")

# ----------------------------
# KPI row 2
# ----------------------------
c5, c6, c7, c8 = st.columns(4)
c5.metric("十年最高價", f"{high_10y:,.2f}")
c6.metric("十年最低價", f"{low_10y:,.2f}")

if ref_zone:
    c7.metric("目前位於十年區間", f"{ref_zone['percentile']:.1f}%")
    c8.metric("十年中位參考價", f"{ref_zone['mid_zone']:,.2f}")
else:
    c7.metric("目前位於十年區間", "N/A")
    c8.metric("十年中位參考價", "N/A")

# ----------------------------
# Tabs
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["區間走勢", "十年走勢", "觀察價區間", "明細資料"])

with tab1:
    st.subheader(f"區間走勢：{symbol}")
    fig = build_main_chart(df, chart_type, show_ma20, show_ma60)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"十年股價：{symbol}")
    fig10 = build_10y_chart(df10)
    st.plotly_chart(fig10, use_container_width=True)

    st.markdown("### 十年摘要")
    st.write(f"- 十年最高價：{high_10y:,.2f}")
    st.write(f"- 十年最低價：{low_10y:,.2f}")
    st.write(f"- 目前收盤價：{current_close:,.2f}")

with tab3:
    st.subheader("教育用途觀察價區間（非投資建議）")
    st.info("以下價位僅為依十年高低區間計算出的展示型參考，不構成買賣建議。")

    if ref_zone:
        st.write(f"- 低檔觀察價（10年區間 25%）：{ref_zone['low_zone']:,.2f}")
        st.write(f"- 中位參考價（10年區間 50%）：{ref_zone['mid_zone']:,.2f}")
        st.write(f"- 高檔觀察價（10年區間 75%）：{ref_zone['high_zone']:,.2f}")
        st.write(f"- 目前所在位置：{ref_zone['percentile']:.1f}%")
        st.write(f"- 區間判讀：{ref_zone['status']}")

        zone_df = pd.DataFrame({
            "項目": ["十年最低價", "低檔觀察價", "中位參考價", "高檔觀察價", "十年最高價", "目前收盤價"],
            "價格": [low_10y, ref_zone["low_zone"], ref_zone["mid_zone"], ref_zone["high_zone"], high_10y, current_close]
        })
        st.dataframe(zone_df, use_container_width=True, hide_index=True)
    else:
        st.warning("無法計算觀察價區間。")

with tab4:
    st.subheader("區間明細資料")
    show_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "MA20", "MA60", "DailyReturnPct", "Volatility20"]
    existing_cols = [c for c in show_cols if c in df.columns]
    st.dataframe(df[existing_cols], use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="下載 CSV",
        data=csv_data,
        file_name=f"{symbol}_analysis.csv",
        mime="text/csv"
    )
