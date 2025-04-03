import streamlit as st
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key securely
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("🚨 API Key is missing! Set it in Streamlit Secrets or a .env file.")
    st.stop()

# Streamlit UI
st.title("🤖 FP&A Robo Commentator - Automated Financial Insights")
st.write("Upload an Excel file, and our AI-powered FP&A Agent will provide insightful commentary!")

# File uploader
uploaded_file = st.file_uploader("📂 Upload your financial data (Excel format)", type=["xlsx"])

if uploaded_file:
    # Read Excel file
    df = pd.read_excel(uploaded_file)

    # Display raw data
    st.subheader("📊 Uploaded Data Preview")
    st.dataframe(df.head())

    # Data Summary
    st.subheader("📌 Summary of Financial Data")
    summary = df.describe(include='all')
    st.dataframe(summary)

    # Convert dataframe to string for AI processing
    financial_summary = df.describe().to_string()

    # AI Section
    st.subheader("🤖 AI-Generated FP&A Commentary")

    # User Prompt
    user_prompt = st.text_area("📝 Enter specific instructions for AI:", "Analyze the uploaded financial data and provide insights on trends, risks, and opportunities.")

    if st.button("🚀 Generate AI Commentary"):
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an advanced FP&A Robo Commentator that analyzes financial data and provides automated insights."},
                {"role": "user", "content": f"The financial data summary is below:\n{financial_summary}\n{user_prompt}"}
            ],
            model="llama3-8b-8192",
        )

        ai_commentary = response.choices[0].message.content

        # Display AI Commentary
        st.subheader("💡 AI-Generated FP&A Commentary")
        st.write(ai_commentary)
