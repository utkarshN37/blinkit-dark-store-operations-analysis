import os
from pathlib import Path

import pandas as pd
import streamlit as st

from insight_detection import detect_insights
from ai_insights import (
    check_ollama_available,
    generate_ai_insight,
    validate_ai_output,
    create_fallback_insight,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Blinkit Operations Intelligence",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load the Blinkit damaged-products dataset using a path
    that works locally and on Streamlit Cloud.
    """

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "data"
        / "raw"
        / "damaged_products.csv"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {file_path}"
        )

    return pd.read_csv(file_path)


# ============================================================
# LOAD + ANALYZE
# ============================================================

try:

    df_damage = load_data()

    insights = detect_insights(
        df_damage
    )

except Exception as e:

    st.error(
        f"Unable to load or analyze the Blinkit dataset: {e}"
    )

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title(
    "📊 Blinkit Operations Intelligence"
)

st.markdown(
    """
    **AI-powered operational analytics for Blinkit dark stores**

    Analyze operational losses, identify key drivers, and generate
    business-focused insights using Python analytics and local AI.
    """
)

st.divider()


# ============================================================
# VERIFIED KPI SECTION
# ============================================================

overall = insights["overall"]

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        label="Total Loss",
        value=f"₹{overall['total_loss']:,.2f}",
    )


with col2:

    st.metric(
        label="Incidents",
        value=f"{overall['total_incidents']:,}",
    )


with col3:

    st.metric(
        label="Damaged Units",
        value=f"{overall['total_damaged_units']:,}",
    )


with col4:

    st.metric(
        label="Stores Affected",
        value=f"{overall['stores_affected']:,}",
    )


with col5:

    st.metric(
        label="Annual Loss Projection",
        value=f"₹{overall['annual_loss_projection']:,.2f}",
    )


# ============================================================
# AUTOMATED INSIGHTS
# ============================================================

st.divider()

st.subheader("🔎 Automated Insights")

flags = insights.get(
    "automatic_flags",
    []
)


if flags:

    for flag in flags:

        priority = flag.get(
            "priority",
            "medium"
        ).lower()

        message = flag.get(
            "message",
            ""
        )

        if priority == "high":

            st.error(
                f"🔴 {message}"
            )

        elif priority == "medium":

            st.warning(
                f"🟡 {message}"
            )

        else:

            st.info(
                f"🟢 {message}"
            )

else:

    st.info(
        "No significant automated findings detected."
    )


# ============================================================
# VERIFIED BUSINESS METRICS
# ============================================================

st.divider()

st.subheader(
    "📌 Verified Business Metrics"
)

store = insights[
    "highest_loss_store"
]

reason = insights[
    "top_loss_reason"
]

category = insights[
    "top_category"
]

pareto = insights[
    "pareto"
]

location = insights[
    "location_concentration"
]


metric_col1, metric_col2, metric_col3 = st.columns(3)


with metric_col1:

    st.metric(
        label="Highest-Loss Store",
        value=store["store_id"],
    )

    st.caption(
        f"₹{store['loss']:,.2f} "
        f"({store['loss_pct']:.2f}% of total loss)"
    )


with metric_col2:

    st.metric(
        label="Top Loss Driver",
        value=reason["reason"],
    )

    st.caption(
        f"₹{reason['loss']:,.2f} "
        f"({reason['loss_pct']:.2f}% of total loss)"
    )


with metric_col3:

    st.metric(
        label="Top Product Category",
        value=category["category"],
    )

    st.caption(
        f"₹{category['loss']:,.2f} in losses"
    )


st.info(
    f"**Pareto Finding:** The top "
    f"{pareto['number_of_causes']} damage reasons account for "
    f"{pareto['loss_percentage']:.2f}% of total losses."
)


# ============================================================
# SAVINGS & ROI
# ============================================================

st.divider()

st.subheader(
    "💰 Savings & ROI Opportunity"
)

savings = insights[
    "savings_opportunity"
]["consolidated"]


roi_col1, roi_col2, roi_col3 = st.columns(3)


with roi_col1:

    st.metric(
        label="Monthly Savings",
        value=f"₹{savings['monthly_savings']:,.2f}",
    )


with roi_col2:

    st.metric(
        label="Annual Savings",
        value=f"₹{savings['annual_savings']:,.2f}",
    )


with roi_col3:

    st.metric(
        label="Estimated Loss Reduction",
        value=f"{savings['estimated_loss_reduction_pct']:.1f}%",
    )


roi_col4, roi_col5 = st.columns(2)


with roi_col4:

    st.metric(
        label="Implementation Timeline",
        value=savings[
            "implementation_timeline"
        ],
    )


with roi_col5:

    st.metric(
        label="Confidence",
        value=savings[
            "confidence"
        ],
    )


# ============================================================
# AI EXECUTIVE BRIEF
# ============================================================

st.divider()

st.subheader(
    "🤖 AI Executive Brief"
)

st.markdown(
    """
    Generate an executive summary interpreting verified analytical
    findings using local AI (Ollama - Llama 3.2 3B).
    """
)


# ------------------------------------------------------------
# Detect local Ollama
# ------------------------------------------------------------

ollama_available = check_ollama_available()


if ollama_available:

    if st.button(
        "Generate AI Executive Brief",
        type="primary"
    ):

        with st.spinner(
            "Generating business insight with Ollama..."
        ):

            try:

                ai_output = generate_ai_insight(
                    insights
                )

                validated_output, validation_errors = (
                    validate_ai_output(
                        ai_output,
                        insights
                    )
                )

                # ------------------------------------------------
                # Use fallback if AI output is unreliable
                # ------------------------------------------------

                if validation_errors:

                    validated_output = (
                        create_fallback_insight(
                            insights
                        )
                    )

                    st.warning(
                        "AI response required validation fallback. "
                        "Verified Python analytics are being shown."
                    )

                # ------------------------------------------------
                # Key Finding
                # ------------------------------------------------

                st.markdown(
                    "### 📌 Key Finding"
                )

                st.write(
                    validated_output[
                        "key_finding"
                    ]
                )

                # ------------------------------------------------
                # Why It Matters
                # ------------------------------------------------

                st.markdown(
                    "### 🎯 Why It Matters"
                )

                st.write(
                    validated_output[
                        "why_it_matters"
                    ]
                )

                # ------------------------------------------------
                # Priority Actions
                # ------------------------------------------------

                st.markdown(
                    "### 📋 Priority Actions"
                )

                for action in validated_output[
                    "priority_actions"
                ]:

                    st.markdown(
                        f"- {action}"
                    )

                # ------------------------------------------------
                # Business Impact
                # ------------------------------------------------

                st.markdown(
                    "### ⚡ Business Impact"
                )

                st.write(
                    validated_output[
                        "business_impact"
                    ]
                )

                # ------------------------------------------------
                # Savings Opportunity
                # ------------------------------------------------

                st.markdown(
                    "### 💰 Savings Opportunity"
                )

                st.success(
                    validated_output[
                        "savings_opportunity"
                    ]
                )

            except Exception as e:

                st.error(
                    f"AI generation failed: {e}"
                )

else:

    # ------------------------------------------------------------
    # CLOUD / NO OLLAMA MODE
    # ------------------------------------------------------------

    st.info(
        """
        💡 **AI Executive Brief is available in the local desktop
        version because Ollama runs locally.**

        The verified Python analytical findings below remain available
        in this deployment.
        """
    )

    fallback = create_fallback_insight(
        insights
    )

    # ------------------------------------------------------------
    # Key Finding
    # ------------------------------------------------------------

    st.markdown(
        "### 📌 Key Finding"
    )

    st.write(
        fallback[
            "key_finding"
        ]
    )

    # ------------------------------------------------------------
    # Why It Matters
    # ------------------------------------------------------------

    st.markdown(
        "### 🎯 Why It Matters"
    )

    st.write(
        fallback[
            "why_it_matters"
        ]
    )

    # ------------------------------------------------------------
    # Priority Actions
    # ------------------------------------------------------------

    st.markdown(
        "### 📋 Priority Actions"
    )

    for action in fallback[
        "priority_actions"
    ]:

        st.markdown(
            f"- {action}"
        )

    # ------------------------------------------------------------
    # Business Impact
    # ------------------------------------------------------------

    st.markdown(
        "### ⚡ Business Impact"
    )

    st.write(
        fallback[
            "business_impact"
        ]
    )

    # ------------------------------------------------------------
    # Savings Opportunity
    # ------------------------------------------------------------

    st.markdown(
        "### 💰 Savings Opportunity"
    )

    st.success(
        fallback[
            "savings_opportunity"
        ]
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Blinkit Dark Store Operations Intelligence • "
    "Python + Pandas + Power BI + Ollama"
)