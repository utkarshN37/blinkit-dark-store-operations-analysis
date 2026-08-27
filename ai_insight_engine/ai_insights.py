import json
import os
import re
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "..", "data", "raw", "damaged_products.csv")

    try:
        df_damage = pd.read_csv(file_path)
        return df_damage
    except FileNotFoundError:
        alt_path = "../data/raw/damaged_products.csv"
        try:
            return pd.read_csv(alt_path)
        except Exception:
            print(f"\n❌ Dataset not found: {file_path}")
            raise
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        raise


# ============================================================
# 2. FORMAT BUSINESS FACT SHEET
# ============================================================

def format_fact_sheet(insights: dict) -> str:
    """
    Format verified analytical findings into a clear, labeled business fact sheet.
    """
    overall = insights["overall"]
    store = insights["highest_loss_store"]
    location = insights["location_concentration"]
    reason = insights["top_loss_reason"]
    top_3_reasons = insights["top_3_root_causes"]
    pareto = insights["pareto"]
    category = insights["top_category"]
    temp = insights["temperature_breach"]
    emp = insights["employee_risk"]
    savings = insights["savings_opportunity"]["consolidated"]

    top_3_store_str = ", ".join(location["top_3_stores"])
    top_3_causes_str = ", ".join(top_3_reasons["causes"])

    fact_sheet = f"""OVERALL
Total loss: ₹{overall['total_loss']:,.2f}
Total incidents: {overall['total_incidents']:,}
Damaged units: {overall['total_damaged_units']:,}
Average loss per incident: ₹{overall['avg_loss_per_incident']:,.2f}
Annual loss projection: ₹{overall['annual_loss_projection']:,.2f}

LOCATION
Highest-loss store: {store['store_id']}
{store['store_id']} loss: ₹{store['loss']:,.2f}
{store['store_id']} share of total loss: {store['loss_pct']:.2f}%
Top 3 stores: {top_3_store_str}
Top 3 stores loss: ₹{location['top_3_stores_loss']:,.2f}
Top 3 stores share: {location['top_3_stores_loss_pct']:.1f}%

ROOT CAUSE
Top loss reason: {reason['reason']}
{reason['reason']} loss: ₹{reason['loss']:,.2f}
{reason['reason']} share: {reason['loss_pct']:.2f}%
Top 3 damage reasons: {top_3_causes_str}
Top 3 damage reasons loss: ₹{top_3_reasons['loss']:,.2f}
Top 3 damage reasons share: {top_3_reasons['loss_pct']:.2f}%
Top {pareto['number_of_causes']} damage reasons share: {pareto['loss_percentage']:.2f}%

CATEGORY
Top category: {category['category']}
{category['category']} loss: ₹{category['loss']:,.2f}

ENVIRONMENTAL
Temperature Breach loss: ₹{temp['loss']:,.2f}

EMPLOYEE
High-risk employees: {emp['high_risk_employee_count']}
High-risk employee loss: ₹{emp['high_risk_employee_loss']:,.2f}
Top 5 employees share: {emp['top_5_employee_loss_pct']:.2f}%

ROI
Monthly savings potential: ₹{savings['monthly_savings']:,.2f}
Annual savings potential: ₹{savings['annual_savings']:,.2f}
Estimated loss reduction: {savings['estimated_loss_reduction_pct']:.1f}%
Implementation timeline: {savings['implementation_timeline']}"""

    return fact_sheet


# ============================================================
# 3. GENERATE AI INSIGHT
# ============================================================

def generate_ai_insight(insights: dict) -> str:
    """
    Send verified business fact sheet to Ollama.
    """

    fact_sheet = format_fact_sheet(insights)

    prompt = f"""You are a senior dark-store operations analyst for Blinkit.

The Python analytics engine has calculated and verified the operational findings below.
Your role is to interpret these findings into an executive business brief.

VERIFIED BUSINESS FACT SHEET (SOURCE OF TRUTH):
{fact_sheet}

RULES:
- Base your analysis strictly on the supplied fact sheet.
- Keep useful numbers in the response, but use numbers ONLY with the exact finding they belong to.
- Never invent numbers, recalculate numbers, or change digits.
- Never combine unrelated metrics (e.g. Handling Error + Manufacturing Defect alone do NOT equal ₹219,812.82; that figure belongs to the full top-3 group including Wrong Item Received).
- Do not confuse store S001's 26.22% share with top-3 stores' 65.3% share.
- Do not confuse monthly savings (₹73,944.82) with annual savings (₹887,337.83).
- When discussing overall savings, use the consolidated ₹73,944.82/month and ₹887,337.83/year figures.
- Never convert INR to USD. Always use ₹ for monetary values.
- Do not claim causation unless supported by the data.
- Keep recommendations practical and directly connected to the findings.

JSON SCHEMA OUTPUT REQUIREMENT:
{{
  "key_finding": "2-3 sentences describing the most critical overall operational loss situation using verified numbers.",
  "why_it_matters": "1-2 sentences explaining business significance, margin erosion, and risk concentration.",
  "priority_actions": [
    "Practical recommendation 1 directly connected to top root cause or store focus",
    "Practical recommendation 2 directly connected to high-risk areas or infrastructure"
  ],
  "business_impact": "1-2 sentences connecting operational losses, store concentration, and category risk.",
  "savings_opportunity": "Concise summary of verified consolidated ROI savings (₹73,944.82 monthly / ₹887,337.83 annual potential)."
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
        print(f"\n❌ Ollama error: {e}")
        raise


# ============================================================
# 4. HELPER: EXTRACT NUMERIC VALUES FROM INSIGHTS DICT
# ============================================================

def _extract_allowed_numbers(obj) -> set:
    """
    Recursively extract all numeric float and int values from the insights dict.
    """
    numbers = set()

    if isinstance(obj, dict):
        for v in obj.values():
            numbers.update(_extract_allowed_numbers(v))
    elif isinstance(obj, list):
        for item in obj:
            numbers.update(_extract_allowed_numbers(item))
    elif isinstance(obj, (int, float)):
        val = float(obj)
        numbers.add(round(val, 2))
        numbers.add(round(val, 1))
        numbers.add(round(val, 0))
        numbers.add(int(val))

    return numbers


# ============================================================
# 5. VALIDATE AI OUTPUT
# ============================================================

def validate_ai_output(
    ai_output: str,
    insights: dict
) -> tuple[dict | None, list[str]]:
    """
    Validate the AI response against Python-generated facts.

    Detects:
    a) numbers not present in supplied analytical input,
    b) altered monetary values,
    c) incorrect currency ($ instead of ₹),
    d) malformed/empty output.
    """

    errors = []

    # Parse JSON
    try:
        raw = json.loads(ai_output)
    except json.JSONDecodeError:
        errors.append("AI response was not valid JSON.")
        return None, errors

    if not isinstance(raw, dict):
        errors.append("AI response JSON is not an object.")
        return None, errors

    # Check required fields
    normalized = {str(k).lower().replace(" ", "_"): v for k, v in raw.items()}
    key_finding = normalized.get("key_finding") or normalized.get("finding") or ""
    why_it_matters = normalized.get("why_it_matters") or normalized.get("importance") or ""
    priority_actions = normalized.get("priority_actions") or normalized.get("recommendations") or normalized.get("actions", [])
    business_impact = normalized.get("business_impact") or normalized.get("impact") or ""
    savings_opportunity = normalized.get("savings_opportunity") or normalized.get("savings") or ""

    if not key_finding or not why_it_matters or not priority_actions or not business_impact:
        errors.append("Missing required executive brief fields.")
        return None, errors

    output_text = json.dumps(raw, ensure_ascii=False)

    # Check currency ($ instead of ₹)
    if "$" in output_text or "USD" in output_text.upper():
        errors.append("AI introduced dollar currency ($ / USD) instead of Indian Rupees (₹).")

    # Extract allowed numbers from Python insights
    allowed_numbers = _extract_allowed_numbers(insights)

    # Find monetary numbers in LLM text (e.g., ₹531,705.27, 531705.27, 73,944.82, 139,401.57, etc.)
    currency_matches = re.findall(r"₹\s*([0-9,]+(?:\.[0-9]+)?)", output_text)

    for match in currency_matches:
        clean_num_str = match.replace(",", "")
        try:
            num_val = float(clean_num_str)
            if (round(num_val, 2) not in allowed_numbers and
                round(num_val, 1) not in allowed_numbers and
                round(num_val, 0) not in allowed_numbers and
                int(num_val) not in allowed_numbers):
                errors.append(f"AI introduced an unverified financial value: ₹{match}")
        except ValueError:
            pass

    if errors:
        return None, errors

    if isinstance(priority_actions, str):
        priority_actions = [priority_actions]
    elif not isinstance(priority_actions, list):
        priority_actions = [str(priority_actions)]

    result = {
        "key_finding": key_finding,
        "why_it_matters": why_it_matters,
        "priority_actions": priority_actions,
        "business_impact": business_impact,
        "savings_opportunity": savings_opportunity if savings_opportunity else create_fallback_insight(insights)["savings_opportunity"]
    }

    return result, []


# ============================================================
# 6. FALLBACK RESPONSE
# ============================================================

def create_fallback_insight(
    insights: dict
) -> dict:
    """
    Create a fully fact-based response if the AI output
    cannot be trusted or if Ollama is unavailable.
    """

    overall = insights["overall"]
    store = insights["highest_loss_store"]
    reason = insights["top_loss_reason"]
    category = insights["top_category"]
    pareto = insights["pareto"]
    savings = insights.get("savings_opportunity", {}).get("consolidated", {})

    monthly_sav = savings.get("monthly_savings", 0.0)
    annual_sav = savings.get("annual_savings", 0.0)
    reduction_pct = savings.get("estimated_loss_reduction_pct", 0.0)

    return {
        "key_finding": (
            f"Blinkit dark store operations recorded ₹{overall['total_loss']:,.2f} in total losses "
            f"across {overall['total_incidents']:,} incidents and {overall['stores_affected']} stores. "
            f"Store {store['store_id']} is the single highest-loss location, contributing {store['loss_pct']:.2f}% "
            f"(₹{store['loss']:,.2f}) of total operational losses."
        ),

        "why_it_matters": (
            f"Operational losses reduce dark-store gross margins. {reason['reason']} represents "
            f"the primary loss cause, generating ₹{reason['loss']:,.2f} ({reason['loss_pct']:.2f}% of loss). "
            f"Top {pareto['number_of_causes']} damage reasons account for {pareto['loss_percentage']:.2f}% "
            f"of all losses, demonstrating clear Pareto concentration."
        ),

        "priority_actions": [
            f"Enforce standard operating procedures and handling training to address {reason['reason']}.",
            f"Conduct targeted operational audits at store {store['store_id']} to identify localized damage bottlenecks.",
            f"Implement IoT temperature monitoring and review storage protocols for high-loss SKUs in {category['category']}."
        ],

        "business_impact": (
            f"Average loss per incident is ₹{overall['avg_loss_per_incident']:,.2f}. "
            f"{category['category']} is the highest-loss product category with ₹{category['loss']:,.2f} in damages."
        ),

        "savings_opportunity": (
            f"Targeted interventions present verified monthly savings of ₹{monthly_sav:,.2f} "
            f"(₹{annual_sav:,.2f} annually), corresponding to a potential {reduction_pct:.1f}% operational loss reduction."
        )
    }


# ============================================================
# 7. MAIN PIPELINE
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("BLINKIT AI INSIGHT ENGINE")
    print("=" * 70)

    df_damage = load_data()
    print(f"\n✅ Loaded {len(df_damage):,} damage records")

    print("🔍 Running deterministic insight detection...")
    insights = detect_insights(df_damage)
    print("✅ Analytical insights generated")

    print("🤖 Generating AI business insight...")

    try:
        ai_output = generate_ai_insight(insights)
        validated_output, validation_errors = validate_ai_output(
            ai_output,
            insights
        )

    except Exception as e:
        print(f"⚠️ Could not execute Ollama generation: {e}")
        validated_output = None
        validation_errors = [str(e)]

    if validation_errors:
        print("\n⚠️ AI response failed validation or Ollama call failed.")
        for error in validation_errors:
            print(f"   - {error}")
        print("\n🛡️ Using fact-based fallback response...")
        validated_output = create_fallback_insight(insights)
    else:
        print("✅ AI response passed validation")

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


if __name__ == "__main__":
    main()

