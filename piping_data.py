
import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import requests
from io import StringIO
from bs4 import BeautifulSoup
from zipfile import ZipFile
import plotly.express as px

# -------------------------------
# STREAMLIT SETUP
# -------------------------------
st.set_page_config(page_title="Universal Data Pipeline", layout="wide")
st.title("🔄 Universal Data Pipeline for Analysts")
st.markdown("""
<style>
.info-card {
    display: flex;
    justify-content: space-around;
    margin-bottom: 20px;
}
.card {
    background-color: #f9f9f9;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
    width: 20%;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# STEP 1: Load Data
# -------------------------------
st.header("📁 Step 1: Upload or Fetch Your Data")
data_source = st.selectbox("Choose your data source", ["Upload File", "Paste JSON", "API Request", "Web Scraping"])
df = pd.DataFrame()

if data_source == "Upload File":
    uploaded_file = st.file_uploader("Upload CSV, Excel, or JSON file", type=["csv", "xlsx", "json"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith(".json"):
            df = pd.read_json(uploaded_file)

elif data_source == "Paste JSON":
    json_data = st.text_area("Paste your JSON data")
    if json_data:
        try:
            df = pd.read_json(StringIO(json_data))
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")

elif data_source == "API Request":
    url = st.text_input("Enter the API endpoint URL")
    if url:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                df = pd.read_json(StringIO(response.text))
                st.success("Data fetched successfully")
            else:
                st.error("API request failed")
        except Exception as e:
            st.error(f"Request failed: {e}")

elif data_source == "Web Scraping":
    page_url = st.text_input("Enter webpage URL to scrape tables")
    if page_url:
        try:
            html = requests.get(page_url).text
            tables = pd.read_html(html)
            table_index = st.number_input("Select table index", 0, len(tables) - 1)
            df = tables[int(table_index)]
        except Exception as e:
            st.error(f"Web scraping failed: {e}")

# -------------------------------
# STEP 2: Understand Data
# -------------------------------
if not df.empty:
    st.header("🔍 Step 2: Understand Your Data")

    domain = st.selectbox("Which field is your data from?", ["Health", "Finance", "Education", "Retail", "Other"])

    num_rows, num_cols = df.shape
    num_nulls = df.isnull().sum().sum()
    num_duplicates = df.duplicated().sum()

    # Horizontal output using HTML + CSS
    st.markdown(f"""
    <div class='info-card'>
        <div class='card'><strong>Rows</strong><br>{num_rows}</div>
        <div class='card'><strong>Columns</strong><br>{num_cols}</div>
        <div class='card'><strong>Total Nulls</strong><br>{num_nulls}</div>
        <div class='card'><strong>Duplicate Rows</strong><br>{num_duplicates}</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📑 Column Preview")
    st.dataframe(df.head())

# -------------------------------
# STEP 3: Clean Data
# -------------------------------
    st.header("🧹 Step 3: Clean Your Data")

    null_strategy = st.selectbox("How should we handle null values?", ["Drop rows", "Forward fill", "Backward fill"])
    dup_strategy = st.selectbox("How should we handle duplicates?", ["Drop duplicates", "Keep all"])

    # Null value handling
    if null_strategy == "Drop rows":
        df = df.dropna()
    elif null_strategy == "Forward fill":
        df = df.ffill()
    elif null_strategy == "Backward fill":
        df = df.bfill()

    # Duplicates handling
    if dup_strategy == "Drop duplicates":
        df = df.drop_duplicates()

    st.success("✅ Data cleaned.")
    st.dataframe(df.head())

    # Download cleaned data
    st.download_button("📥 Download Cleaned Data", df.to_csv(index=False), "cleaned_data.csv")

# -------------------------------
# STEP 4: Visualize Data
# -------------------------------
    st.header("📊 Step 4: Visualize Your Data")

    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    if "plot_count" not in st.session_state:
        st.session_state.plot_count = 0

    if "plotting_done" not in st.session_state:
        st.session_state.plotting_done = False

    if st.button("➕ Add Another Plot"):
        st.session_state.plot_count += 1

    if st.button("✅ Done Plotting"):
        st.session_state.plotting_done = True

    if not st.session_state.plotting_done:
        for i in range(st.session_state.plot_count):
            plot_type = st.selectbox("Choose plot type:", [
                "Histogram", "Box Plot", "Bar Chart (Categorical)", "Scatter Plot", "Line Plot"], key=f"type_{i}")

            if plot_type == "Histogram":
                x_col = st.selectbox("Select numeric column (X):", numeric_cols, key=f"hist_{i}")
                fig = px.histogram(df, x=x_col, title=f"Histogram of {x_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Box Plot":
                y_col = st.selectbox("Select numeric column (Y):", numeric_cols, key=f"box_{i}")
                fig = px.box(df, y=y_col, title=f"Box Plot of {y_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Bar Chart (Categorical)":
                cat_col = st.selectbox("Select categorical column:", categorical_cols, key=f"bar_{i}")
                top_n = st.slider("Top N categories to display:", 5, 30, 10, key=f"topn_{i}")
                counts = df[cat_col].value_counts().head(top_n).reset_index()
                counts.columns = [cat_col, "count"]
                fig = px.bar(counts, x=cat_col, y="count", title=f"Top {top_n} categories in {cat_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Scatter Plot":
                x_col = st.selectbox("Select X-axis (numeric):", numeric_cols, key=f"x_scatter_{i}")
                y_col = st.selectbox("Select Y-axis (numeric):", numeric_cols, key=f"y_scatter_{i}")
                color_col = st.selectbox("Optional: Color by (categorical):", ["None"] + categorical_cols, key=f"color_{i}")
                if color_col != "None":
                    fig = px.scatter(df, x=x_col, y=y_col, color=df[color_col], title=f"{y_col} vs {x_col} by {color_col}")
                else:
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif plot_type == "Line Plot":
                x_col = st.selectbox("Select X-axis:", df.columns, key=f"x_line_{i}")
                y_col = st.selectbox("Select Y-axis (numeric):", numeric_cols, key=f"y_line_{i}")
                fig = px.line(df.sort_values(by=x_col), x=x_col, y=y_col, title=f"{y_col} over {x_col}")
                st.plotly_chart(fig, use_container_width=True)

