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

# Streamlit App UI
st.set_page_config(page_title="Smart Excel Merger AI", page_icon="📊", layout="wide")
st.title("📊 Smart Excel Merger AI – AI-Powered File Merging")
st.write("Upload multiple Excel files, and let the AI help you merge them!")

# File uploader
uploaded_files = st.file_uploader("📂 Upload your Excel files (at least 2)", type=["xlsx"], accept_multiple_files=True)

if len(uploaded_files) < 2:
    st.warning("⚠️ Please upload at least two Excel files to merge.")
    st.stop()

# Load all Excel files into Pandas DataFrames
dfs = {file.name: pd.read_excel(file) for file in uploaded_files}

# Display file previews
st.subheader("📂 Uploaded File Previews")
for filename, df in dfs.items():
    st.write(f"**{filename}**")
    st.dataframe(df.head())

# AI Section
st.subheader("🤖 AI-Powered Merge Guidance")

# AI Summary of Data
client = Groq(api_key=GROQ_API_KEY)
merge_instructions = st.text_area("📝 Describe how you want to merge these files:", "Merge by common columns, or append them.")

response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are an AI assistant that helps users merge Excel files."},
        {"role": "user", "content": f"Here are the datasets:\n{', '.join(dfs.keys())}\nUser instructions: {merge_instructions}\nHow should we merge these files?"}
    ],
    model="llama3-8b-8192",
)

ai_guidance = response.choices[0].message.content
st.write(ai_guidance)

# **Choose Merge Type Based on AI Guidance**
merge_type = st.selectbox("📌 Select Merge Type:", ["Merge by Common Columns", "Append Rows", "Custom Merge"])

if st.button("🚀 Merge Files"):
    try:
        if merge_type == "Merge by Common Columns":
            # Find common columns across all files
            common_cols = set.intersection(*(set(df.columns) for df in dfs.values()))
            if not common_cols:
                st.error("⚠️ No common columns found for merging. Please use a different merge method.")
                st.stop()
            merged_df = pd.concat([df.set_index(list(common_cols)) for df in dfs.values()], axis=1).reset_index()

        elif merge_type == "Append Rows":
            merged_df = pd.concat(dfs.values(), ignore_index=True)

        elif merge_type == "Custom Merge":
            custom_column = st.text_input("Enter the column name to merge on:")
            if custom_column not in dfs[list(dfs.keys())[0]].columns:
                st.error("⚠️ The entered column does not exist in all files. Check spelling or try another method.")
                st.stop()
            merged_df = dfs[list(dfs.keys())[0]]
            for df in list(dfs.values())[1:]:
                merged_df = merged_df.merge(df, on=custom_column, how="outer")

        # Display Merged Data
        st.subheader("📊 Merged Data Preview")
        st.dataframe(merged_df.head())

        # Download Merged File
        output_file = "merged_excel.xlsx"
        merged_df.to_excel(output_file, index=False)
        st.download_button(label="📥 Download Merged File", data=open(output_file, "rb"), file_name="merged_data.xlsx")

    except Exception as e:
        st.error(f"⚠️ Error merging files: {e}")
