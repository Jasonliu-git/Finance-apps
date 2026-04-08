import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 頁面設定 ---
st.set_page_config(page_title="台股模擬投資 App", layout="centered")
st.title("📈 台股模擬投資 Demo")

# --- 2. 初始化虛擬帳戶 (使用 Session State) ---
if 'cash' not in st.session_state:
    st.session_state['cash'] = 1000000  # 初始資金 100 萬
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = {}  # 紀錄庫存：{ '2330.TW': {'shares': 1000, 'cost': 750} }

# --- 3. 側邊欄：資產總覽 ---
st.sidebar.header("💰 我的資產")
st.sidebar.metric("可用資金 (TWD)", f"${st.session_state['cash']:,.0f}")

# --- 4. 主畫面：股票查詢與下單 ---
st.subheader("🔍 股票查詢與交易")
# 讓使用者輸入代號，自動補上 .TW
stock_id = st.text_input("請輸入台股代號 (如: 2330, 2317, 2454)", value="2330")
symbol = f"{stock_id}.TW"

if stock_id:
    try:
        # 抓取股價
        ticker = yf.Ticker(symbol)
        current_price = ticker.fast_info['last_price']
        company_name = ticker.info.get('shortName', stock_id)
        
        # 顯示股價 (台灣習慣紅漲綠跌，這裡簡單用 st.metric 呈現)
        st.metric(label=f"{company_name} ({stock_id}) 目前市價", value=f"${current_price:.2f}")
        
        # --- 下單區塊 ---
        with st.form("trade_form"):
            shares_to_buy = st.number_input("買進股數", min_value=1, value=1000, step=100)
            total_cost = shares_to_buy * current_price
            st.write(f"預估總花費: ${total_cost:,.0f}")
            
            submitted = st.form_submit_button("🛒 確認買進")
            
            if submitted:
                if st.session_state['cash'] >= total_cost:
                    # 扣款
                    st.session_state['cash'] -= total_cost
                    # 增加庫存
                    if symbol in st.session_state['portfolio']:
                        st.session_state['portfolio'][symbol]['shares'] += shares_to_buy
                    else:
                        st.session_state['portfolio'][symbol] = {'shares': shares_to_buy, 'cost': current_price}
                    st.success(f"成功買進 {shares_to_buy} 股 {company_name}！")
                    st.experimental_rerun() # 重新整理頁面更新餘額
                else:
                    st.error("❌ 餘額不足！")
    except Exception as e:
        st.warning("找不到該股票或資料讀取失敗，請確認代號。")

# --- 5. 庫存清單 ---
st.subheader("📦 目前庫存")
if st.session_state['portfolio']:
    # 將字典轉換為 DataFrame 方便顯示
    df = pd.DataFrame.from_dict(st.session_state['portfolio'], orient='index')
    df.reset_index(inplace=True)
    df.rename(columns={'index': '股票代號', 'shares': '持有股數', 'cost': '買進成本'}, inplace=True)
    st.dataframe(df)
else:
    st.info("目前沒有任何庫存股票。")
