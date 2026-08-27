import json
import pandas as pd
import ollama

from insight_detection import detect_insights


# ============================================================
# 1. LOAD BLINKIT DATA
# ============================================================

def load_data() -> pd.DataFrame:
    """
    Load the existing Blinkit damaged-products dataset.
    """

    file_path = "../data/raw/damaged_products.csv"

    try:
        df_damage = pd.read_csv(file_path)
        return df_damage

    except FileNotFoundError:
        print(f"\n❌ Dataset not found: {file_path}")
        print("Check that the project folder structure is correct.")
        raise

    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        raise


# ============================================================
# 2. GENERATE AI INSIGHT
# ============================================================

def generate_ai_insight(insights: dict) -> str:
    """
    Send verified analytical findings to Ollama.

    IMPORTANT:
    The LLM explains the findings.
    It does NOT perform the underlying calculations.
    """

    insights_json = json.dumps(
        insights,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
You are a business analyst reviewing Blinkit dark-store operations.

The Python analytics engine has already calculated and verified
the findings below.

Your job is to explain these findings in simple, useful business language.

RULES:
- Use only the supplied findings.
- Do not invent new numbers.
- Do not perform new calculations.
- Do not create a new savings estimate.
- Do not repeat every metric.
- Focus on what matters most to management.
- Explain why the finding matters.
- Give practical actions directly connected to the findings.
- Keep the response concise and natural.
- Monetary values are Indian Rupees (₹).

Return the response in this format:

EXECUTIVE SUMMARY:
[2-3 sentences describing the most important overall situation]

PRIORITY ISSUES:
[2-4 short bullet points]

WHAT MANAGEMENT SHOULD DO:
[2-4 short bullet points]

ANALYTICAL FINDINGS:
{insights_json}
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

        print(f"\n❌ Ollama error: {e}")
        raise


# ============================================================
# 3. VALIDATE AI OUTPUT
# ============================================================

def validate_ai_output(
    ai_output: str,
    insights: dict
) -> tuple[dict | None, list[str]]:
    """
    Validate the AI response against Python-generated facts.

    Returns:
        validated_output
        validation_errors
    """

    errors = []

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:
        result = json.loads(ai_output)

    except json.JSONDecodeError:
        errors.append("AI response was not valid JSON.")
        return None, errors

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_fields = [
        "key_finding",
        "top_driver",
        "location_insight",
        "business_impact",
        "recommended_actions",
        "savings_opportunity",
        "data_points"
    ]

    for field in required_fields:

        if field not in result:
            errors.append(
                f"Missing required field: {field}"
            )

    if errors:
        return None, errors

    # --------------------------------------------------------
    # Convert output into searchable text
    # --------------------------------------------------------

    output_text = json.dumps(
        result,
        ensure_ascii=False
    )

    # --------------------------------------------------------
    # Ground-truth values
    # --------------------------------------------------------

    total_loss = insights["overall"]["total_loss"]

    total_incidents = insights["overall"]["total_incidents"]

    total_damaged_units = insights["overall"]["total_damaged_units"]

    avg_loss = insights["overall"]["avg_loss_per_incident"]

    highest_store = insights["highest_loss_store"]

    top_reason = insights["top_loss_reason"]

    top_category = insights["top_category"]

    highest_severity = insights["highest_loss_severity"]

    # --------------------------------------------------------
    # Exact values that should appear
    # --------------------------------------------------------

    expected_values = [

        f"{total_loss:,.2f}",

        f"{total_incidents:,}",

        f"{total_damaged_units:,}",

        f"{avg_loss:,.2f}",

        f"{highest_store['loss']:,.2f}",

        f"{highest_store['loss_pct']:.2f}",

        f"{top_reason['loss']:,.2f}",

        f"{top_reason['loss_pct']:.2f}",

        f"{top_category['loss']:,.2f}",

        f"{highest_severity['loss']:,.2f}"
    ]

    # --------------------------------------------------------
    # Check financial values
    # --------------------------------------------------------

    for value in expected_values:

        if value not in output_text:

            errors.append(
                f"Verified value missing or changed: {value}"
            )

    # --------------------------------------------------------
    # Currency validation
    # --------------------------------------------------------

    if "$" in output_text:

        errors.append(
            "AI introduced dollar currency."
        )

    # --------------------------------------------------------
    # Check for suspicious invented savings
    # --------------------------------------------------------

    supplied_savings = insights.get(
        "savings_opportunity"
    )

    if not supplied_savings:

        savings_text = str(
            result.get(
                "savings_opportunity",
                ""
            )
        ).lower()

        forbidden_terms = [
            "₹10,000",
            "₹20,000",
            "10000",
            "20000",
            "$",
            "usd"
        ]

        for term in forbidden_terms:

            if term.lower() in savings_text:

                errors.append(
                    "AI appears to have invented a savings value."
                )
                break

    # --------------------------------------------------------
    # Return validation result
    # --------------------------------------------------------

    if errors:

        return None, errors

    return result, []


# ============================================================
# 4. FALLBACK RESPONSE
# ============================================================

def create_fallback_insight(
    insights: dict
) -> dict:
    """
    Create a fully fact-based response if the AI output
    cannot be trusted.
    """

    total_loss = insights["overall"]["total_loss"]

    total_incidents = insights["overall"]["total_incidents"]

    avg_loss = insights["overall"]["avg_loss_per_incident"]

    store = insights["highest_loss_store"]

    reason = insights["top_loss_reason"]

    category = insights["top_category"]

    pareto = insights["pareto"]

    savings = insights.get(
        "savings_opportunity"
    )

    return {

        "key_finding": (
            f"The operation recorded ₹{total_loss:,.2f} "
            f"in losses across {total_incidents:,} incidents. "
            f"The leading loss location is {store['store_id']}."
        ),

        "top_driver": (
            f"{reason['reason']} is the largest individual "
            f"loss driver, contributing ₹{reason['loss']:,.2f} "
            f"({reason['loss_pct']:.2f}% of total loss)."
        ),

        "location_insight": (
            f"{store['store_id']} recorded ₹{store['loss']:,.2f} "
            f"in losses, representing {store['loss_pct']:.2f}% "
            f"of total losses across {store['incidents']} incidents."
        ),

        "business_impact": (
            f"Average loss per incident is ₹{avg_loss:,.2f}. "
            f"The top {pareto['number_of_causes']} damage reasons "
            f"represent {pareto['loss_percentage']:.2f}% of total losses."
        ),

        "recommended_actions": [

            f"Prioritize investigation and corrective action "
            f"for {reason['reason']} incidents.",

            f"Review operational processes at {store['store_id']} "
            f"and focus monitoring on the highest-impact damage causes."

        ],

        "savings_opportunity": (
            savings
            if savings
            else "Not provided in analytical input."
        ),

        "data_points": [

            f"Total loss: ₹{total_loss:,.2f}",

            f"Total incidents: {total_incidents:,}",

            f"Average loss per incident: ₹{avg_loss:,.2f}",

            f"Top loss reason: {reason['reason']} "
            f"(₹{reason['loss']:,.2f})",

            f"Top category: {category['category']} "
            f"(₹{category['loss']:,.2f})"

        ]
    }


# ============================================================
# 5. MAIN PIPELINE
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("BLINKIT AI INSIGHT ENGINE")
    print("=" * 70)

    # --------------------------------------------------------
    # Step 1: Load data
    # --------------------------------------------------------

    df_damage = load_data()

    print(
        f"\n✅ Loaded {len(df_damage):,} damage records"
    )

    # --------------------------------------------------------
    # Step 2: Detect analytical insights
    # --------------------------------------------------------

    print(
        "🔍 Running deterministic insight detection..."
    )

    insights = detect_insights(
        df_damage
    )

    print(
        "✅ Analytical insights generated"
    )

    # --------------------------------------------------------
    # Step 3: Send verified facts to Ollama
    # --------------------------------------------------------

    print(
        "🤖 Generating AI business insight..."
    )

    ai_output = generate_ai_insight(
        insights
    )

    # --------------------------------------------------------
    # Step 4: Validate AI response
    # --------------------------------------------------------

    validated_output, validation_errors = (
        validate_ai_output(
            ai_output,
            insights
        )
    )

    # --------------------------------------------------------
    # Step 5: Handle invalid AI response
    # --------------------------------------------------------

    if validation_errors:

        print(
            "\n⚠️ AI response failed validation."
        )

        for error in validation_errors:

            print(
                f"   - {error}"
            )

        print(
            "\n🛡️ Using fact-based fallback response..."
        )

        validated_output = create_fallback_insight(
            insights
        )

    else:

        print(
            "✅ AI response passed validation"
        )

    # --------------------------------------------------------
    # Step 6: Display final result
    # --------------------------------------------------------

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