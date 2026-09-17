# reduce_dataset.py - Updated script to compress SGJobData.csv to < 25MB for GitHub & Streamlit Cloud
import pandas as pd
import numpy as np
import re
import os

def reduce_data():
    input_path = 'data/SGJobData.csv'
    
    print(f"Reading raw dataset from '{input_path}'...")
    if not os.path.exists(input_path):
        if os.path.exists('SGJobData.csv'):
            input_path = 'SGJobData.csv'
        elif os.path.exists('../data/SGJobData.csv'):
            input_path = '../data/SGJobData.csv'

    df = pd.read_csv(input_path)
    raw_size_mb = os.path.getsize(input_path) / (1024 * 1024) if os.path.exists(input_path) else 0
    print(f"Raw dataset loaded: {len(df):,} rows | File size: ~{raw_size_mb:.1f} MB")
    
    # 1. Keep only Open job status
    df_clean = df[df['status_jobStatus'] == 'Open'].copy()
    
    # 2. Filter valid monthly employment types
    valid_emp_types = ['Permanent', 'Full Time', 'Contract', 'Internship/Attachment']
    df_clean = df_clean[df_clean['employmentTypes'].isin(valid_emp_types)].copy()
    
    # 3. Extract Category via Regex
    def extract_cat(s):
        if pd.isna(s) or not isinstance(s, str):
            return 'Uncategorized'
        match = re.search(r'["\']category["\']\s*:\s*["\']([^"\']+)["\']', s)
        return match.group(1) if match else 'Uncategorized'
    
    df_clean['clean_category'] = df_clean['categories'].apply(extract_cat)
    
    # 4. Dates and Active Posting Duration Calculation
    df_clean['orig_posting_dt'] = pd.to_datetime(df_clean['metadata_originalPostingDate'], errors='coerce')
    df_clean['expiry_dt'] = pd.to_datetime(df_clean['metadata_expiryDate'], errors='coerce')
    df_clean['posting_duration_days'] = (df_clean['expiry_dt'] - df_clean['orig_posting_dt']).dt.days.fillna(0).astype(int)
    
    # 5. Numeric Cleanup
    df_clean['average_salary'] = pd.to_numeric(df_clean['average_salary'], errors='coerce').fillna(0).astype(int)
    df_clean['salary_minimum'] = pd.to_numeric(df_clean['salary_minimum'], errors='coerce').fillna(0).astype(int)
    df_clean['salary_maximum'] = pd.to_numeric(df_clean['salary_maximum'], errors='coerce').fillna(0).astype(int)
    df_clean['metadata_repostCount'] = pd.to_numeric(df_clean['metadata_repostCount'], errors='coerce').fillna(0).astype(int)
    
    # 6. Composite Difficulty Score
    df_clean['difficulty_score'] = (df_clean['metadata_repostCount'] + 1) * (df_clean['posting_duration_days'] + 1)
    
    # 7. Select ONLY Essential Columns needed for the Dashboard
    essential_cols = [
        'title', 'clean_category', 'positionLevels', 'postedCompany_name',
        'employmentTypes', 'salary_minimum', 'average_salary', 'salary_maximum',
        'posting_duration_days', 'metadata_repostCount', 'difficulty_score',
        'metadata_expiryDate'
    ]
    
    df_final = df_clean[essential_cols].copy()
    
    # Clean text columns to avoid whitespace bloat
    df_final['title'] = df_final['title'].astype(str).str.strip().str.slice(0, 100)
    df_final['postedCompany_name'] = df_final['postedCompany_name'].astype(str).str.strip()
    
    output_dir = 'streamlit/data'
    os.makedirs(output_dir, exist_ok=True)
    
    # Export 1: Gzipped CSV (.csv.gz) - RECOMMENDED for Streamlit & GitHub (~15-22 MB)
    gz_path = os.path.join(output_dir, 'SGJobData_clean.csv.gz')
    df_final.to_csv(gz_path, index=False, compression='gzip')
    gz_size_mb = os.path.getsize(gz_path) / (1024 * 1024)
    
    # Export 2: Standard CSV (.csv) - Optimized formatting (~75-85 MB)
    csv_path = os.path.join(output_dir, 'SGJobData_clean.csv')
    df_final.to_csv(csv_path, index=False)
    csv_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
    
    print("\n" + "=" * 60)
    print("✅ DATA COMPRESSION & REDUCTION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Original Rows:    {len(df):,}  --> Cleaned Rows: {len(df_final):,}")
    print(f"1. Standard CSV:  '{csv_path}'  --> Size: ~{csv_size_mb:.1f} MB")
    print(f"2. Gzipped CSV:   '{gz_path}'   --> Size: ~{gz_size_mb:.1f} MB  <-- RECOMMENDED FOR GITHUB")
    print("\n💡 Use 'SGJobData_clean.csv.gz' for GitHub push! It is native to Pandas read_csv().")

if __name__ == '__main__':
    reduce_data()
