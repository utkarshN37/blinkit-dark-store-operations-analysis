import pandas as pd
from insight_detection import detect_insights


# Load existing Blinkit damage dataset
df_damage = pd.read_csv(
    "../data/raw/damaged_products.csv"
)

# Run insight detection
insights = detect_insights(df_damage)


print("\n" + "=" * 60)
print("BLINKIT AUTOMATED INSIGHT DETECTION")
print("=" * 60)

print("\nOVERALL")
for key, value in insights["overall"].items():
    print(f"{key}: {value}")

print("\nHIGHEST LOSS STORE")
for key, value in insights["highest_loss_store"].items():
    print(f"{key}: {value}")

print("\nTOP LOSS REASON")
for key, value in insights["top_loss_reason"].items():
    print(f"{key}: {value}")

print("\nTOP CATEGORY")
for key, value in insights["top_category"].items():
    print(f"{key}: {value}")

print("\nHIGHEST LOSS SEVERITY")
for key, value in insights["highest_loss_severity"].items():
    print(f"{key}: {value}")

print("\nPARETO")
for key, value in insights["pareto"].items():
    print(f"{key}: {value}")

print("\nAUTOMATIC FLAGS")
for flag in insights["automatic_flags"]:
    print(f"⚠️ {flag}")

print("\n" + "=" * 60)