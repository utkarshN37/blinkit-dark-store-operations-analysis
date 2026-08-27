import pandas as pd
import streamlit as st

from insight_detection import detect_insights


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Blinkit Operations Intelligence",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    file_path = "../data/raw/damaged_products.csv"

    return pd.read_csv(file_path)


# ============================================================
# RUN ANALYTICS
# ============================================================

df_damage = load_data()

insights = detect_insights(df_damage)


# ============================================================
# HEADER
# ============================================================

st.title("📊 Blinkit Operations Intelligence")

st.markdown(
    """
    **AI-powered operational analytics for Blinkit dark stores**

    Analyze operational losses, identify key drivers, and generate
    business-focused insights using Python analytics and local AI.
    """
)

st.divider()


# ============================================================
# KPI SECTION
# ============================================================

overall = insights["overall"]

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        label="Total Loss",
        value=f"₹{overall['total_loss']:,.1f}"
    )


with col2:

    st.metric(
        label="Incidents",
        value=f"{overall['total_incidents']:,}"
    )


with col3:

    st.metric(
        label="Damaged Units",
        value=f"{overall['total_damaged_units']:,}"
    )


with col4:

    st.metric(
        label="Stores Affected",
        value=f"{overall['stores_affected']:,}"
    )


# ============================================================
# AUTOMATED INSIGHTS
# ============================================================

st.divider()

st.subheader("🔎 Automated Insights")


flags = insights["automatic_flags"]


if flags:

    for flag in flags:

        if flag["priority"] == "high":

            st.error(
                f"🔴 {flag['message']}"
            )

        elif flag["priority"] == "medium":

            st.warning(
                f"🟡 {flag['message']}"
            )

        else:

            st.info(
                f"🟢 {flag['message']}"
            )

else:

    st.info(
        "No significant automated findings detected."
    )


# ============================================================
# KEY BUSINESS METRICS
# ============================================================

st.divider()

st.subheader("📌 Key Business Findings")


store = insights["highest_loss_store"]
reason = insights["top_loss_reason"]
category = insights["top_category"]
pareto = insights["pareto"]


metric_col1, metric_col2, metric_col3 = st.columns(3)


with metric_col1:

    st.metric(
        label="Highest-Loss Store",
        value=store["store_id"],
        delta=f"₹{store['loss']:,.0f}"
    )

    st.caption(
        f"{store['loss_pct']:.2f}% of total loss"
    )


with metric_col2:

    st.metric(
        label="Top Loss Driver",
        value=reason["reason"],
        delta=f"₹{reason['loss']:,.0f}"
    )

    st.caption(
        f"{reason['loss_pct']:.2f}% of total loss"
    )


with metric_col3:

    st.metric(
        label="Top Product Category",
        value=category["category"],
        delta=f"₹{category['loss']:,.0f}"
    )


st.info(
    f"**Pareto finding:** The top {pareto['number_of_causes']} "
    f"damage reasons account for {pareto['loss_percentage']:.2f}% "
    f"of total losses."
)


# ============================================================
# AI EXECUTIVE BRIEF
# ============================================================

st.divider()

st.subheader("🤖 AI Executive Brief")

st.info(
    "AI insight generation will be connected here next."
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Blinkit Dark Store Operations Intelligence • "
    "Python + Pandas + Power BI + Ollama"
)