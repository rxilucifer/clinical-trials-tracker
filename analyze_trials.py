"""
Cleans data/trials.csv and answers basic clinical operations questions.

Writes:
  data/trials_clean.csv
  output/*.csv    (summary tables)
  images/*.png    (charts)
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

COUNTRY = "India"  # keep the same as in fetch_trials.py

Path("output").mkdir(exist_ok=True)
Path("images").mkdir(exist_ok=True)

df = pd.read_csv("data/trials.csv")
print(f"Loaded {len(df)} trials\n")

# ---------- 1. Clean ----------
status_labels = {
    "COMPLETED": "Completed", "UNKNOWN": "Unknown", "TERMINATED": "Terminated",
    "RECRUITING": "Recruiting", "ACTIVE_NOT_RECRUITING": "Active, not recruiting",
    "WITHDRAWN": "Withdrawn", "NOT_YET_RECRUITING": "Not yet recruiting",
    "SUSPENDED": "Suspended", "ENROLLING_BY_INVITATION": "Enrolling by invitation",
    "AVAILABLE": "Available",
}
df["status"] = df["status"].map(status_labels).fillna(df["status"])

# Trap: pandas reads the text "NA" (no phase) as an empty value, so put it back
df["phase"] = df["phase"].fillna("NA")
phase_labels = {
    "PHASE1": "Phase 1", "PHASE2": "Phase 2", "PHASE3": "Phase 3",
    "PHASE4": "Phase 4", "PHASE1/PHASE2": "Phase 1/2",
    "PHASE2/PHASE3": "Phase 2/3", "EARLY_PHASE1": "Early phase 1",
    "NA": "Not applicable",
}
df["phase"] = df["phase"].map(phase_labels).fillna(df["phase"])

sponsor_labels = {
    "INDUSTRY": "Industry", "OTHER": "Other (e.g. universities, hospitals)",
    "NIH": "Government", "FED": "Government", "OTHER_GOV": "Government",
    "NETWORK": "Network", "INDIV": "Individual", "UNKNOWN": "Unknown",
}
df["sponsor_class"] = df["sponsor_class"].map(sponsor_labels).fillna(df["sponsor_class"])

# Dates come as "2022-03" or "2022-03-15", so allow mixed formats
df["start_date"] = pd.to_datetime(df["start_date"], format="mixed", errors="coerce")
df["completion_date"] = pd.to_datetime(df["completion_date"], format="mixed", errors="coerce")
df["start_year"] = df["start_date"].dt.year
df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce")


def trial_scope(row):
    """Is the trial run only in the country, or in other countries too?"""
    if row["sites_total"] == 0:
        return "No sites listed"
    if row["sites_in_country"] == 0:
        return f"No {COUNTRY} site listed"
    if row["sites_in_country"] == row["sites_total"]:
        return f"{COUNTRY} only"
    return f"{COUNTRY} and other countries"


df["scope"] = df.apply(trial_scope, axis=1)
df.to_csv("data/trials_clean.csv", index=False)

# ---------- 2. How complete is the data? ----------
key_columns = ["start_date", "completion_date", "enrollment", "phase", "sponsor", "cities"]
missing = df[key_columns].isna().sum().rename("missing")
missing_table = pd.DataFrame({"missing": missing, "percent": (missing / len(df) * 100).round(1)})
missing_table.index.name = "column"
missing_table.to_csv("output/missing_values.csv")
print("Missing values:")
print(missing_table.to_string(), "\n")


# ---------- 3. Summary tables ----------
def count_table(column):
    counts = df[column].value_counts()
    table = pd.DataFrame({"trials": counts, "percent": (counts / len(df) * 100).round(1)})
    table.index.name = column
    table.to_csv(f"output/by_{column}.csv")
    return table


for column in ["status", "phase", "sponsor_class", "scope"]:
    print(f"Trials by {column}:")
    print(count_table(column).to_string(), "\n")

top_sponsors = df["sponsor"].value_counts().head(10).rename("trials")
top_sponsors.index.name = "sponsor"
top_sponsors.to_csv("output/top_sponsors.csv")
print("Top 10 sponsors:")
print(top_sponsors.to_string(), "\n")

enrollment_by_phase = (
    df.groupby("phase")["enrollment"].agg(["count", "median", "max"]).round(0)
)
enrollment_by_phase.to_csv("output/enrollment_by_phase.csv")
print("Enrollment by phase (planned or actual participants):")
print(enrollment_by_phase.to_string(), "\n")

year_counts = df["start_year"].dropna().astype(int).value_counts().sort_index()
year_counts.rename("trials").to_csv("output/trials_by_start_year.csv")

# ---------- 4. Questions a clinical operations team would ask ----------
finished = df[df["status"].isin(["Completed", "Terminated", "Withdrawn"])]
stopped_share = finished["status"].isin(["Terminated", "Withdrawn"]).mean() * 100
ongoing = df["status"].isin(
    ["Recruiting", "Not yet recruiting", "Enrolling by invitation", "Active, not recruiting"]
).sum()

print("Quick answers:")
print(f"- Trials in total: {len(df)}")
print(f"- Still ongoing (recruiting, about to start, or active): {ongoing}")
print(f"- Of {len(finished)} finished trials, {stopped_share:.1f}% were stopped early (terminated or withdrawn)")
print(f"- Status 'Unknown' (not updated for over 2 years): {(df['status'] == 'Unknown').sum()}")
print(f"- Trials run only in {COUNTRY}: {(df['scope'] == f'{COUNTRY} only').sum()}")
print(f"- Median planned or actual enrollment: {df['enrollment'].median():.0f} participants")

# ---------- 5. Charts ----------
plt.figure(figsize=(9, 5))
year_counts.plot.bar(color="#1F4E78")
plt.title(f"Trials by start year ({COUNTRY} sites)")
plt.xlabel("Start year")
plt.ylabel("Number of trials")
plt.tight_layout()
plt.savefig("images/trials_by_year.png", dpi=150)
plt.close()

plt.figure(figsize=(9, 5))
df["status"].value_counts().sort_values().plot.barh(color="#1F4E78")
plt.title("Trials by status")
plt.xlabel("Number of trials")
plt.tight_layout()
plt.savefig("images/trials_by_status.png", dpi=150)
plt.close()

plt.figure(figsize=(10, 5))
top_sponsors.sort_values().plot.barh(color="#1F4E78")
plt.title("Top 10 sponsors")
plt.xlabel("Number of trials")
plt.tight_layout()
plt.savefig("images/top_sponsors.png", dpi=150)
plt.close()

print("\nSaved: data/trials_clean.csv, output/*.csv, images/*.png")