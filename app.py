import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="SG Job Postings Dashboard", layout="wide")

print(f"🟢 Rerun at: {datetime.now()}")

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "job_data.csv"
COMPANIES_PATH = BASE_DIR / "data" / "companies.csv"
LOOKUPS_PATH = BASE_DIR / "data" / "lookups.csv"


@st.cache_data
def load_data(data_path, companies_path, lookups_path):
    df = pd.read_csv(data_path)
    df["posting_date"] = pd.to_datetime(df["posting_date"])

    # company_id, category_id, employment_type_id, position_level_id and job_status_id
    # were normalized out into small lookup tables to keep job_data.csv small.
    # Join everything back in so the rest of the app can work with plain names.
    companies = pd.read_csv(companies_path)
    df = df.merge(companies, on="company_id", how="left").drop(columns=["company_id"])
    df = df.rename(columns={"company_name": "company"})

    lookups = pd.read_csv(lookups_path)
    for dim in ["category", "employment_type", "position_level", "job_status"]:
        dim_lookup = lookups[lookups["dim"] == dim][["id", "value"]].rename(
            columns={"id": f"{dim}_id", "value": dim}
        )
        df = df.merge(dim_lookup, on=f"{dim}_id", how="left").drop(columns=[f"{dim}_id"])

    return df


df = load_data(DATA_PATH, COMPANIES_PATH, LOOKUPS_PATH)

st.title("💼 Singapore Job Postings Dashboard")
st.caption(
    "Explore job postings scraped from MyCareersFuture (SGJobData), "
    "with a focus on which roles are hardest to fill."
)

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

st.sidebar.header("Hard-to-Fill Threshold")
st.sidebar.caption(
    "A posting is flagged 'hard to fill' if it was reposted, or received "
    "very few applications relative to its vacancies."
)
max_apps_per_vacancy = st.sidebar.slider(
    "Flag postings with applications-per-vacancy below",
    min_value=0.0,
    max_value=10.0,
    value=1.0,
    step=0.5,
)

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

# A posting is "hard to fill" if it was reposted at least once, OR it drew very
# few applications relative to how many vacancies it needs to fill.
filtered_df["hard_to_fill"] = (
    (filtered_df["repost_count"] > 0)
    | (filtered_df["applications_per_vacancy"] < max_apps_per_vacancy)
)


st.header("Filtered Results")
st.write(
    f"Matching rows: {len(filtered_df):,} | Columns: {len(filtered_df.columns)}")
st.dataframe(filtered_df, use_container_width=True)


# KPI Rows
st.header("Key Metrics")
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Job Postings", f"{len(filtered_df):,}")
col2.metric("Average Salary", f"${filtered_df['average_salary'].mean():,.0f}")
hard_to_fill_rate = filtered_df["hard_to_fill"].mean() * 100 if len(filtered_df) else 0
col3.metric("Hard-to-Fill Rate", f"{hard_to_fill_rate:.1f}%")
col4.metric("Avg Applications / Vacancy", f"{filtered_df['applications_per_vacancy'].mean():.1f}")
col5.metric("Avg Posting Duration", f"{filtered_df['posting_duration_days'].mean():.0f} days")

st.header("Hard-to-Fill Vacancy Analysis")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Hard-to-Fill Rate by Category")
    hard_by_category = (
        filtered_df.groupby("category", as_index=False)["hard_to_fill"]
        .mean()
        .assign(hard_to_fill=lambda d: d["hard_to_fill"] * 100)
        .sort_values("hard_to_fill", ascending=False)
        .head(10)
    )
    fig_hard_category = px.bar(
        hard_by_category, x="category", y="hard_to_fill",
        labels={"hard_to_fill": "Hard-to-fill rate (%)"},
    )
    st.plotly_chart(fig_hard_category, use_container_width=True)

with col_right:
    st.subheader("Hard-to-Fill Rate by Position Level")
    hard_by_level = (
        filtered_df.groupby("position_level", as_index=False)["hard_to_fill"]
        .mean()
        .assign(hard_to_fill=lambda d: d["hard_to_fill"] * 100)
        .sort_values("hard_to_fill", ascending=False)
    )
    fig_hard_level = px.bar(
        hard_by_level, x="position_level", y="hard_to_fill",
        labels={"hard_to_fill": "Hard-to-fill rate (%)"},
    )
    st.plotly_chart(fig_hard_level, use_container_width=True)

st.subheader("Applications per Vacancy vs. Average Salary")
st.caption(
    "Roles in the bottom-left (low applications, but not necessarily low salary) "
    "are the ones employers struggle most to fill despite paying competitively."
)
scatter_df = (
    filtered_df.groupby("category", as_index=False)
    .agg(
        avg_salary=("average_salary", "mean"),
        avg_apps_per_vacancy=("applications_per_vacancy", "mean"),
        postings=("average_salary", "count"),
    )
)
fig_scatter = px.scatter(
    scatter_df, x="avg_salary", y="avg_apps_per_vacancy", size="postings",
    hover_name="category",
    labels={"avg_salary": "Average Salary ($)", "avg_apps_per_vacancy": "Avg Applications / Vacancy"},
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.subheader("Monthly Hard-to-Fill Rate & Median Applications per Vacancy")
trend = (
    filtered_df.assign(month=filtered_df["posting_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month", as_index=False)
    .agg(
        hard_to_fill_rate=("hard_to_fill", "mean"),
        median_apps_per_vacancy=("applications_per_vacancy", "median"),
    )
    .sort_values("month")
)
trend["hard_to_fill_rate"] = trend["hard_to_fill_rate"] * 100
fig_trend = px.line(
    trend, x="month", y=["hard_to_fill_rate", "median_apps_per_vacancy"], markers=True,
)
st.plotly_chart(fig_trend, use_container_width=True)

st.subheader("Top 10 Companies with the Most Hard-to-Fill Postings")
top_companies_hard = (
    filtered_df[filtered_df["hard_to_fill"]]
    .groupby("company", as_index=False)
    .size()
    .rename(columns={"size": "hard_to_fill_postings"})
    .sort_values("hard_to_fill_postings", ascending=False)
    .head(10)
)
fig_companies_hard = px.bar(top_companies_hard, x="company", y="hard_to_fill_postings")
st.plotly_chart(fig_companies_hard, use_container_width=True)

with st.expander("View Filtered Job Postings"):
    st.dataframe(filtered_df, use_container_width=True, height=350)
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered CSV",
        data=csv,
        file_name="filtered_job_data.csv",
        mime="text/csv",
    )
