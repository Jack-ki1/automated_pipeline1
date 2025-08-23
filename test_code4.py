
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


    num_rows, num_cols = df.shape
    num_nulls = df.isnull().sum().sum()
    num_duplicates = df.duplicated().sum()
    memory_usage = df.memory_usage(deep=True).sum() / (1024**2)  # MB

    # --- Summary cards ---
    st.markdown(f"""
    <div class='info-card'>
        <div class='card'><strong>Total Rows</strong><br>{num_rows:,}</div>
        <div class='card'><strong>Total Columns</strong><br>{num_cols}</div>
        <div class='card'><strong>Total Nulls</strong><br>{num_nulls:,}</div>
        <div class='card'><strong>Duplicate Rows</strong><br>{num_duplicates:,}</div>
        <div class='card'><strong>Memory Usage</strong><br>{memory_usage:.2f} MB</div>
    </div>
    """, unsafe_allow_html=True)

    # --- Tabs for deeper insights ---
    tab1, tab2, tab3, tab4 = st.tabs(["📑 Preview", "ℹ️ Metadata", "📊 Stats", "📉 Visual Insights"])

    # =====================
    # TAB 1: Preview
    # =====================
    with tab1:
        st.subheader("👀 Quick Preview")
        st.write("First 5 rows of the dataset:")
        st.dataframe(df.head())
        st.write("Last 5 rows of the dataset:")
        st.dataframe(df.tail())

    # =====================
    # TAB 2: Metadata
    # =====================
    with tab2:
        st.subheader("🧾 Column Metadata")

        # Show df.info() nicely
        buffer = StringIO()
        df.info(buf=buffer)
        st.text(buffer.getvalue())

        # Build metadata table
        missing_counts = df.isnull().sum()
        pct_missing = (missing_counts / len(df) * 100).round(2)  # ✅ FIX: use Series.round(2), not round(ndarray, 2)

        meta_df = pd.DataFrame({
            "Column": df.columns,
            "Data Type": df.dtypes.astype(str).values,
            "Missing Values": missing_counts.values,
            "% Missing": pct_missing.values,
            "Unique Values": df.nunique().values,
            "Sample Value": [df[col].dropna().iloc[0] if df[col].notna().any() else "NaN" for col in df.columns]
        })
        st.dataframe(meta_df)

    # =====================
    # TAB 3: Stats
    # =====================
    with tab3:
        st.subheader("📊 Descriptive Statistics")

        # Numerical summary (guard for no numeric columns)
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) > 0:
            num_summary = df[num_cols].describe().T
            num_summary["missing"] = df[num_cols].isnull().sum()
            st.write("### Numerical Columns Summary")
            st.dataframe(num_summary)
        else:
            st.info("No numerical columns detected.")

        # Categorical summary (guard for no categorical columns)
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(cat_cols) > 0:
            st.write("### Categorical Columns Summary")
            cat_unique = df[cat_cols].nunique()
            mode_df = df[cat_cols].mode(dropna=True)
            most_freq = mode_df.iloc[0] if not mode_df.empty else pd.Series(index=cat_cols, dtype=object)
            cat_summary = pd.DataFrame({
                "Unique Values": cat_unique,
                "Most Frequent": most_freq
            })
            st.dataframe(cat_summary)
        else:
            st.info("No categorical columns detected.")

        st.write("### Full Summary (All Types)")
        # df.describe(include="all") can be empty if df has weird dtypes; guard it
        try:
            st.dataframe(df.describe(include="all").T)
        except Exception:
            st.info("Full summary not available for this mix of dtypes.")

    # =====================
    # TAB 4: Visual Insights
    # =====================
    with tab4:
        st.subheader("📉 Data Quality & Distribution Insights")

        # Missing values per column
        missing_df = missing_counts.reset_index()
        missing_df.columns = ["Column", "Missing Count"]
        fig = px.bar(missing_df, x="Column", y="Missing Count", title="Missing Values per Column")
        st.plotly_chart(fig, use_container_width=True)

        # Top numeric column distributions (up to 3)
        top_numeric = list(num_cols)[:3]
        if len(top_numeric) > 0:
            st.write("### Distribution of Numeric Columns")
            for col in top_numeric:
                fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                st.plotly_chart(fig, use_container_width=True)

        # Top categorical column frequencies (up to 3)
        top_cat = list(cat_cols)[:3]
        if len(top_cat) > 0:
            st.write("### Frequency of Categorical Columns")
            for col in top_cat:
                vc = df[col].astype(str).value_counts(dropna=False).reset_index()
                vc.columns = [col, "Count"]
                fig = px.bar(vc.head(20), x=col, y="Count", title=f"Top Categories in {col}")
                st.plotly_chart(fig, use_container_width=True)

    # -------------------------------
    # STEP 3: Clean Data
    # -------------------------------
    st.header("🧹 Step 3: Clean Your Data")

    st.markdown("### Null Value Handling")
    st.write(f"Total missing values: **{df.isnull().sum().sum()}** across {df.isnull().any().sum()} columns.")

    null_strategy = st.selectbox(
        "Choose how to handle missing values:",
        [
            "Do nothing",
            "Drop rows with any nulls",
            "Drop rows with all nulls",
            "Fill with column mean (numeric only)",
            "Fill with column median (numeric only)",
            "Fill with column mode (all types)",
            "Forward fill (propagate last valid value)",
            "Backward fill (propagate next valid value)",
            "Custom fill per column"
        ]
    )

    if null_strategy == "Drop rows with any nulls":
        df = df.dropna(how="any")
    elif null_strategy == "Drop rows with all nulls":
        df = df.dropna(how="all")
    elif null_strategy == "Fill with column mean (numeric only)":
        for col in df.select_dtypes(include=["number"]).columns:
            df[col] = df[col].fillna(df[col].mean())
    elif null_strategy == "Fill with column median (numeric only)":
        for col in df.select_dtypes(include=["number"]).columns:
            df[col] = df[col].fillna(df[col].median())
    elif null_strategy == "Fill with column mode (all types)":
        for col in df.columns:
            if df[col].isnull().any():
                try:
                    df[col] = df[col].fillna(df[col].mode()[0])
                except Exception:
                    pass
    elif null_strategy == "Forward fill (propagate last valid value)":
        df = df.ffill()
    elif null_strategy == "Backward fill (propagate next valid value)":
        df = df.bfill()
    elif null_strategy == "Custom fill per column":
        st.write("Specify replacement values for each column with missing data:")
        fill_values = {}
        for col in df.columns[df.isnull().any()]:
            replacement = st.text_input(f"Fill value for column `{col}` (current nulls: {df[col].isnull().sum()})")
            if replacement != "":
                fill_values[col] = replacement
        if st.button("Apply Custom Fill"):
            for col, replacement in fill_values.items():
                try:
                    df[col] = df[col].fillna(type(df[col].dropna().iloc[0])(replacement))
                except Exception:
                    df[col] = df[col].fillna(replacement)
            st.success("✅ Custom fill applied.")

    st.markdown("---")
    st.markdown("### Duplicate Handling")
    st.write(f"Total duplicate rows detected: **{df.duplicated().sum()}**")

    dup_strategy = st.selectbox(
        "Choose how to handle duplicates:",
        [
            "Do nothing",
            "Drop all duplicates (keep first)",
            "Drop all duplicates (keep last)",
            "Drop duplicates across selected subset of columns"
        ]
    )

    if dup_strategy == "Drop all duplicates (keep first)":
        df = df.drop_duplicates(keep="first")
    elif dup_strategy == "Drop all duplicates (keep last)":
        df = df.drop_duplicates(keep="last")
    elif dup_strategy == "Drop duplicates across selected subset of columns":
        subset_cols = st.multiselect("Select columns to check duplicates on:", df.columns)
        if subset_cols:
            df = df.drop_duplicates(subset=subset_cols, keep="first")

    st.success("✅ Data cleaned.")
    st.dataframe(df.head())


    # -------------------------------
    # STEP 3b: Data Type Checking
    # -------------------------------
    st.subheader("🛠 Step 3b: Check & Correct Column Data Types")
    st.write("The system will suggest data types based on heuristics. You can override them below:")

    # Function to auto-suggest column types
    def suggest_dtype(series: pd.Series):
        if pd.api.types.is_numeric_dtype(series):
            return "int64" if pd.api.types.is_integer_dtype(series) else "float64"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime64[ns]"
        elif pd.api.types.is_bool_dtype(series):
            return "bool"
        else:
            # Try parsing as datetime
            try:
                pd.to_datetime(series.dropna().sample(min(50, len(series))), errors="raise")
                return "datetime64[ns]"
            except Exception:
                pass
            # Try numeric
            if series.dropna().astype(str).str.replace(".", "", 1).str.isnumeric().all():
                return "float64"
            # Try boolean
            if series.dropna().astype(str).str.lower().isin(["true", "false", "yes", "no", "0", "1"]).all():
                return "bool"
            # Categorical suggestion
            if series.nunique() < (0.05 * len(series)):
                return "category"
            return "object"

    # Build selection UI
    col_types = {}
    for col in df.columns:
        suggested_type = suggest_dtype(df[col])
        current_type = str(df[col].dtype)
        st.markdown(f"**Column:** `{col}` | Detected: `{current_type}` | Suggested: `{suggested_type}`")

        new_type = st.selectbox(
            f"Select type for '{col}'",
            ["int64", "float64", "object", "datetime64[ns]", "bool", "category"],
            index=["int64", "float64", "object", "datetime64[ns]", "bool", "category"].index(suggested_type)
            if suggested_type in ["int64", "float64", "object", "datetime64[ns]", "bool", "category"] else 2
        )
        col_types[col] = new_type

    if st.button("Apply Type Conversions"):
        for col, t in col_types.items():
            try:
                if t == "datetime64[ns]":
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                elif t == "bool":
                    df[col] = df[col].astype(str).str.lower().map(
                        {"true": True, "false": False, "yes": True, "no": False, "1": True, "0": False}
                    ).astype("boolean")
                elif t == "category":
                    df[col] = df[col].astype("category")
                else:
                    df[col] = df[col].astype(t, errors="ignore")
            except Exception as e:
                st.warning(f"⚠️ Could not convert {col} to {t}: {e}")
        st.success("✅ Data type conversions applied.")
        st.dataframe(df.dtypes)

    # Download cleaned data
    st.download_button("📥 Download Cleaned Data", df.to_csv(index=False), "cleaned_data.csv")

# -------------------------------
# STEP 4: Visualize Data
# -------------------------------
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

# -------------------------------
# STEP 5: Download Data Report
# -------------------------------
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import tempfile

st.header("📥 Step 5: Download Data Report")

if not df.empty:
    if st.button("Generate PDF Report"):
        # Create temporary file
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(tmp_file.name, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("📊 Data Report", styles["Title"]))
        elements.append(Spacer(1, 12))

        # --- Dataset Summary ---
        elements.append(Paragraph("Dataset Summary", styles["Heading2"]))
        summary_data = [
            ["Rows", df.shape[0]],
            ["Columns", df.shape[1]],
            ["Total Nulls", int(df.isnull().sum().sum())],
            ["Duplicate Rows", int(df.duplicated().sum())],
        ]
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 12))

        # --- Column Metadata ---
        elements.append(Paragraph("Column Metadata", styles["Heading2"]))
        meta_data = [["Column", "Dtype", "Missing %", "Unique Values"]]
        for col in df.columns:
            missing_pct = round(df[col].isnull().sum() / len(df) * 100, 2)
            meta_data.append([col, str(df[col].dtype), f"{missing_pct}%", df[col].nunique()])
        meta_table = Table(meta_data, colWidths=[150, 100, 100, 100])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 12))

        # --- Numerical Summary ---
        elements.append(Paragraph("Numerical Data Summary", styles["Heading2"]))
        desc = df.describe(include="all").fillna("").astype(str).reset_index()
        desc_data = [desc.columns.tolist()] + desc.values.tolist()
        desc_table = Table(desc_data, colWidths=[100]*len(desc.columns))
        desc_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ]))
        elements.append(desc_table)

        # Build PDF
        doc.build(elements)

        # Read PDF and make it downloadable
        with open(tmp_file.name, "rb") as f:
            st.download_button(
                label="⬇️ Download Data Report (PDF)",
                data=f,
                file_name="data_report.pdf",
                mime="application/pdf"
            )

