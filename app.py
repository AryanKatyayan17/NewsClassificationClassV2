import streamlit as st
import json
import os
from streamlit_autorefresh import st_autorefresh

DATA_FILE = "test_classified_news.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_severity_color(severity):
    colors = {
        "Low": "green",
        "Medium": "orange",
        "High": "red",
        "Alert": "darkred"
    }
    return colors.get(severity, "gray")

st.set_page_config(page_title="Threat Intelligence Dashboard", layout="wide")

st.title("Threat Intelligence Dashboard")

st_autorefresh(interval=30 * 1000, key="datarefresh")

articles = load_data()

if not articles:
    st.warning("No data available. Run the pipeline first.")
    st.stop()

st.write(f"Total Articles: {len(articles)}")

st.sidebar.header("Filters")

all_severities = set()
all_categories = set()

for article in articles:
    classification = article.get("classification", {})
    all_severities.add(classification.get("severity", "Unknown"))
    for cat in classification.get("categories", []):
        all_categories.add(cat)

selected_severity = st.sidebar.multiselect(
    "Select Severity",
    sorted(all_severities),
    default=list(all_severities)
)

selected_categories = st.sidebar.multiselect(
    "Select Categories",
    sorted(all_categories),
    default=list(all_categories)
)

for article in articles[::-1]:  # newest first
    title = article.get("title", "No Title")
    url = article.get("url", "#")
    source = article.get("source", "Unknown")
    date = article.get("publish_date", "N/A")
    text = article.get("text", "")

    classification = article.get("classification", {})
    categories = classification.get("categories", [])
    severity = classification.get("severity", "Unknown")

    # Apply Filters
    if severity not in selected_severity:
        continue

    if not any(cat in selected_categories for cat in categories):
        continue

    severity_color = get_severity_color(severity)

    # Short preview (first 40 words)
    preview = " ".join(text.split()[:40]) + "..."

    st.markdown("---")

    # Title (clickable)
    st.markdown(f"### [{title}]({url})")

    # Source and date
    st.markdown(f"**Source:** {source} | **Date:** {date}")

    # Categories
    if categories:
        category_str = " ".join([f"`{cat}`" for cat in categories])
        st.markdown(f"**Categories:** {category_str}")

    # Severity
    st.markdown(
        f"**Severity:** <span style='color:{severity_color}; font-weight:bold;'>{severity}</span>",
        unsafe_allow_html=True
    )

    # Preview
    st.write(preview)