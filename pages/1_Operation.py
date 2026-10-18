"""
Operations page of the Clinical Trials Tracker dashboard.
Needs the files created by operations_view.py.
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Operations view", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(f"output/{name}.csv")


recruiting = load("ops_recruiting_now")
attention = load("ops_attention_list")
cities = load("ops_recruiting_by_city")
duration = load("ops_duration_by_phase")
footprint = load("ops_site_footprint")

link_column = st.column_config.LinkColumn("ClinicalTrials.gov", display_text="Open")

st.title("Operations view")
st.caption("Diabetes trials with a site in India. Source: ClinicalTrials.gov. "
           "Flags are leads to check, not proof of a problem: records may be out of date.")

c1, c2, c3 = st.columns(3)
c1.metric("Recruiting now", len(recruiting))
c2.metric("Trials needing attention", attention["nct_id"].nunique())
c3.metric("Median months (completed trials)", f"{duration['median_months'].median():.0f}")

left, right = st.columns(2)
with left:
    st.subheader("Cities with the most recruiting trials")
    st.bar_chart(cities.head(10).set_index("city")["recruiting_trials"])
with right:
    st.subheader("Site footprint in India")
    st.bar_chart(footprint.set_index("sites_in_country")["trials"])

st.subheader("Typical duration by phase (completed trials)")
st.dataframe(duration, hide_index=True)

st.subheader("Trials needing attention")
flag = st.selectbox("Flag", ["All"] + sorted(attention["flag"].unique()))
shown = attention if flag == "All" else attention[attention["flag"] == flag]
st.dataframe(shown, hide_index=True, column_config={"link": link_column})

st.subheader("Trials recruiting now")
st.dataframe(recruiting, hide_index=True, column_config={"link": link_column})