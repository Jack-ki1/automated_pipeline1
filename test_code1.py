
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
st.title("📊📉FINESE CROSS INDUSTRY ANALYSIS SYSTEM📉")
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
    st.dataframe(df.head(3))
    st.subheader("📑 data Preview")
    st.dataframe(df.info(verbose=True))
    st.subheader("📑 numerical data summary")
    st.dataframe(df.describe())
    st.subheader("📑 count of unique values per column")
    st.dataframe(df.nunique())

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
   # Step 4: Visualization Setup
    st.markdown("### 📊 Data Visualization")

    num_charts = st.number_input("How many plots would you like to generate?", min_value=1, step=1)
    chart_configs = []

    chart_types = ["Bar", "Line", "Scatter", "Histogram", "Box"]

    for i in range(int(num_charts)):
        st.markdown(f"**Chart {i+1} Configuration**")
        chart_type = st.selectbox(f"Select chart type for Chart {i+1}", chart_types, key=f"type_{i}")
        x_axis = st.selectbox(f"Select x-axis for Chart {i+1}", ["None"] + list(df.columns), key=f"x_{i}")
        y_axis = st.selectbox(f"Select y-axis for Chart {i+1}", ["None"] + list(df.columns), key=f"y_{i}")
        color_axis = st.selectbox(f"Optional: Select column for color (Chart {i+1})", ["None"] + list(df.columns), key=f"color_{i}")
        chart_configs.append({"type": chart_type, "x": x_axis, "y": y_axis, "color": color_axis})

    st.markdown("---")
    st.markdown("### 📈 Your Charts")

    # Display charts 2 per row
    for i in range(0, len(chart_configs), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(chart_configs):
                config = chart_configs[i + j]
                with cols[j]:
                    if config['x'] != "None" and config['y'] != "None":
                        if config['type'] == "Bar":
                            fig = px.bar(df, x=config['x'], y=config['y'], color=None if config['color'] == "None" else config['color'])
                        elif config['type'] == "Line":
                            fig = px.line(df, x=config['x'], y=config['y'], color=None if config['color'] == "None" else config['color'])
                        elif config['type'] == "Scatter":
                            fig = px.scatter(df, x=config['x'], y=config['y'], color=None if config['color'] == "None" else config['color'])
                        elif config['type'] == "Histogram":
                            fig = px.histogram(df, x=config['x'], y=config['y'], color=None if config['color'] == "None" else config['color'])
                        elif config['type'] == "Box":
                            fig = px.box(df, x=config['x'], y=config['y'], color=None if config['color'] == "None" else config['color'])
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(f"Chart {i+j+1} skipped: x or y axis not specified.")
else:
    st.warning("Please load your data to proceed.")
