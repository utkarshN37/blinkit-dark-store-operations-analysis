import pandas as pd
import streamlit as st

from insight_detection import detect_insights
from ai_insights import (
    generate_ai_insight,
    validate_ai_output,
    create_fallback_insight,
    check_ollama_available
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Blinkit Operations Intelligence",
    page_icon="📊",
    layout="wide"
)



# ============================================================
# LOAD DATA & RUN ANALYTICS
# ============================================================

@st.cache_data
def load_data():

    file_path = "../data/raw/damaged_products.csv"

    return pd.read_csv(file_path)


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

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        label="Total Loss",
        value=f"₹{overall['total_loss']:,.2f}"
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


with col5:

    st.metric(
        label="Annual Loss Projection",
        value=f"₹{overall['annual_loss_projection']:,.2f}"
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
# VERIFIED BUSINESS METRICS
# ============================================================

st.divider()

st.subheader("📌 Verified Business Metrics")


store = insights["highest_loss_store"]
reason = insights["top_loss_reason"]
category = insights["top_category"]
pareto = insights["pareto"]
consolidated_savings = insights["savings_opportunity"]["consolidated"]


v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)


with v_col1:

    st.metric(
        label="Total Loss",
        value=f"₹{overall['total_loss']:,.2f}"
    )


with v_col2:

    st.metric(
        label="Highest-Loss Store",
        value=store["store_id"],
        delta=f"₹{store['loss']:,.2f} ({store['loss_pct']:.1f}%)"
    )


with v_col3:

    st.metric(
        label="Top Loss Driver",
        value=reason["reason"],
        delta=f"₹{reason['loss']:,.2f} ({reason['loss_pct']:.1f}%)"
    )


with v_col4:

    st.metric(
        label="Monthly Savings",
        value=f"₹{consolidated_savings['monthly_savings']:,.2f}"
    )


with v_col5:

    st.metric(
        label="Annual Savings",
        value=f"₹{consolidated_savings['annual_savings']:,.2f}"
    )


st.info(
    f"**Pareto Finding:** The top {pareto['number_of_causes']} damage reasons "
    f"account for {pareto['loss_percentage']:.2f}% of total losses. "
    f"Top Product Category: **{category['category']}** (₹{category['loss']:,.2f})."
)


# ============================================================
# SAVINGS & ROI OPPORTUNITY (VERIFIED PYTHON METRICS)
# ============================================================

st.divider()

st.subheader("💰 Savings & ROI Opportunity")


s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)


with s_col1:

    st.metric(
        label="Monthly Savings",
        value=f"₹{consolidated_savings['monthly_savings']:,.2f}"
    )


with s_col2:

    st.metric(
        label="Annual Savings",
        value=f"₹{consolidated_savings['annual_savings']:,.2f}"
    )


with s_col3:

    st.metric(
        label="Estimated Loss Reduction",
        value=f"{consolidated_savings['estimated_loss_reduction_pct']}%"
    )


with s_col4:

    st.metric(
        label="Implementation Timeline",
        value=str(consolidated_savings["implementation_timeline"])
    )


with s_col5:

    st.metric(
        label="Confidence",
        value=str(consolidated_savings["confidence"])
    )


# ============================================================
# AI EXECUTIVE BRIEF
# ============================================================

st.divider()

st.subheader("🤖 AI Executive Brief")

ollama_online = check_ollama_available()


if not ollama_online:
    st.info(
        "💡 **AI Executive Brief is available in the local desktop version because Ollama runs locally.** "
        "Displaying verified deterministic Python analytical insights below for cloud deployment."
    )

    fallback_brief = create_fallback_insight(insights)

    st.markdown("### Key Finding")
    st.write(fallback_brief.get("key_finding", ""))

    st.markdown("### Why It Matters")
    st.write(fallback_brief.get("why_it_matters", ""))

    st.markdown("### Priority Actions")
    actions = fallback_brief.get("priority_actions", [])
    if isinstance(actions, list):
        for act in actions:
            st.markdown(f"- {act}")
    else:
        st.write(actions)

    st.markdown("### Business Impact")
    st.write(fallback_brief.get("business_impact", ""))

    st.markdown("### Savings Opportunity")
    st.success(fallback_brief.get("savings_opportunity", ""))

else:
    st.markdown(
        "Generate an executive summary interpreting verified analytical findings using local AI (Ollama - Llama 3.2 3B)."
    )

    if "ai_brief" not in st.session_state:
        st.session_state["ai_brief"] = None
        st.session_state["is_fallback"] = False

    if st.button("Generate AI Executive Brief", type="primary"):
        with st.spinner("🤖 Connecting to local AI (Ollama - Llama 3.2 3B)..."):
            try:
                raw_ai_output = generate_ai_insight(insights)
                brief, errors = validate_ai_output(raw_ai_output, insights)

                if errors or not brief:
                    st.session_state["ai_brief"] = create_fallback_insight(insights)
                    st.session_state["is_fallback"] = True
                else:
                    st.session_state["ai_brief"] = brief
                    st.session_state["is_fallback"] = False

            except Exception as e:
                st.session_state["ai_brief"] = create_fallback_insight(insights)
                st.session_state["is_fallback"] = True

    brief = st.session_state.get("ai_brief")

    if brief:
        if st.session_state.get("is_fallback"):
            st.warning(
                "⚠️ Ollama model output failed validation or encountered an error. Displaying verified qualitative Python fallback brief."
            )

        st.markdown("### Key Finding")
        st.write(brief.get("key_finding", ""))

        st.markdown("### Why It Matters")
        st.write(brief.get("why_it_matters", ""))

        st.markdown("### Priority Actions")
        actions = brief.get("priority_actions", [])
        if isinstance(actions, list):
            for act in actions:
                st.markdown(f"- {act}")
        else:
            st.write(actions)

        st.markdown("### Business Impact")
        st.write(brief.get("business_impact", ""))

        st.markdown("### Savings Opportunity")
        savings_opp = brief.get("savings_opportunity", "")
        if isinstance(savings_opp, dict):
            sav_items = [f"**{k.replace('_', ' ').title()}**: {v}" for k, v in savings_opp.items()]
            st.success(" • ".join(sav_items))
        else:
            st.success(str(savings_opp))


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Blinkit Dark Store Operations Intelligence • "
    "Python + Pandas + Power BI + Ollama"
)

