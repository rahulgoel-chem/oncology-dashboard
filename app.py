import streamlit as st
import pandas as pd
import requests
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="Oncology AI Intelligence", layout="wide")

# -----------------------------
# FUNCTIONS
# -----------------------------

@st.cache_data(ttl=86400)
def pull_trials():

    url = "https://clinicaltrials.gov/api/v2/studies"

    params = {
        "query.cond": "cancer OR tumor OR lymphoma OR leukemia",
        "pageSize": 1000
    }

    response = requests.get(url, params=params)
    data = response.json()

    trials = []

    for study in data.get("studies", []):

        protocol = study.get("protocolSection", {})

        id_module = protocol.get("identificationModule", {})
        design_module = protocol.get("designModule", {})
        status_module = protocol.get("statusModule", {})
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        arms_module = protocol.get("armsInterventionsModule", {})

        trial_id = id_module.get("nctId")
        title = id_module.get("briefTitle")

        phase_list = design_module.get("phases", [])
        phase = ", ".join(phase_list) if phase_list else None

        interventions = arms_module.get("interventions", [])
        drug_names = [i.get("name") for i in interventions if i.get("type") == "DRUG"]
        drug_names = ", ".join(drug_names)

        status = status_module.get("overallStatus")
        sponsor = sponsor_module.get("leadSponsor", {}).get("name")

        trials.append([
            trial_id,
            title,
            phase,
            drug_names,
            status,
            sponsor
        ])

    df = pd.DataFrame(
        trials,
        columns=[
            "NCT ID",
            "Title",
            "Phase",
            "Drug",
            "Status",
            "Sponsor"
        ]
    )

    return df


# -----------------------------
# AI TAGGING FUNCTIONS
# -----------------------------

def modality_tag(drug):

    drug = str(drug).lower()

    if "car" in drug:
        return "CAR-T"
    if "adc" in drug:
        return "ADC"
    if "bispecific" in drug:
        return "Bispecific"

    return "Other"


def extract_target(text):

    targets = ["CD19", "HER2", "BCMA", "CD20", "EGFR", "CLDN18.2"]

    for t in targets:
        if re.search(t, str(text), re.IGNORECASE):
            return t

    return "Unknown"


def approval_score(phase):

    if pd.isna(phase):
        return 0.2

    if "PHASE3" in phase.upper():
        return 0.7
    if "PHASE2" in phase.upper():
        return 0.5
    if "PHASE1" in phase.upper():
        return 0.3

    return 0.2


# -----------------------------
# LOAD DATA
# -----------------------------

df = pull_trials()

df["Modality"] = df["Drug"].apply(modality_tag)
df["Target"] = df["Title"].apply(extract_target)
df["Approval_Prob"] = df["Phase"].apply(approval_score)


# -----------------------------
# DASHBOARD UI
# -----------------------------

st.title("🧬 Live Oncology Clinical Trials Intelligence")

st.write("Auto-updated from ClinicalTrials.gov")

col1, col2, col3 = st.columns(3)

col1.metric("Total Trials", len(df))
col2.metric("Sponsors", df["Sponsor"].nunique())
col3.metric("Phase 3 Trials", df[df["Phase"].str.contains("PHASE3", na=False)].shape[0])

st.dataframe(df, use_container_width=True)


# -----------------------------
# SPONSOR RANKING
# -----------------------------

st.subheader("🏆 Sponsor Pipeline Ranking")

ranking = df.groupby("Sponsor")["NCT ID"].count().sort_values(ascending=False).head(15)

st.bar_chart(ranking)


# -----------------------------
# MODALITY DISTRIBUTION
# -----------------------------

st.subheader("💊 Modality Distribution")

modality_counts = df["Modality"].value_counts()

st.bar_chart(modality_counts)


# -----------------------------
# TARGET LANDSCAPE
# -----------------------------

st.subheader("🎯 Target Landscape")

target_counts = df["Target"].value_counts()

st.bar_chart(target_counts)


# -----------------------------
# HIGH PROBABILITY TRIALS
# -----------------------------

st.subheader("🚀 High Probability Phase 3 Trials")

high_df = df[df["Approval_Prob"] > 0.6]

st.dataframe(high_df)
