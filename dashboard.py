"""
Clinical Trials Tracker dashboard.
Run with: streamlit run dashboard.py
Data source: ClinicalTrials.gov (a service of the U.S. National Library of Medicine)
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Clinical Trials Tracker", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_csv("data/trials_clean.csv", parse_dates=["start_date", "completion_date"])
    df["link"] = "https://clinicaltrials.gov/study/" + df["nct_id"]
    return df


df = load_data()

st.title("Clinical Trials Tracker")
st.caption(
    "Diabetes trials with a site in India. "
    f"Source: ClinicalTrials.gov, data downloaded on {df['downloaded_on'].iloc[0]}."
)

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")


def multi(label, column):
    options = sorted(df[column].dropna().unique())
    return st.sidebar.multiselect(label, options, default=options)


statuses = multi("Status", "status")
phases = multi("Phase", "phase")
sponsor_classes = multi("Sponsor type", "sponsor_class")
scopes = multi("Where the trial runs", "scope")

years = df["start_year"].dropna().astype(int)
year_range = st.sidebar.slider(
    "Start year", int(years.min()), int(years.max()), (int(years.min()), int(years.max()))
)
include_no_date = st.sidebar.checkbox("Include trials with no start date", value=True)
search = st.sidebar.text_input("Search title, condition, sponsor or city")

filtered = df[
    df["status"].isin(statuses)
    & df["phase"].isin(phases)
    & df["sponsor_class"].isin(sponsor_classes)
    & df["scope"].isin(scopes)
]
in_range = filtered["start_year"].between(year_range[0], year_range[1])
if include_no_date:
    in_range = in_range | filtered["start_year"].isna()
filtered = filtered[in_range]

if search:
    text = (
        filtered["title"].fillna("") + " " + filtered["conditions"].fillna("") + " "
        + filtered["sponsor"].fillna("") + " " + filtered["cities"].fillna("")
    )
    filtered = filtered[text.str.contains(search, case=False, regex=False)]

if filtered.empty:
    st.warning("No trials match these filters.")
    st.stop()

# ---------- Headline numbers ----------
finished = filtered[filtered["status"].isin(["Completed", "Terminated", "Withdrawn"])]
stopped = finished["status"].isin(["Terminated", "Withdrawn"]).mean() * 100 if len(finished) else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trials shown", len(filtered))
c2.metric("Recruiting now", int((filtered["status"] == "Recruiting").sum()))
c3.metric("Median enrollment", f"{filtered['enrollment'].median():.0f}")
c4.metric("Stopped early (of finished)", f"{stopped:.0f}%")

# ---------- Charts ----------
left, right = st.columns(2)
with left:
    st.subheader("Trials by status")
    st.bar_chart(filtered["status"].value_counts())
    st.subheader("Trials by start year")
    st.bar_chart(filtered["start_year"].dropna().astype(int).value_counts().sort_index())
with right:
    st.subheader("Trials by phase")
    st.bar_chart(filtered["phase"].value_counts())
    st.subheader("Top 10 sponsors")
    st.bar_chart(filtered["sponsor"].value_counts().head(10))

st.subheader("Top 10 cities in India")
cities = filtered["cities"].dropna().str.split("; ").explode().value_counts().head(10)
st.bar_chart(cities)
st.caption("A trial is counted once for each city where it has a site.")

# ---------- Table ----------
st.subheader("Trials")
columns = ["nct_id", "title", "status", "phase", "sponsor", "start_date",
           "enrollment", "sites_in_country", "cities", "link"]
st.dataframe(
    filtered[columns],
    hide_index=True,
    column_config={
        "link": st.column_config.LinkColumn("ClinicalTrials.gov", display_text="Open"),
        "start_date": st.column_config.DateColumn("start_date", format="YYYY-MM-DD"),
    },
)

st.download_button(
    "Download filtered trials (CSV)",
    filtered.to_csv(index=False),
    file_name="filtered_trials.csv",
    mime="text/csv",
)