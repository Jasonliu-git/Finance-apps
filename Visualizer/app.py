import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
st.title("📊 Advanced Data Visualizer – AI-Powered Chart Generator")
st.write("Upload any Excel file, let the AI analyze it, and generate beautiful visualizations!")

# File uploader
uploaded_file = st.file_uploader("📂 Upload your dataset (Excel format)", type=["xlsx"])

if uploaded_file:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)

    # Display data preview
    st.subheader("📊 Data Preview")
    st.dataframe(df.head())

    # AI Analysis: Ask LLM for best chart recommendations
    st.subheader("🤖 AI Chart Recommendation")

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an AI data visualization expert. Given a dataset, recommend the most suitable chart types for visualization."},
            {"role": "user", "content": f"Here is a preview of the dataset:\n{df.describe(include='all').to_string()}\nWhich charts would best visualize this data?"}
        ],
        model="llama3-8b-8192",
    )

    ai_chart_recommendation = response.choices[0].message.content
    st.write(ai_chart_recommendation)

    # User selects a chart based on AI recommendation
    chart_type = st.selectbox("📌 Select a Chart Type to Generate:", [
        "Bar Chart", "Stacked Bar Chart", "Line Chart", "Scatter Plot",
        "Heatmap", "Boxplot", "Pairplot", "Swarmplot", "Histogram",
        "Violin Plot", "Density Plot", "Area Chart", "Pie Chart",
        "Correlation Matrix", "Bubble Chart"
    ])

    # Automatically detect numerical and categorical columns
    numerical_columns = df.select_dtypes(include=['number']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()

    if numerical_columns:
        st.subheader("📊 Generated Visualization")

        if chart_type == "Bar Chart" and categorical_columns:
            plt.figure(figsize=(12, 6))
            sns.barplot(x=categorical_columns[0], y=numerical_columns[0], data=df, palette="coolwarm")
            plt.title(f"Bar Chart: {categorical_columns[0]} vs {numerical_columns[0]}")
            plt.xticks(rotation=45)
            st.pyplot(plt)

        elif chart_type == "Stacked Bar Chart" and categorical_columns:
            plt.figure(figsize=(12, 6))
            df.groupby(categorical_columns[0])[numerical_columns].sum().plot(kind="bar", stacked=True, colormap="coolwarm")
            plt.title(f"Stacked Bar Chart: {categorical_columns[0]}")
            st.pyplot(plt)

        elif chart_type == "Line Chart":
            plt.figure(figsize=(12, 6))
            sns.lineplot(data=df[numerical_columns], palette="viridis", linewidth=2.5)
            plt.title("Line Chart of Numerical Data Over Time")
            st.pyplot(plt)

        elif chart_type == "Scatter Plot" and len(numerical_columns) > 1:
            plt.figure(figsize=(12, 6))
            sns.scatterplot(x=numerical_columns[0], y=numerical_columns[1], data=df, palette="coolwarm", alpha=0.7)
            plt.title(f"Scatter Plot: {numerical_columns[0]} vs {numerical_columns[1]}")
            st.pyplot(plt)

        elif chart_type == "Heatmap" and len(numerical_columns) > 1:
            plt.figure(figsize=(12, 6))
            sns.heatmap(df[numerical_columns].corr(), annot=True, cmap="coolwarm", linewidths=0.5)
            plt.title("Heatmap of Numerical Data Correlations")
            st.pyplot(plt)

        elif chart_type == "Boxplot":
            plt.figure(figsize=(12, 6))
            sns.boxplot(data=df[numerical_columns], palette="coolwarm")
            plt.title("Boxplot of Numerical Data")
            st.pyplot(plt)

        elif chart_type == "Pairplot":
            st.subheader("⏳ Generating Pairplot... This may take a few seconds.")
            sns.pairplot(df[numerical_columns], palette="coolwarm")
            st.pyplot(plt)

        elif chart_type == "Swarmplot" and categorical_columns:
            plt.figure(figsize=(12, 6))
            sns.swarmplot(x=categorical_columns[0], y=numerical_columns[0], data=df, palette="coolwarm")
            plt.title(f"Swarmplot: {categorical_columns[0]} vs {numerical_columns[0]}")
            plt.xticks(rotation=45)
            st.pyplot(plt)

        elif chart_type == "Histogram":
            plt.figure(figsize=(12, 6))
            sns.histplot(df[numerical_columns[0]], bins=30, kde=True, color="blue")
            plt.title(f"Histogram of {numerical_columns[0]}")
            st.pyplot(plt)

        elif chart_type == "Violin Plot":
            plt.figure(figsize=(12, 6))
            sns.violinplot(data=df[numerical_columns], palette="coolwarm")
            plt.title("Violin Plot of Numerical Data")
            st.pyplot(plt)

        elif chart_type == "Density Plot":
            plt.figure(figsize=(12, 6))
            sns.kdeplot(data=df[numerical_columns], palette="coolwarm", fill=True)
            plt.title("Density Plot of Numerical Data")
            st.pyplot(plt)

        elif chart_type == "Area Chart":
            plt.figure(figsize=(12, 6))
            df[numerical_columns].plot.area(alpha=0.4, colormap="coolwarm")
            plt.title("Area Chart of Numerical Data")
            st.pyplot(plt)

        elif chart_type == "Pie Chart" and categorical_columns:
            plt.figure(figsize=(8, 8))
            df[categorical_columns[0]].value_counts().plot.pie(autopct="%1.1f%%", cmap="coolwarm")
            plt.title(f"Pie Chart: {categorical_columns[0]}")
            st.pyplot(plt)

        elif chart_type == "Correlation Matrix" and len(numerical_columns) > 1:
            plt.figure(figsize=(12, 6))
            sns.heatmap(df[numerical_columns].corr(), annot=True, cmap="coolwarm", linewidths=0.5)
            plt.title("Correlation Matrix")
            st.pyplot(plt)

        elif chart_type == "Bubble Chart" and len(numerical_columns) > 2:
            plt.figure(figsize=(12, 6))
            sns.scatterplot(x=numerical_columns[0], y=numerical_columns[1], size=numerical_columns[2], data=df, palette="coolwarm", alpha=0.7)
            plt.title(f"Bubble Chart: {numerical_columns[0]} vs {numerical_columns[1]} (Sized by {numerical_columns[2]})")
            st.pyplot(plt)
    else:
        st.warning("⚠️ No numerical data found for visualization!")
