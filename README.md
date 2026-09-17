# D4F-Assignment1-Team1-repo

Module 1 Project Assignment 

> ## 📁 Project Folder Structure

```text
D4F-Assignment1-Team1-repo/         <-- GitHub Repository Root
│
├── environment.yml                     <-- Run "conda env create -f environment.yml" locally to create the pds environment to run assignment.ipynb
├── env_streamlit.yml                   <-- Run "conda env create -f env_streamlit.yml" locally to create the m1-a1-streamlit_app environment
├── assignment.ipynb                    <-- Run locally in Jupyter Notebook in Visual Studio Code 
├── reduce_dataset.py                   <-- Run once locally to generate compressed clean dataset (SGJobData_clean.csv.gz)
│
└── streamlit/                          <-- Streamlit Application Directory
    ├── app.py                              <-- Main Streamlit dashboard script
    ├── requirements.txt                    <-- Package dependencies for Streamlit Cloud
    └── data/
        └── SGJobData_clean.csv.gz              <-- Compressed dataset file (~20MB, <100MB for GitHub)
```

---

> ## 💻 Steps to Run Streamlit App Locally

1. **Open the project folder** in Visual Studio Code.
2. **Open a new WSL terminal** inside VS Code.
3. **Activate the environment** by running:
   ```bash
   conda activate m1-a1-streamlit_app
   ```
4. **Navigate to the streamlit folder** and run the app:
   ```bash
   cd streamlit
   streamlit run app.py
   ```
5. **Open your browser** and go to the local URL provided (usually `http://localhost:8501`) to view the Streamlit dashboard.

---

> ## 🚀 Steps to Run Streamlit App on a Public Website

1. Navigate to [share.streamlit.io](https://streamlit.io) and log in with your GitHub account.
2. Click the **"New app"** button.
3. Configure your deployment settings:
   * **Repository:** `your-username/your-repo-name`
   * **Branch:** `main`
   * **Main file path:** `streamlit/app.py`
4. Click **"Deploy!"**.
