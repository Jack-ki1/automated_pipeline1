
import streamlit as st
import pandas as pd
import json
import os
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Streamlit App Configuration
st.set_page_config(page_title="Data Pipeline Dashboard", layout="wide")
st.title("📊 Data Pipeline Dashboard")

# Step 1: Get Data Source Type
source_type = st.selectbox("Select data source type", ["CSV", "Excel", "JSON", "TSV", "API", "SQL Database", "Cloud Storage", "Web Scraping"])

def load_data():
    if source_type in ["CSV", "Excel", "JSON", "TSV"]:
        file = st.file_uploader(f"Upload your {source_type} file", type=["csv", "xlsx", "json", "tsv"])
        if file is not None:
            if source_type == "CSV":
                return pd.read_csv(file)
            elif source_type == "Excel":
                return pd.read_excel(file)
            elif source_type == "JSON":
                return pd.read_json(file)
            elif source_type == "TSV":
                return pd.read_csv(file, sep='	')

    elif source_type == "API":
        api_url = st.text_input("Enter API URL")
        if api_url:
            response = requests.get(api_url)
            if response.status_code == 200:
                return pd.DataFrame(response.json())
            else:
                st.error("Failed to fetch data from API")

    elif source_type == "SQL Database":
        st.info("This feature requires SQLAlchemy or similar library. To be implemented if needed.")

    elif source_type == "Cloud Storage":
        st.warning("Cloud Storage fetch skipped - please install required SDK like boto3 for AWS.")

    elif source_type == "Web Scraping":
        st.info("Basic scraping logic. Input URL and tag.")
        from bs4 import BeautifulSoup
        scrape_url = st.text_input("Enter website URL")
        tag = st.text_input("Enter HTML tag to scrape", value="p")
        if scrape_url and tag:
            page = requests.get(scrape_url)
            soup = BeautifulSoup(page.content, "html.parser")
            data = [element.text for element in soup.find_all(tag)]
            return pd.DataFrame(data, columns=["Scraped Data"])
    return None

df = load_data()

if df is not None:
    st.success("Data Loaded Successfully")

    # Step 2: Understand Data Type
    domain = st.selectbox("Which domain does your data belong to?", ["Health", "Finance", "Education", "Marketing", "Other"])
    st.markdown("### Dataset Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Shape of Data:**", df.shape)
    with col2:
        st.write("**Column Names:**", list(df.columns))
    with col3:
        st.write("**Data Types:**")
        st.dataframe(df.dtypes)

    # Step 3: Data Cleaning
    st.markdown("### 🧹 Data Cleaning")

    if df.duplicated().any():
        dup_action = st.selectbox("Duplicates found. What would you like to do?", ["Drop Duplicates", "Retain Duplicates"])
        if dup_action == "Drop Duplicates":
            df.drop_duplicates(inplace=True)
            st.success("Duplicates dropped.")
        else:
            st.info("Duplicates retained.")
    else:
        st.info("No duplicates found.")

    if df.isnull().sum().sum() > 0:
        st.write("**Missing Values Summary:**")
        st.dataframe(df.isnull().sum())
        null_strategy = st.selectbox("How do you want to handle missing values?", ["Forward Fill", "Backward Fill", "Drop Rows"])
        if null_strategy == "Forward Fill":
            df.fillna(method='ffill', inplace=True)
            st.success("Missing values forward filled.")
        elif null_strategy == "Backward Fill":
            df.fillna(method='bfill', inplace=True)
            st.success("Missing values backward filled.")
        else:
            df.dropna(inplace=True)
            st.success("Rows with missing values dropped.")
    else:
        st.info("No missing values found.")

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
