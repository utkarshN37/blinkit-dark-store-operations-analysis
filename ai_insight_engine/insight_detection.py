import pandas as pd


# ============================================================
# BLINKIT INSIGHT DETECTION ENGINE
# ============================================================
# Purpose:
# Convert Blinkit operational data into verified,
# structured analytical findings for the AI layer.
#
# IMPORTANT:
# This file performs the calculations.
# The LLM should only explain the results.
# ============================================================


def detect_insights(df_damage: pd.DataFrame) -> dict:
    """
    Detect business insights and ROI opportunities from
    Blinkit damaged-products data.

    Parameters
    ----------
    df_damage : pd.DataFrame
        Blinkit damaged products dataset.

    Returns
    -------
    dict
        Structured, verified analytical findings.
    """

    # ========================================================
    # 0. DATA VALIDATION
    # ========================================================

    required_columns = [
        "damage_id",
        "store_id",
        "quantity_damaged",
        "total_loss_value",
        "damage_reason",
        "category",
        "severity",
        "reported_by_emp_id",
        "reported_by_emp_name"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df_damage.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df_damage.empty:
        raise ValueError(
            "Blinkit damage dataset is empty."
        )

    # Work on a copy so the original DataFrame is unchanged
    df = df_damage.copy()

    # ========================================================
    # 1. OVERALL KPIs
    # ========================================================

    total_loss = df["total_loss_value"].sum()

    total_incidents = df["damage_id"].nunique()

    total_damaged_units = df["quantity_damaged"].sum()

    avg_loss_per_incident = (
        total_loss / total_incidents
        if total_incidents > 0
        else 0
    )

    unique_stores = df["store_id"].nunique()

    # Your notebook uses a 3-month analysis period for
    # monthly and annual projections.
    analysis_months = 3

    monthly_loss = total_loss / analysis_months

    annual_loss_projection = monthly_loss * 12

    # ========================================================
    # 2. STORE ANALYSIS
    # ========================================================

    store_loss = (
        df.groupby("store_id")
        .agg(
            total_loss=("total_loss_value", "sum"),
            incidents=("damage_id", "nunique")
        )
        .reset_index()
        .sort_values(
            "total_loss",
            ascending=False
        )
    )

    store_loss["loss_pct"] = (
        store_loss["total_loss"]
        / total_loss
        * 100
    )

    # Highest-loss store
    highest_store = store_loss.iloc[0]

    # Top 3 stores
    top_3_stores = store_loss.head(3)

    top_3_stores_loss = (
        top_3_stores["total_loss"].sum()
    )

    top_3_stores_pct = (
        top_3_stores_loss
        / total_loss
        * 100
    )

    # ========================================================
    # 3. DAMAGE-REASON / ROOT-CAUSE ANALYSIS
    # ========================================================

    damage_by_reason = (
        df.groupby("damage_reason")
        .agg(
            total_loss=("total_loss_value", "sum"),
            total_qty=("quantity_damaged", "sum"),
            incidents=("damage_id", "nunique"),
            avg_loss_per_unit=("unit_price", "mean")
        )
        .reset_index()
        .sort_values(
            "total_loss",
            ascending=False
        )
    )

    damage_by_reason["loss_pct"] = (
        damage_by_reason["total_loss"]
        / total_loss
        * 100
    )

    damage_by_reason["cumulative_pct"] = (
        damage_by_reason["loss_pct"].cumsum()
    )

    # Largest individual loss driver
    top_reason = damage_by_reason.iloc[0]

    # Top 3 root causes
    top_3_reasons = damage_by_reason.head(3)

    top_3_reason_loss = (
        top_3_reasons["total_loss"].sum()
    )

    top_3_reason_pct = (
        top_3_reason_loss
        / total_loss
        * 100
    )

    # Causes contributing to approximately 80% of losses
    pareto_causes = damage_by_reason[
        damage_by_reason["cumulative_pct"] <= 80
    ]

    # Handle the case where the first category itself exceeds 80%
    if pareto_causes.empty:
        pareto_causes = damage_by_reason.head(1)

    pareto_loss = (
        pareto_causes["total_loss"].sum()
    )

    pareto_loss_pct = (
        pareto_loss
        / total_loss
        * 100
    )

    # ========================================================
    # 4. CATEGORY ANALYSIS
    # ========================================================

    loss_by_category = (
        df.groupby("category")
        .agg(
            total_loss=("total_loss_value", "sum"),
            incidents=("damage_id", "nunique")
        )
        .reset_index()
        .sort_values(
            "total_loss",
            ascending=False
        )
    )

    loss_by_category["loss_pct"] = (
        loss_by_category["total_loss"]
        / total_loss
        * 100
    )

    top_category = loss_by_category.iloc[0]

    # ========================================================
    # 5. SEVERITY ANALYSIS
    # ========================================================

    loss_by_severity = (
        df.groupby("severity")
        .agg(
            total_loss=("total_loss_value", "sum"),
            incidents=("damage_id", "nunique"),
            avg_loss=("total_loss_value", "mean")
        )
        .reset_index()
        .sort_values(
            "total_loss",
            ascending=False
        )
    )

    loss_by_severity["loss_pct"] = (
        loss_by_severity["total_loss"]
        / total_loss
        * 100
    )

    highest_loss_severity = (
        loss_by_severity.iloc[0]
    )

    # ========================================================
    # 6. EMPLOYEE ANALYSIS
    # ========================================================
    # Uses the same reported employee information available
    # in the notebook's damage-level analysis.
    # ========================================================

    loss_by_employee = (
        df.groupby(
            [
                "reported_by_emp_id",
                "reported_by_emp_name"
            ]
        )
        .agg(
            total_loss=("total_loss_value", "sum"),
            incidents=("damage_id", "nunique")
        )
        .reset_index()
        .sort_values(
            "total_loss",
            ascending=False
        )
    )

    loss_by_employee["loss_pct"] = (
        loss_by_employee["total_loss"]
        / total_loss
        * 100
    )

    # Top 5 employee loss concentration
    top_5_employees = loss_by_employee.head(5)

    top_5_employee_loss = (
        top_5_employees["total_loss"].sum()
    )

    top_5_employee_pct = (
        top_5_employee_loss
        / total_loss
        * 100
    )

    # High-risk employees: same threshold used in notebook
    high_risk_employees = loss_by_employee[
        loss_by_employee["total_loss"] > 20000
    ]

    high_risk_employee_loss = (
        high_risk_employees["total_loss"].sum()
    )

    # ========================================================
    # 7. TEMPERATURE-BREACH ANALYSIS
    # ========================================================

    temperature_breach_loss = (
        damage_by_reason.loc[
            damage_by_reason["damage_reason"]
            == "Temperature Breach",
            "total_loss"
        ].sum()
    )

    # ========================================================
    # 8. ROI / RECOMMENDATION ENGINE
    # ========================================================
    # These formulas follow your existing notebook.
    #
    # Recommendation 1:
    # Top 3 damage reasons → 30% reduction
    #
    # Recommendation 2:
    # Top 3 stores → 25% reduction
    #
    # Recommendation 3:
    # High-risk employees → 20% reduction
    #
    # Recommendation 4:
    # Temperature breaches → 40% reduction
    # ========================================================

    # --------------------------------------------------------
    # Recommendation 1: Root Cause Focus
    # --------------------------------------------------------

    monthly_savings_1 = (
        top_3_reason_loss
        * 0.30
        / analysis_months
    )

    annual_savings_1 = (
        monthly_savings_1 * 12
    )

    # --------------------------------------------------------
    # Recommendation 2: Location-Specific Optimization
    # --------------------------------------------------------

    monthly_savings_2 = (
        top_3_stores_loss
        * 0.25
        / analysis_months
    )

    annual_savings_2 = (
        monthly_savings_2 * 12
    )

    # --------------------------------------------------------
    # Recommendation 3: High-Risk Employee Monitoring
    # --------------------------------------------------------

    monthly_savings_3 = (
        high_risk_employee_loss
        * 0.20
        / analysis_months
    )

    annual_savings_3 = (
        monthly_savings_3 * 12
    )

    # --------------------------------------------------------
    # Recommendation 4: Infrastructure Upgrades
    # --------------------------------------------------------

    monthly_savings_4 = (
        temperature_breach_loss
        * 0.40
        / analysis_months
    )

    annual_savings_4 = (
        monthly_savings_4 * 12
    )

    # --------------------------------------------------------
    # Consolidated ROI
    # --------------------------------------------------------

    total_monthly_savings = (
        monthly_savings_1
        + monthly_savings_2
        + monthly_savings_3
        + monthly_savings_4
    )

    total_annual_savings = (
        total_monthly_savings * 12
    )

    estimated_loss_reduction_pct = (
        total_monthly_savings
        / monthly_loss
        * 100
        if monthly_loss > 0
        else 0
    )

    # ========================================================
    # 9. AUTOMATIC INSIGHT FLAGS
    # ========================================================

    automatic_flags = []

    # Store concentration
    if highest_store["loss_pct"] >= 25:

        automatic_flags.append({
            "type": "location_risk",
            "priority": "high",
            "message": (
                f"{highest_store['store_id']} contributes "
                f"{highest_store['loss_pct']:.2f}% "
                f"of total losses."
            )
        })

    # Top 3 root causes
    if top_3_reason_pct >= 40:

        automatic_flags.append({
            "type": "root_cause_concentration",
            "priority": "high",
            "message": (
                f"The top 3 damage reasons account for "
                f"{top_3_reason_pct:.2f}% of total losses."
            )
        })

    # Pareto
    automatic_flags.append({
        "type": "pareto",
        "priority": "high",
        "message": (
            f"The top {len(pareto_causes)} damage reasons "
            f"account for {pareto_loss_pct:.2f}% "
            f"of total losses."
        )
    })

    # Employee concentration
    if top_5_employee_pct >= 20:

        automatic_flags.append({
            "type": "employee_concentration",
            "priority": "medium",
            "message": (
                f"Top 5 employees account for "
                f"{top_5_employee_pct:.2f}% "
                f"of reported losses."
            )
        })

    # Temperature breach
    if temperature_breach_loss > 0:

        automatic_flags.append({
            "type": "environmental_risk",
            "priority": "medium",
            "message": (
                f"Temperature breaches contributed "
                f"₹{temperature_breach_loss:,.2f} "
                f"in losses."
            )
        })

    # ========================================================
    # 10. STRUCTURED OUTPUT
    # ========================================================

    return {

        # ----------------------------------------------------
        # Overall KPIs
        # ----------------------------------------------------

        "overall": {

            "total_loss": round(
                float(total_loss), 2
            ),

            "total_incidents": int(
                total_incidents
            ),

            "total_damaged_units": int(
                total_damaged_units
            ),

            "avg_loss_per_incident": round(
                float(avg_loss_per_incident), 2
            ),

            "stores_affected": int(
                unique_stores
            ),

            "analysis_months": int(
                analysis_months
            ),

            "monthly_loss": round(
                float(monthly_loss), 2
            ),

            "annual_loss_projection": round(
                float(annual_loss_projection), 2
            )
        },

        # ----------------------------------------------------
        # Highest Loss Store
        # ----------------------------------------------------

        "highest_loss_store": {

            "store_id": str(
                highest_store["store_id"]
            ),

            "loss": round(
                float(highest_store["total_loss"]),
                2
            ),

            "loss_pct": round(
                float(highest_store["loss_pct"]),
                2
            ),

            "incidents": int(
                highest_store["incidents"]
            )
        },

        # ----------------------------------------------------
        # Top Loss Reason
        # ----------------------------------------------------

        "top_loss_reason": {

            "reason": str(
                top_reason["damage_reason"]
            ),

            "loss": round(
                float(top_reason["total_loss"]),
                2
            ),

            "loss_pct": round(
                float(top_reason["loss_pct"]),
                2
            ),

            "incidents": int(
                top_reason["incidents"]
            )
        },

        # ----------------------------------------------------
        # Top 3 Root Causes
        # ----------------------------------------------------

        "top_3_root_causes": {

            "causes": (
                top_3_reasons["damage_reason"]
                .tolist()
            ),

            "loss": round(
                float(top_3_reason_loss),
                2
            ),

            "loss_pct": round(
                float(top_3_reason_pct),
                2
            )
        },

        # ----------------------------------------------------
        # Pareto
        # ----------------------------------------------------

        "pareto": {

            "number_of_causes": int(
                len(pareto_causes)
            ),

            "loss": round(
                float(pareto_loss), 2
            ),

            "loss_percentage": round(
                float(pareto_loss_pct), 2
            ),

            "causes": (
                pareto_causes["damage_reason"]
                .tolist()
            )
        },

        # ----------------------------------------------------
        # Top Category
        # ----------------------------------------------------

        "top_category": {

            "category": str(
                top_category["category"]
            ),

            "loss": round(
                float(top_category["total_loss"]),
                2
            ),

            "loss_pct": round(
                float(top_category["loss_pct"]),
                2
            )
        },

        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        "highest_loss_severity": {

            "severity": str(
                highest_loss_severity["severity"]
            ),

            "loss": round(
                float(
                    highest_loss_severity["total_loss"]
                ),
                2
            ),

            "loss_pct": round(
                float(
                    highest_loss_severity["loss_pct"]
                ),
                2
            ),

            "incidents": int(
                highest_loss_severity["incidents"]
            )
        },

        # ----------------------------------------------------
        # Employee Risk
        # ----------------------------------------------------

        "employee_risk": {

            "high_risk_employee_count": int(
                len(high_risk_employees)
            ),

            "high_risk_employee_loss": round(
                float(high_risk_employee_loss),
                2
            ),

            "top_5_employee_loss_pct": round(
                float(top_5_employee_pct),
                2
            )
        },

        # ----------------------------------------------------
        # Location Concentration
        # ----------------------------------------------------

        "location_concentration": {

            "top_3_stores": (
                top_3_stores["store_id"]
                .tolist()
            ),

            "top_3_stores_loss": round(
                float(top_3_stores_loss),
                2
            ),

            "top_3_stores_loss_pct": round(
                float(top_3_stores_pct),
                2
            )
        },

        # ----------------------------------------------------
        # Temperature Risk
        # ----------------------------------------------------

        "temperature_breach": {

            "loss": round(
                float(temperature_breach_loss),
                2
            )
        },

        # ----------------------------------------------------
        # ROI / Savings
        # ----------------------------------------------------

        "savings_opportunity": {

            "root_cause_focus": {

                "monthly_savings": round(
                    float(monthly_savings_1),
                    2
                ),

                "annual_savings": round(
                    float(annual_savings_1),
                    2
                ),

                "expected_reduction_pct": 30
            },

            "location_optimization": {

                "monthly_savings": round(
                    float(monthly_savings_2),
                    2
                ),

                "annual_savings": round(
                    float(annual_savings_2),
                    2
                ),

                "expected_reduction_pct": 25
            },

            "employee_monitoring": {

                "monthly_savings": round(
                    float(monthly_savings_3),
                    2
                ),

                "annual_savings": round(
                    float(annual_savings_3),
                    2
                ),

                "expected_reduction_pct": 20
            },

            "infrastructure_upgrade": {

                "monthly_savings": round(
                    float(monthly_savings_4),
                    2
                ),

                "annual_savings": round(
                    float(annual_savings_4),
                    2
                ),

                "expected_reduction_pct": 40
            },

            "consolidated": {

                "monthly_savings": round(
                    float(total_monthly_savings),
                    2
                ),

                "annual_savings": round(
                    float(total_annual_savings),
                    2
                ),

                "estimated_loss_reduction_pct": round(
                    float(
                        estimated_loss_reduction_pct
                    ),
                    1
                ),

                "implementation_timeline": "3-6 months",

                "confidence": "High (data-backed)"
            }
        },

        # ----------------------------------------------------
        # Automatic Flags
        # ----------------------------------------------------

        "automatic_flags": automatic_flags
    }