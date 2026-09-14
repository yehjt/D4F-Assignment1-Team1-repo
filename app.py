import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

print(f"🟢 Rerun at: {datetime.now()}")

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "job_data.csv"


@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["posting_date"] = pd.to_datetime(df["posting_date"])
    return df


df = load_data(DATA_PATH)

st.set_page_config(page_title="SG Job Postings Dashboard", layout="wide")
st.title("💼 Singapore Job Postings Dashboard")
st.caption("Explore job postings scraped from MyCareersFuture (SGJobData).")

st.sidebar.header("Filters")

# Get unique categories, employment types and position levels for the multi-select widgets
unique_categories = sorted(df["category"].dropna().unique())
unique_employment_types = sorted(df["employment_type"].dropna().unique())
unique_position_levels = sorted(df["position_level"].dropna().unique())

# Get min and max average salary for the slider
min_salary = int(df["average_salary"].min())
max_salary = int(df["average_salary"].max())

# Get min and max posting dates for the date input
date_min = df["posting_date"].min().date()
date_max = df["posting_date"].max().date()

# Create filter widgets
selected_categories = st.sidebar.multiselect("Category", unique_categories, default=[])
selected_employment_types = st.sidebar.multiselect(
    "Employment Type", unique_employment_types, default=[]
)
selected_position_levels = st.sidebar.multiselect(
    "Position Level", unique_position_levels, default=[]
)
salary_range = st.sidebar.slider(
    "Average Salary Range",
    min_value=min_salary,
    max_value=max_salary,
    value=(min_salary, max_salary),
    step=500,
)
date_range = st.sidebar.date_input("Posting Date Range", value=(date_min, date_max))

# Make a copy of the original dataframe to apply filters
filtered_df = df.copy()

# If the user has selected any categories, filter the dataframe accordingly
if selected_categories:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]

# If the user has selected any employment types, filter the dataframe accordingly
if selected_employment_types:
    filtered_df = filtered_df[filtered_df["employment_type"].isin(selected_employment_types)]

# If the user has selected any position levels, filter the dataframe accordingly
if selected_position_levels:
    filtered_df = filtered_df[filtered_df["position_level"].isin(selected_position_levels)]

# Filter the dataframe based on the selected average salary range
filtered_df = filtered_df[filtered_df["average_salary"].between(
    salary_range[0], salary_range[1])]

# If the user has selected a date range, filter the dataframe accordingly
if len(date_range) == 2:
    # unpack values from date_range tuple
    start_date, end_date = date_range
    filtered_df = filtered_df[filtered_df["posting_date"].between(
        pd.to_datetime(start_date), pd.to_datetime(end_date))]


st.header("Filtered Results")
st.write(
    f"Matching rows: {len(filtered_df):,} | Columns: {len(filtered_df.columns)}")
st.dataframe(filtered_df, use_container_width=True)


# KPI Rows
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Job Postings", f"{len(filtered_df):,}")
col2.metric("Average Salary", f"${filtered_df['average_salary'].mean():,.0f}")
col3.metric("Median Salary", f"${filtered_df['average_salary'].median():,.0f}")
col4.metric("Total Vacancies", f"{filtered_df['num_vacancies'].sum():,.0f}")

st.header("Visual Analysis")

col_left, col_right = st.columns(2)

# Tells Streamlit to put the following content in the left column
with col_left:
    st.subheader("Average Salary by Category")
    avg_salary_by_category = (
        filtered_df.groupby("category", as_index=False)["average_salary"]
        .mean()
        .sort_values("average_salary", ascending=False)
        .head(10)  # Top 10 categories only for clarity
    )
    fig_category = px.bar(avg_salary_by_category, x="category", y="average_salary")
    st.plotly_chart(fig_category, use_container_width=True)

# Tells Streamlit to put the following content in the right column
with col_right:
    st.subheader("Postings by Employment Type")
    tx_by_employment = (
        filtered_df.groupby("employment_type", as_index=False)
        .size()
        .rename(columns={"size": "postings"})
        .sort_values("postings", ascending=False)
    )
    fig_employment = px.bar(tx_by_employment, x="employment_type", y="postings")
    st.plotly_chart(fig_employment, use_container_width=True)


st.subheader("Monthly Median Salary & Postings Volume")
trend = (
    filtered_df.assign(month=filtered_df["posting_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)
    .agg(median_salary=("average_salary", "median"), postings=("title", "count"))
    .sort_values("month")
)
fig_trend = px.line(trend, x="month", y="median_salary", markers=True)
st.plotly_chart(fig_trend, use_container_width=True)

st.subheader("Top 10 Hiring Companies")
top_companies = (
    filtered_df.groupby("company", as_index=False)
    .size()
    .rename(columns={"size": "postings"})
    .sort_values("postings", ascending=False)
    .head(10)
)
fig_companies = px.bar(top_companies, x="company", y="postings")
st.plotly_chart(fig_companies, use_container_width=True)

with st.expander("View Filtered Job Postings"):
    st.dataframe(filtered_df, use_container_width=True, height=350)
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv,
        file_name="filtered_job_data.csv",
        mime="text/csv",
    )
