import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

st.set_page_config(page_title="台股分析 Demo", layout="wide")

# ---------- Helpers ----------
def normalize_symbol(symbol: str) -> str:
    """
    簡單 demo 規則：
    - 如果使用者輸入 2330 -> 2330.TW
    - 若已輸入完整 ticker（如 2330.TW / AAPL）則直接使用
    """
    s = symbol.strip().upper()
    if s.isdigit():
        return f"{s}.TW"
    return s

@st.cache_data(ttl=3600)
def load_price_data(symbol: str, start_date, end_date) -> pd.DataFrame:
    df = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False
    )

    if df is None or df.empty:
        return pd.DataFrame()

    # 避免欄位結構差異
    df = df.copy()
    df.columns = [c if isinstance(c, str) else c[0] for c in df.columns]

    # 技術指標
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["DailyReturnPct"] = df["Close"].pct_change() * 100
    df["Volatility20"] = df["DailyReturnPct"].rolling(20).std()

    df.reset_index(inplace=True)
    return df

def build_chart(df: pd.DataFrame, chart_type: str, show_ma20: bool, show_ma60: bool):
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
                name="Close"
            ),
            row=1, col=1
        )

    if show_ma20:
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["MA20"],
                mode="lines",
                name="MA20"
            ),
            row=1, col=1
        )

    if show_ma60:
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
        height=700,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h")
    )
    return fig

# ---------- Sidebar ----------
st.sidebar.header("設定")
raw_symbol = st.sidebar.text_input("股票代號", value="2330")
symbol = normalize_symbol(raw_symbol)

default_end = date.today()
default_start = default_end - timedelta(days=365)

start_date = st.sidebar.date_input("開始日期", value=default_start)
end_date = st.sidebar.date_input("結束日期", value=default_end)

chart_type = st.sidebar.selectbox("圖表類型", ["K線", "折線"])
show_ma20 = st.sidebar.checkbox("顯示 MA20", value=True)
show_ma60 = st.sidebar.checkbox("顯示 MA60", value=True)

if start_date >= end_date:
    st.error("開始日期必須早於結束日期")
    st.stop()

# ---------- Main ----------
st.title("台股分析 Demo（Streamlit）")
st.caption("教育展示用途：顯示歷史價量、移動平均線、波動概況與資料下載。")

df = load_price_data(symbol, start_date, end_date)

if df.empty:
    st.warning(f"查無資料：{symbol}")
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

col1, col2, col3, col4 = st.columns(4)
col1.metric("最新收盤價", f"{current_close:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
col2.metric("區間報酬率", f"{period_return:+.2f}%")
col3.metric("區間最高 / 最低", f"{period_high:,.2f} / {period_low:,.2f}")
col4.metric("平均成交量", f"{avg_volume:,.0f}")

st.subheader(f"價格走勢：{symbol}")
fig = build_chart(df, chart_type, show_ma20, show_ma60)
st.plotly_chart(fig, use_container_width=True)

st.subheader("快速觀察")
latest_ma20 = latest["MA20"]
latest_ma60 = latest["MA60"]
latest_vol = latest["Volatility20"]

summary = []
summary.append(f"- 最新收盤價：{current_close:,.2f}")
if pd.notna(latest_ma20):
    summary.append(f"- MA20：{latest_ma20:,.2f}")
if pd.notna(latest_ma60):
    summary.append(f"- MA60：{latest_ma60:,.2f}")
if pd.notna(latest_vol):
    summary.append(f"- 20日波動度（以日報酬標準差表示）：{latest_vol:,.2f}")

st.markdown("\n".join(summary))

st.subheader("明細資料")
show_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "MA20", "MA60", "DailyReturnPct", "Volatility20"]
st.dataframe(df[show_cols], use_container_width=True)

csv_data = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="下載 CSV",
    data=csv_data,
    file_name=f"{symbol}_analysis.csv",
    mime="text/csv"
)
