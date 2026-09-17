# streamlit/app.py - Updated to support SGJobData_clean.csv.gz (< 25MB)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(
    page_title="Singapore Job Market - Hard-to-Fill Roles Dashboard",
    page_icon="💼",
    layout="wide"
)

# 1. Flexible Data Loader (Prefers compressed .csv.gz then .csv)
@st.cache_data
def load_data():
    possible_paths = [
        'streamlit/data/SGJobData_clean.csv.gz',
        'data/SGJobData_clean.csv.gz',
        'SGJobData_clean.csv.gz',
        'streamlit/data/SGJobData_clean.csv',
        'data/SGJobData_clean.csv',
        'SGJobData_clean.csv'
    ]
    file_path = next((path for path in possible_paths if os.path.exists(path)), None)
    
    if file_path is None:
        st.error("❌ Dataset file not found! Please ensure 'SGJobData_clean.csv.gz' or 'SGJobData_clean.csv' is placed in 'streamlit/data/'.")
        st.stop()
        
    return pd.read_csv(file_path)

df_raw = load_data()

# 2. Header & Sidebar Filters
st.title("💼 Singapore Open Jobs Interactive Dashboard")
st.markdown("### Predicting & Analyzing Hard-to-Fill Roles for Job Seekers & Recruiters")

st.sidebar.header("🔍 Interactive Query Filters")

# Filter 1: Job Category
all_categories = sorted([cat for cat in df_raw['clean_category'].unique() if cat != 'Uncategorized'])
selected_categories = st.sidebar.multiselect("Select Job Category:", options=all_categories, default=[])

# Filter 2: Position Levels
all_levels = sorted([lvl for lvl in df_raw['positionLevels'].dropna().unique()])
selected_levels = st.sidebar.multiselect("Select Position Level:", options=all_levels, default=[])

# Filter 3: Job Title Search
search_title = st.sidebar.text_input("Search Job Title (e.g. Engineer, Manager):", "")

# Filter 4: Employment Types
all_emp_types = sorted([emp for emp in df_raw['employmentTypes'].dropna().unique()])
selected_emp_types = st.sidebar.multiselect("Select Employment Type:", options=all_emp_types, default=all_emp_types)

# Filter 5: Monthly Salary Range Slider
min_salary_val = int(df_raw['average_salary'].min())
max_salary_val = min(int(df_raw['average_salary'].quantile(0.99)), 30000)
salary_range = st.sidebar.slider("Select Average Monthly Salary Range (SGD):", min_value=min_salary_val, max_value=max_salary_val, value=(min_salary_val, max_salary_val), step=500)

# Filter 6: Role Difficulty Score Range Slider
min_diff_val = int(df_raw['difficulty_score'].min())
max_diff_val = int(df_raw['difficulty_score'].quantile(0.99))
if max_diff_val <= min_diff_val:
    max_diff_val = min_diff_val + 100

diff_range = st.sidebar.slider("Select Role Difficulty Score Range:", min_value=min_diff_val, max_value=max_diff_val, value=(min_diff_val, max_diff_val), step=1)

# 3. Query Execution
df_filtered = df_raw.copy()

if selected_categories:
    df_filtered = df_filtered[df_filtered['clean_category'].isin(selected_categories)]

if selected_levels:
    df_filtered = df_filtered[df_filtered['positionLevels'].isin(selected_levels)]

if search_title.strip():
    df_filtered = df_filtered[df_filtered['title'].str.contains(search_title, case=False, na=False)]

if selected_emp_types:
    df_filtered = df_filtered[df_filtered['employmentTypes'].isin(selected_emp_types)]

min_sal, max_sal = salary_range
df_filtered = df_filtered[(df_filtered['average_salary'] >= min_sal) & (df_filtered['average_salary'] <= max_sal)]

min_diff, max_diff = diff_range
df_filtered = df_filtered[(df_filtered['difficulty_score'] >= min_diff) & (df_filtered['difficulty_score'] <= max_diff)]

# 4. Summary Metrics & Results Table
col1, col2, col3, col4 = st.columns(4)
col1.metric("Filtered Open Postings", f"{len(df_filtered):,}")
col2.metric("Average Monthly Salary", f"S${df_filtered['average_salary'].mean():,.0f}" if len(df_filtered) > 0 else "S$0")
col3.metric("Avg Posting Duration", f"{df_filtered['posting_duration_days'].mean():.1f} Days" if len(df_filtered) > 0 else "0 Days")
col4.metric("Avg Repost Count", f"{df_filtered['metadata_repostCount'].mean():.2f}" if len(df_filtered) > 0 else "0")

st.markdown("---")
st.subheader("📋 Query Results Data Table")

display_cols = [
    'title', 'clean_category', 'positionLevels', 'postedCompany_name', 
    'employmentTypes', 'salary_minimum', 'average_salary', 'salary_maximum',
    'posting_duration_days', 'metadata_repostCount', 'difficulty_score', 'metadata_expiryDate'
]

st.dataframe(
    df_filtered[display_cols].rename(columns={
        'title': 'Job Title', 'clean_category': 'Category', 'positionLevels': 'Position Level',
        'postedCompany_name': 'Company Name', 'employmentTypes': 'Employment Type',
        'salary_minimum': 'Min Salary (S$)', 'average_salary': 'Avg Salary (S$)', 'salary_maximum': 'Max Salary (S$)',
        'posting_duration_days': 'Posting Duration (Days)', 'metadata_repostCount': 'Repost Count',
        'difficulty_score': 'Difficulty Score', 'metadata_expiryDate': 'Expiry Date'
    }),
    use_container_width=True,
    height=360
)

st.markdown("---")

# 5. Visualizations
if len(df_filtered) == 0:
    st.warning("⚠️ No job postings match your selected filter criteria. Please adjust your sidebar settings.")
else:
    st.subheader("📊 Interactive Analytical Charts")
    sns.set_theme(style="whitegrid")
    
    # Chart 1: Posting Duration
    st.markdown("#### 1. Mean Posting Duration (Active Days) by Category")
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    top_cats_filtered = df_filtered['clean_category'].value_counts().head(10).index
    df_chart1 = df_filtered[df_filtered['clean_category'].isin(top_cats_filtered)]
    
    dur_summary = df_chart1.groupby('clean_category')['posting_duration_days'].mean().sort_values(ascending=True)
    bars1 = ax1.barh(dur_summary.index, dur_summary.values, color='#3182bd', height=0.6)
    ax1.set_xlabel('Average Posting Duration (Days)', fontweight='bold')
    ax1.set_ylabel('Job Category', fontweight='bold')
    for bar in bars1:
        w = bar.get_width()
        ax1.text(w + 0.5, bar.get_y() + bar.get_height()/2, f"{w:.1f} days", va='center', fontweight='bold', fontsize=9)
    st.pyplot(fig1)
    
    st.markdown("---")
    
    # Chart 2: Salary Range
    st.markdown("#### 2. Monthly Salary Range (Min, Average, Max)")
    fig2, ax2 = plt.subplots(figsize=(12, 5))
    sal_summary = df_chart1.groupby('clean_category')[['salary_minimum', 'average_salary', 'salary_maximum']].mean().sort_values(by='average_salary', ascending=True)
    sal_summary.plot(kind='barh', ax=ax2, color=['#1f77b4', '#ff7f0e', '#2ca02c'], width=0.75)
    ax2.set_xlabel('Monthly Salary (SGD)', fontweight='bold')
    ax2.set_ylabel('Job Category', fontweight='bold')
    ax2.legend(['Min Salary', 'Average Salary', 'Max Salary'], loc='lower right')
    st.pyplot(fig2)
    
    st.markdown("---")
    
    # Chart 3: Top Hiring Companies
    st.markdown("#### 3. Top Hiring Companies for Selected Roles")
    fig3, ax3 = plt.subplots(figsize=(14, 7))
    comp_breakdown = (
        df_filtered.groupby(['postedCompany_name', 'clean_category', 'positionLevels'])
        .size().reset_index(name='posting_count')
        .sort_values(by='posting_count', ascending=True).tail(10)
    )
    comp_breakdown['display_label'] = comp_breakdown['postedCompany_name'] + " \n[" + comp_breakdown['clean_category'] + " | " + comp_breakdown['positionLevels'] + "]"
    
    colors3 = plt.cm.tab10.colors[:len(comp_breakdown)]
    bars3 = ax3.barh(y=comp_breakdown['display_label'], width=comp_breakdown['posting_count'], color=colors3, height=0.65)
    
    max_c3 = comp_breakdown['posting_count'].max()
    for bar in bars3:
        w = bar.get_width()
        ax3.text(x=w + (max_c3 * 0.015), y=bar.get_y() + bar.get_height() / 2, s=f" {w:,} posts", va='center', ha='left', fontsize=10, fontweight='bold', color='#222222')
        
    ax3.set_xlim(0, max_c3 * 1.18)
    ax3.set_xlabel('Number of Open Job Postings', fontweight='bold')
    ax3.set_ylabel('Company [ Job Category | Position Level ]', fontweight='bold')
    st.pyplot(fig3)
