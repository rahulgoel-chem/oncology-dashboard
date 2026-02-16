import streamlit as st
import pandas as pd

st.set_page_config(page_title="Oncology Intelligence Dashboard")

st.title("🧬 Oncology Clinical Trial Intelligence Dashboard")

# Load dataset
df = pd.read_csv("trials.csv")

st.subheader("Dataset Preview")
st.dataframe(df)

st.subheader("Phase Distribution")
st.bar_chart(df["Phase"].value_counts())

st.subheader("Sponsor Distribution")
st.bar_chart(df["Sponsor"].value_counts())
