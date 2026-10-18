# Clinical Trials Tracker

Python tools that download clinical trial records from ClinicalTrials.gov and
analyse them like a clinical operations team: trials by status, phase, sponsor,
and location.

Current focus: **diabetes trials with a site in India**.

Data source: [ClinicalTrials.gov](https://clinicaltrials.gov), a service of the
U.S. National Library of Medicine. The data is a snapshot taken on the date
shown in `data/trials.csv` (column `downloaded_on`) and changes over time.

## Status
- [x] Phase 1: Download trial data
- [x] Phase 2: Clean and analyse
- [x] Phase 3: Dashboard
- [ ] Phase 4: Operations view
- [ ] Phase 5: Findings report

## How to run
1. `pip install -r requirements.txt`
2. `python fetch_trials.py` downloads the trials into `data/trials.csv`
3. `python analyze_trials.py` cleans the data and creates summary tables and charts
4. `streamlit run dashboard.py` opens the dashboard

## Dashboard

`dashboard.py` is a Streamlit app for exploring the trials. You can filter by
status, phase, sponsor type, where the trial runs and start year, search by
text, open any trial on ClinicalTrials.gov, and download the filtered list.

![Dashboard overview](images/dashboard_01.png)

![Dashboard trials table](images/dashboard_02.png)

## Analysis

`analyze_trials.py` cleans the downloaded data and produces summary tables in
`output/` and charts in `images/`.

![Trials by start year](images/trials_by_year.png)

![Trials by status](images/trials_by_status.png)

![Top sponsors](images/top_sponsors.png)