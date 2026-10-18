"""
Downloads clinical trials from ClinicalTrials.gov (public API v2)
and saves them as data/trials.csv.

Change CONDITION and COUNTRY below to track a different area.
Source: ClinicalTrials.gov, a service of the U.S. National Library of Medicine.
"""
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

CONDITION = "diabetes"
COUNTRY = "India"
MAX_TRIALS = 1000

URL = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = [
    "NCTId", "BriefTitle", "OverallStatus", "StudyType", "Phase",
    "StartDate", "CompletionDate", "EnrollmentCount", "Condition",
    "LeadSponsorName", "LeadSponsorClass",
    "LocationCity", "LocationCountry",
]


def fetch_all():
    """Ask the API for trials, one page at a time."""
    params = {
        "query.cond": CONDITION,
        "query.locn": COUNTRY,
        "fields": "|".join(FIELDS),
        "pageSize": 200,
        "countTotal": "true",
        "format": "json",
    }
    studies = []
    while len(studies) < MAX_TRIALS:
        response = requests.get(URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        if not studies and "totalCount" in data:
            print(f"Trials matching the search: {data['totalCount']}")
        studies.extend(data.get("studies", []))
        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
        time.sleep(0.3)  # be gentle with the server
    return studies[:MAX_TRIALS]


def flatten(study):
    """Turn one nested trial record into one flat row."""
    p = study.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    conditions = p.get("conditionsModule", {}).get("conditions", [])
    sponsor = p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {})
    locations = p.get("contactsLocationsModule", {}).get("locations", [])
    in_country = [loc for loc in locations if loc.get("country") == COUNTRY]

    return {
        "nct_id": ident.get("nctId"),
        "title": ident.get("briefTitle"),
        "status": status.get("overallStatus"),
        "study_type": design.get("studyType"),
        "phase": "/".join(design.get("phases", [])) or "NA",
        "start_date": status.get("startDateStruct", {}).get("date"),
        "completion_date": status.get("completionDateStruct", {}).get("date"),
        "enrollment": design.get("enrollmentInfo", {}).get("count"),
        "conditions": "; ".join(conditions),
        "sponsor": sponsor.get("name"),
        "sponsor_class": sponsor.get("class"),
        "sites_total": len(locations),
        "sites_in_country": len(in_country),
        "cities": "; ".join(sorted({loc["city"] for loc in in_country if loc.get("city")})),
        "downloaded_on": date.today().isoformat(),
    }


if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)

    studies = fetch_all()
    df = pd.DataFrame([flatten(s) for s in studies])
    df.to_csv("data/trials.csv", index=False)

    print(f"Saved {len(df)} trials to data/trials.csv")
    print("\nBy status:")
    print(df["status"].value_counts().to_string())
    print("\nBy phase:")
    print(df["phase"].value_counts().to_string())