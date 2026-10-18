"""
Operations view: the questions a clinical operations team asks about a
portfolio of trials.

Writes:
  output/ops_*.csv   (tables)
  images/ops_*.png   (charts)
"""
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

Path("output").mkdir(exist_ok=True)
Path("images").mkdir(exist_ok=True)

TODAY = pd.Timestamp(date.today())

df = pd.read_csv("data/trials_clean.csv", parse_dates=["start_date", "completion_date"])
raw = pd.read_csv(
    "data/trials.csv", usecols=["nct_id", "start_date", "completion_date"], dtype=str
)


def end_of_period(text):
    """'2026-10' means the whole month, so use its last day. '2026-10-05' stays as it is."""
    if pd.isna(text):
        return pd.NaT
    stamp = pd.to_datetime(text)
    return stamp + pd.offsets.MonthEnd(0) if len(text) == 7 else stamp


raw["start_end"] = pd.to_datetime(raw["start_date"].map(end_of_period))
raw["completion_end"] = pd.to_datetime(raw["completion_date"].map(end_of_period))
df = df.merge(raw[["nct_id", "start_end", "completion_end"]], on="nct_id", how="left")
df["link"] = "https://clinicaltrials.gov/study/" + df["nct_id"]

print(f"Loaded {len(df)} trials. Today is {TODAY.date()}.\n")

# ---------- 1. Recruiting now ----------
list_columns = ["nct_id", "title", "status", "phase", "sponsor", "start_date",
                "completion_date", "enrollment", "sites_in_country", "cities", "link"]
recruiting = df[df["status"] == "Recruiting"].sort_values("sites_in_country", ascending=False)
recruiting[list_columns].to_csv("output/ops_recruiting_now.csv", index=False)

# ---------- 2. Where are trials recruiting? ----------
def city_counts(frame):
    return frame["cities"].dropna().str.split("; ").explode().value_counts()


city_table = pd.DataFrame({
    "recruiting_trials": city_counts(recruiting),
    "all_trials": city_counts(df),
}).fillna(0).astype(int)
city_table = city_table.sort_values(["recruiting_trials", "all_trials"], ascending=False)
city_table.index.name = "city"
city_table.head(15).to_csv("output/ops_recruiting_by_city.csv")

# ---------- 3. Trials that need attention ----------
flags = []


def add_flag(mask, text):
    part = df[mask].copy()
    part["flag"] = text
    flags.append(part)


active = ["Recruiting", "Enrolling by invitation", "Active, not recruiting"]
add_flag(df["status"].isin(active) & (df["completion_end"] < TODAY),
         "Completion date passed but still active")
add_flag((df["status"] == "Not yet recruiting") & (df["start_end"] < TODAY),
         "Start date passed but not yet recruiting")
add_flag(df["status"] == "Unknown", "Status unknown (not verified for over 2 years)")
add_flag(df["status"] == "Suspended", "Suspended")

attention = pd.concat(flags, ignore_index=True)
attention[["flag"] + list_columns].to_csv("output/ops_attention_list.csv", index=False)
flag_counts = attention["flag"].value_counts()

# ---------- 4. How long do trials take? ----------
done = df[(df["status"] == "Completed") & df["start_date"].notna()
          & df["completion_end"].notna()].copy()
done["months"] = (done["completion_end"] - done["start_date"]).dt.days / 30.44
done = done[done["months"] > 0]
duration = done.groupby("phase")["months"].agg(trials="count", median_months="median").round(1)
duration.to_csv("output/ops_duration_by_phase.csv")

# ---------- 5. Site footprint ----------
labels = ["No India site listed", "1 site", "2 to 5 sites", "6 to 20 sites", "More than 20 sites"]
df["site_group"] = pd.cut(df["sites_in_country"], bins=[-1, 0, 1, 5, 20, float("inf")],
                          labels=labels)
footprint = df["site_group"].value_counts().reindex(labels).fillna(0).astype(int)
footprint = pd.DataFrame({"trials": footprint,
                          "percent": (footprint / len(df) * 100).round(1)})
footprint.index.name = "sites_in_country"
footprint.to_csv("output/ops_site_footprint.csv")

# ---------- 6. Sponsor workload ----------
upcoming = df[df["status"].isin(["Recruiting", "Not yet recruiting", "Enrolling by invitation"])]
busy_sponsors = upcoming["sponsor"].value_counts().head(10).rename("open_trials")
busy_sponsors.index.name = "sponsor"
busy_sponsors.to_csv("output/ops_busy_sponsors.csv")

# ---------- Print the answers ----------
print(f"Recruiting now: {len(recruiting)} trials")
print("\nTop cities for recruiting trials:")
print(city_table.head(10).to_string())
print("\nTrials that need attention (a trial can have more than one flag):")
print(flag_counts.to_string())
print(f"Unique trials flagged: {attention['nct_id'].nunique()}")
print("\nMonths from start to completion (completed trials):")
print(duration.to_string())
print("\nSite footprint in the country:")
print(footprint.to_string())
print("\nSponsors with the most open trials:")
print(busy_sponsors.to_string())

# ---------- Charts ----------
plt.figure(figsize=(9, 5))
city_table["recruiting_trials"].head(10).sort_values().plot.barh(color="#1F4E78")
plt.title("Cities with the most recruiting trials")
plt.xlabel("Recruiting trials with a site in the city")
plt.tight_layout()
plt.savefig("images/ops_recruiting_cities.png", dpi=150)
plt.close()

plt.figure(figsize=(9, 4))
flag_counts.sort_values().plot.barh(color="#C0504D")
plt.title("Trials that need attention")
plt.xlabel("Number of trials")
plt.tight_layout()
plt.savefig("images/ops_attention_flags.png", dpi=150)
plt.close()

print("\nSaved: output/ops_*.csv and images/ops_*.png")