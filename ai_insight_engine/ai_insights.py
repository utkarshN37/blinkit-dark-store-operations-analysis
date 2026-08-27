import json
import os
import re
import pandas as pd

from insight_detection import detect_insights


# ============================================================
# 1. OLLAMA AVAILABILITY
# ============================================================

def check_ollama_available() -> bool:
    """
    Check whether Ollama is available locally.
    Returns False on Streamlit Cloud or any environment
    where Ollama is unavailable.
    """
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


# ============================================================
# 2. LOAD BLINKIT DATA
# ============================================================

def load_data() -> pd.DataFrame:
    """
    Load the existing Blinkit damaged-products dataset.
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(
        base_dir,
        "..",
        "data",
        "raw",
        "damaged_products.csv"
    )

    try:
        return pd.read_csv(file_path)

    except FileNotFoundError:
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    except Exception as e:
        raise RuntimeError(
            f"Error loading dataset: {e}"
        )


# ============================================================
# 3. BUSINESS FACT SHEET
# ============================================================

def format_fact_sheet(insights: dict) -> str:
    """
    Convert verified Python analytics into a clear fact sheet
    for the LLM.
    """

    overall = insights["overall"]
    store = insights["highest_loss_store"]
    location = insights["location_concentration"]
    reason = insights["top_loss_reason"]
    top_3_reasons = insights["top_3_root_causes"]
    pareto = insights["pareto"]
    category = insights["top_category"]
    temp = insights["temperature_breach"]
    employee = insights["employee_risk"]
    savings = insights["savings_opportunity"]["consolidated"]

    top_3_stores = ", ".join(location["top_3_stores"])
    top_3_causes = ", ".join(top_3_reasons["causes"])

    return f"""
OVERALL
Total loss: ₹{overall['total_loss']:,.2f}
Total incidents: {overall['total_incidents']:,}
Damaged units: {overall['total_damaged_units']:,}
Average loss per incident: ₹{overall['avg_loss_per_incident']:,.2f}
Annual loss projection: ₹{overall['annual_loss_projection']:,.2f}

LOCATION
Highest-loss store: {store['store_id']}
{store['store_id']} loss: ₹{store['loss']:,.2f}
{store['store_id']} share: {store['loss_pct']:.2f}%
Top 3 stores: {top_3_stores}
Top 3 stores loss: ₹{location['top_3_stores_loss']:,.2f}
Top 3 stores share: {location['top_3_stores_loss_pct']:.1f}%

ROOT CAUSE
Top loss reason: {reason['reason']}
{reason['reason']} loss: ₹{reason['loss']:,.2f}
{reason['reason']} share: {reason['loss_pct']:.2f}%
Top 3 damage reasons: {top_3_causes}
Top 3 damage reasons loss: ₹{top_3_reasons['loss']:,.2f}
Top 3 damage reasons share: {top_3_reasons['loss_pct']:.2f}%
Top {pareto['number_of_causes']} damage reasons share: {pareto['loss_percentage']:.2f}%

CATEGORY
Top category: {category['category']}
{category['category']} loss: ₹{category['loss']:,.2f}

ENVIRONMENTAL
Temperature Breach loss: ₹{temp['loss']:,.2f}

EMPLOYEE
High-risk employees: {employee['high_risk_employee_count']}
High-risk employee loss: ₹{employee['high_risk_employee_loss']:,.2f}
Top 5 employees share: {employee['top_5_employee_loss_pct']:.2f}%

ROI
Monthly savings potential: ₹{savings['monthly_savings']:,.2f}
Annual savings potential: ₹{savings['annual_savings']:,.2f}
Estimated loss reduction: {savings['estimated_loss_reduction_pct']:.1f}%
Implementation timeline: {savings['implementation_timeline']}
"""


# ============================================================
# 4. GENERATE AI INSIGHT
# ============================================================

def generate_ai_insight(insights: dict) -> str:
    """
    Generate an executive business brief using Ollama.

    Python remains the source of truth.
    Ollama interprets the verified findings.
    """

    try:
        import ollama
    except ImportError as e:
        raise RuntimeError(
            "Ollama is not installed in this environment."
        ) from e

    fact_sheet = format_fact_sheet(insights)

    prompt = f"""
You are a senior business analyst reviewing Blinkit
dark-store operational performance.

The Python analytics engine has already calculated the
following VERIFIED BUSINESS FACTS.

================ VERIFIED FACT SHEET ================

{fact_sheet}

======================================================

Your task is to explain what these results mean for the business.

IMPORTANT RULES:

- Use the supplied facts as the source of truth.
- Keep useful numbers in the response.
- NEVER invent numbers.
- NEVER change digits.
- NEVER perform new calculations.
- NEVER mix a number with the wrong finding.
- Use a number only with the exact metric it belongs to.
- Always use ₹ for Indian currency.
- Never convert INR to USD.
- Do not claim causation unless supported by the data.
- Recommendations must be directly connected to the findings.
- Avoid generic recommendations.
- It is okay to omit less-important metrics.

Examples of correct relationships:

S001 → ₹139,401.57 → 26.22% of total loss

Top 3 stores → ₹347,013.64 → 65.3% of total loss

Handling Error → ₹81,810.01 → 15.39%

Top 3 damage reasons → ₹219,812.82 → 41.34%

Snacks & Chips → ₹111,047.24

Temperature Breach → ₹65,104.64

Monthly savings → ₹73,944.82

Annual savings → ₹887,337.83

Estimated loss reduction → 41.7%

DO NOT combine unrelated metrics.

For example:
₹219,812.82 belongs to the full top-3 damage-reason group:
Handling Error + Manufacturing Defect + Wrong Item Received.

Return ONLY valid JSON in this structure:

{{
  "key_finding": "",
  "why_it_matters": "",
  "priority_actions": [],
  "business_impact": "",
  "savings_opportunity": ""
}}
"""

    try:
        response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format="json"
        )

        return response["message"]["content"]

    except Exception as e:
        raise RuntimeError(
            f"Ollama generation failed: {e}"
        ) from e


# ============================================================
# 5. EXTRACT NUMERIC VALUES
# ============================================================

def _extract_allowed_numbers(obj) -> set:
    """
    Extract numeric values from Python-generated insights.
    Used only to detect obviously invented financial values.
    """

    numbers = set()

    if isinstance(obj, dict):

        for value in obj.values():
            numbers.update(
                _extract_allowed_numbers(value)
            )

    elif isinstance(obj, list):

        for item in obj:
            numbers.update(
                _extract_allowed_numbers(item)
            )

    elif isinstance(obj, (int, float)):

        value = float(obj)

        numbers.add(round(value, 2))
        numbers.add(round(value, 1))
        numbers.add(round(value, 0))
        numbers.add(int(value))

    return numbers


# ============================================================
# 6. VALIDATE AI OUTPUT
# ============================================================

def validate_ai_output(
    ai_output: str,
    insights: dict
) -> tuple[dict | None, list[str]]:
    """
    Lightweight validation.

    We validate important issues without requiring the AI
    to repeat every supplied metric.
    """

    errors = []

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:
        raw = json.loads(ai_output)

    except json.JSONDecodeError:
        return None, [
            "AI response was not valid JSON."
        ]

    if not isinstance(raw, dict):
        return None, [
            "AI response JSON is not an object."
        ]

    # --------------------------------------------------------
    # Fields
    # --------------------------------------------------------

    key_finding = raw.get(
        "key_finding",
        ""
    )

    why_it_matters = raw.get(
        "why_it_matters",
        ""
    )

    priority_actions = raw.get(
        "priority_actions",
        []
    )

    business_impact = raw.get(
        "business_impact",
        ""
    )

    savings_opportunity = raw.get(
        "savings_opportunity",
        ""
    )

    if not key_finding:
        errors.append(
            "Missing key_finding."
        )

    if not why_it_matters:
        errors.append(
            "Missing why_it_matters."
        )

    if not priority_actions:
        errors.append(
            "Missing priority_actions."
        )

    if not business_impact:
        errors.append(
            "Missing business_impact."
        )

    if errors:
        return None, errors

    # --------------------------------------------------------
    # Normalize actions
    # --------------------------------------------------------

    if isinstance(priority_actions, str):

        priority_actions = [
            priority_actions
        ]

    elif not isinstance(priority_actions, list):

        priority_actions = [
            str(priority_actions)
        ]

    output_text = json.dumps(
        raw,
        ensure_ascii=False
    )

    # --------------------------------------------------------
    # Currency sanity check
    # --------------------------------------------------------

    if "$" in output_text or "USD" in output_text.upper():

        errors.append(
            "AI used USD/dollar currency."
        )

    # --------------------------------------------------------
    # Financial value validation
    #
    # We only validate RUPEE values because these are the
    # numbers most important to protect.
    # --------------------------------------------------------

    allowed_numbers = _extract_allowed_numbers(
        insights
    )

    currency_matches = re.findall(
        r"₹\s*([0-9,]+(?:\.[0-9]+)?)",
        output_text
    )

    for match in currency_matches:

        try:

            value = float(
                match.replace(",", "")
            )

            rounded_values = {
                round(value, 2),
                round(value, 1),
                round(value, 0),
                int(value)
            }

            if not rounded_values.intersection(
                allowed_numbers
            ):

                errors.append(
                    f"Unverified financial value: ₹{match}"
                )

        except ValueError:
            continue

    # --------------------------------------------------------
    # Return validated result
    # --------------------------------------------------------

    if errors:
        return None, errors

    result = {
        "key_finding": key_finding,
        "why_it_matters": why_it_matters,
        "priority_actions": priority_actions,
        "business_impact": business_impact,
        "savings_opportunity": savings_opportunity
    }

    return result, []


# ============================================================
# 7. FALLBACK INSIGHT
# ============================================================

def create_fallback_insight(
    insights: dict
) -> dict:
    """
    Fully Python-generated fallback.
    Used when Ollama is unavailable or produces
    an unreliable response.
    """

    overall = insights["overall"]
    store = insights["highest_loss_store"]
    reason = insights["top_loss_reason"]
    category = insights["top_category"]
    pareto = insights["pareto"]
    savings = (
        insights["savings_opportunity"]
        ["consolidated"]
    )

    return {

        "key_finding": (
            f"Blinkit dark-store operations recorded "
            f"₹{overall['total_loss']:,.2f} in total losses "
            f"across {overall['total_incidents']:,} incidents. "
            f"S001 is the highest-loss store, contributing "
            f"₹{store['loss']:,.2f} "
            f"({store['loss_pct']:.2f}%) of total loss."
        ),

        "why_it_matters": (
            f"Losses are concentrated across a small number "
            f"of damage causes. {reason['reason']} is the "
            f"largest individual driver at "
            f"₹{reason['loss']:,.2f}, while the top "
            f"{pareto['number_of_causes']} causes represent "
            f"{pareto['loss_percentage']:.2f}% of total loss."
        ),

        "priority_actions": [

            (
                f"Prioritize corrective action for "
                f"{reason['reason']} and review handling "
                f"processes at S001."
            ),

            (
                f"Focus operational reviews on high-loss "
                f"stores and the leading damage causes."
            ),

            (
                f"Investigate {category['category']} and "
                f"temperature-related losses for targeted "
                f"process improvements."
            )
        ],

        "business_impact": (
            f"Average loss per incident is "
            f"₹{overall['avg_loss_per_incident']:,.2f}. "
            f"{category['category']} is the highest-loss "
            f"category at ₹{category['loss']:,.2f}."
        ),

        "savings_opportunity": (
            f"Existing intervention modelling indicates "
            f"₹{savings['monthly_savings']:,.2f} monthly "
            f"and ₹{savings['annual_savings']:,.2f} annual "
            f"savings potential, with an estimated "
            f"{savings['estimated_loss_reduction_pct']:.1f}% "
            f"loss reduction."
        )
    }


# ============================================================
# 8. MAIN PIPELINE
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("BLINKIT AI INSIGHT ENGINE")
    print("=" * 70)

    # Load data
    df_damage = load_data()

    print(
        f"\n✅ Loaded {len(df_damage):,} damage records"
    )

    # Deterministic analytics
    print(
        "🔍 Running deterministic insight detection..."
    )

    insights = detect_insights(
        df_damage
    )

    print(
        "✅ Analytical insights generated"
    )

    # AI generation
    print(
        "🤖 Generating AI business insight..."
    )

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

    except Exception as e:

        validated_output = None

        validation_errors = [
            str(e)
        ]

    # Fallback
    if validation_errors:

        print(
            "\n⚠️ AI response failed validation "
            "or Ollama was unavailable."
        )

        for error in validation_errors:

            print(
                f"   - {error}"
            )

        print(
            "\n🛡️ Using fact-based fallback..."
        )

        validated_output = create_fallback_insight(
            insights
        )

    else:

        print(
            "✅ AI response passed validation"
        )

    # Final output
    print("\n" + "=" * 70)
    print("BLINKIT AI-GENERATED BUSINESS INSIGHT")
    print("=" * 70)

    print(
        json.dumps(
            validated_output,
            indent=2,
            ensure_ascii=False
        )
    )

    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()