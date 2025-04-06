"""
In an environment with streamlit, plotly, duckdb, and groq installed,
Run with `streamlit run app.py`
"""

import random
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import os
from groq import Groq
from dotenv import load_dotenv

#######################################
# PAGE SETUP
#######################################

st.set_page_config(page_title="AI-Powered Dashboard", page_icon="📊", layout="wide")

st.title("📊 AI-Powered Dashboard Maker")
st.markdown("_Prototype v1.0_")

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_file = st.file_uploader("📂 Upload an Excel file")

if uploaded_file is None:
    st.info("📢 Please upload a file through the sidebar.", icon="ℹ️")
    st.stop()

#######################################
# DATA LOADING
#######################################

@st.cache_data
def load_data(path: str):
    df = pd.read_excel(path)
    return df

df = load_data(uploaded_file)
all_months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

with st.expander("📜 Data Preview"):
    st.dataframe(df)

#######################################
# VISUALIZATION METHODS
#######################################

def plot_metric(label, value, prefix="", suffix="", show_graph=False, color_graph=""):
    fig = go.Figure()

    fig.add_trace(
        go.Indicator(
            value=value,
            gauge={"axis": {"visible": False}},
            number={
                "prefix": prefix,
                "suffix": suffix,
                "font.size": 28,
            },
            title={
                "text": label,
                "font": {"size": 24},
            },
        )
    )

    if show_graph:
        fig.add_trace(
            go.Scatter(
                y=random.sample(range(0, 101), 30),
                hoverinfo="skip",
                fill="tozeroy",
                fillcolor=color_graph,
                line={
                    "color": color_graph,
                },
            )
        )

    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)
    fig.update_layout(
        margin=dict(t=30, b=0),
        showlegend=False,
        plot_bgcolor="white",
        height=100,
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_gauge(indicator_number, indicator_color, indicator_suffix, indicator_title, max_bound):
    fig = go.Figure(
        go.Indicator(
            value=indicator_number,
            mode="gauge+number",
            domain={"x": [0, 1], "y": [0, 1]},
            number={
                "suffix": indicator_suffix,
                "font.size": 26,
            },
            gauge={
                "axis": {"range": [0, max_bound], "tickwidth": 1},
                "bar": {"color": indicator_color},
            },
            title={
                "text": indicator_title,
                "font": {"size": 28},
            },
        )
    )
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=50, b=10, pad=8),
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_top_right():
    sales_data = duckdb.sql(
        f"""
        WITH sales_data AS (
            UNPIVOT (
                SELECT Scenario, business_unit, {','.join(all_months)}
                FROM df 
                WHERE Year='2023' AND Account='Sales'
            ) 
            ON {','.join(all_months)}
            INTO NAME month VALUE sales
        ),
        aggregated_sales AS (
            SELECT Scenario, business_unit, SUM(sales) AS sales
            FROM sales_data
            GROUP BY Scenario, business_unit
        )
        SELECT * FROM aggregated_sales
        """
    ).df()

    fig = px.bar(
        sales_data,
        x="business_unit",
        y="sales",
        color="Scenario",
        barmode="group",
        text_auto=".2s",
        title="📊 Sales for Year 2023",
        height=400,
    )
    fig.update_traces(
        textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
    )
    st.plotly_chart(fig, use_container_width=True)


def plot_bottom_left():
    sales_data = duckdb.sql(
        f"""
        WITH sales_data AS (
            UNPIVOT (
                SELECT Scenario, {','.join(all_months)}
                FROM df 
                WHERE Year='2023' AND Account='Sales' AND business_unit='Software'
            ) 
            ON {','.join(all_months)}
            INTO NAME month VALUE sales
        )
        SELECT * FROM sales_data
        """
    ).df()

    fig = px.line(
        sales_data,
        x="month",
        y="sales",
        color="Scenario",
        markers=True,
        text="sales",
        title="📈 Monthly Budget vs Forecast 2023",
    )
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)


#######################################
# STREAMLIT LAYOUT
#######################################

top_left_column, top_right_column = st.columns((2, 1))
bottom_left_column, bottom_right_column = st.columns(2)

with top_left_column:
    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        plot_metric("Total Revenue", 6621280, prefix="$", show_graph=True, color_graph="rgba(0, 104, 201, 0.2)")
        plot_gauge(1.86, "#0068C9", "%", "Current Ratio", 3)

    with column_2:
        plot_metric("Total Expenses", 1630270, prefix="$", show_graph=True, color_graph="rgba(255, 43, 43, 0.2)")
        plot_gauge(10, "#FF8700", " days", "In Stock", 31)

    with column_3:
        plot_metric("Profit Margin", 75.38, prefix="", suffix=" %")
        
    with column_4:
        plot_metric("Debt Ratio", 1.10, prefix="", suffix=" %")

with top_right_column:
    plot_top_right()

with bottom_left_column:
    plot_bottom_left()

#######################################
# AI-POWERED INSIGHTS
#######################################

st.subheader("🤖 AI-Powered Insights")

# AI Summary of Data
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are an AI-powered financial analyst providing insights on uploaded datasets."},
        {"role": "user", "content": f"Here is a summary of the dataset:\n{df.describe(include='all').to_string()}\nWhat are the key insights?"}
    ],
    model="llama3-8b-8192",
)

st.write(response.choices[0].message.content)



 # AI Chat - Users Can Ask Questions
st.subheader("🗣️ Chat with AI About Your Data")

user_query = st.text_input("🔍 Ask the AI about your dataset:")
if user_query:
     chat_response = client.chat.completions.create(
        messages=[
             {"role": "system", "content": "You are an AI data scientist helping users understand their datasets."},
              {"role": "user", "content": f"Dataset Summary:\n{df.describe(include='all').to_string()}\n{user_query}"}
         ],
         model="llama3-8b-8192",
     )
     st.write(chat_response.choices[0].message.content)
