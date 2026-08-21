import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

# ----------------------------------
# CONFIGURATION
# ----------------------------------
NUM_STORES = 5
NUM_EMPLOYEES = 40
NUM_PRODUCTS = 150
DATE_RANGE_DAYS = 90  # 3 months of data

# Store data
stores = {
    "S001": {"name": "Nashik Downtown", "city": "Nashik", "zone": "Central"},
    "S002": {"name": "Nashik West", "city": "Nashik", "zone": "West"},
    "S003": {"name": "Pune Camp", "city": "Pune", "zone": "Central"},
    "S004": {"name": "Pune Hinjewadi", "city": "Pune", "zone": "Tech Park"},
    "S005": {"name": "Mumbai Bandra", "city": "Mumbai", "zone": "West"}
}

# Product categories (Blinkit-like)
product_categories = {
    "Snacks & Chips": 30,
    "Beverages": 20,
    "Dairy & Milk": 15,
    "Fruits & Vegetables": 25,
    "Bakery": 12,
    "Personal Care": 18,
    "Household": 20,
    "Frozen Foods": 15
}

# Employee roles
roles = {
    "Store Manager": ["Supervisory"],
    "Assistant Manager": ["Supervisory"],
    "Team Lead - Putaway": ["Operational"],
    "Team Lead - Inventory": ["Operational"],
    "Warehouse Associate": ["Operational"],
    "Quality Checker": ["Quality"]
}

# Damage reasons (realistic for retail)
damage_reasons = [
    "Packaging Damaged",
    "Product Expired",
    "Product Crushed",
    "Wrong Item Received",
    "Spillage/Leakage",
    "Manufacturing Defect",
    "Temperature Breach",
    "Handling Error",
    "Pest Damage",
    "Shelf Life Expired"
]

# Putaway status
putaway_status = ["Completed", "Partial", "Delayed", "Quality Hold"]

# Audit findings
audit_findings = [
    "Stock Match",
    "Overstock",
    "Understock",
    "Misplaced Item",
    "Duplicate SKU",
    "Expired Product Found",
    "Damaged Stock Found"
]

# ----------------------------------
# HELPER FUNCTIONS
# ----------------------------------
def generate_product_data(num_products):
    """Generate master product list"""
    products = []
    product_id = 1
    
    for category, count in product_categories.items():
        for i in range(count):
            products.append({
                "product_id": f"PROD{product_id:05d}",
                "product_name": f"{category} - Product {i+1}",
                "category": category,
                "sku": f"SKU{product_id:06d}",
                "unit_price": round(random.uniform(20, 500), 2),
                "shelf_life_days": random.randint(7, 365),
                "reorder_level": random.randint(10, 50),
                "max_stock": random.randint(50, 200)
            })
            product_id += 1
    
    return products[:num_products]

def generate_employee_data(num_employees):
    """Generate employee master data"""
    employees = []
    first_names = ["Rajesh", "Priya", "Amit", "Sneha", "Suresh", "Anjali", 
                   "Rohan", "Neha", "Vikram", "Pooja", "Kunal", "Disha"]
    last_names = ["Sharma", "Patel", "Gupta", "Singh", "Verma", "Joshi", 
                  "Kulkarni", "Mehta", "Yadav", "Reddy"]
    
    for i in range(num_employees):
        emp_id = f"EMP{i+1:04d}"
        store_id = random.choice(list(stores.keys()))
        role = random.choice(list(roles.keys()))
        
        joining_date = datetime.now() - timedelta(days=random.randint(30, 730))
        
        employees.append({
            "employee_id": emp_id,
            "employee_name": f"{random.choice(first_names)} {random.choice(last_names)}",
            "store_id": store_id,
            "role": role,
            "role_category": roles[role][0],
            "joining_date": joining_date.strftime("%Y-%m-%d"),
            "experience_months": (datetime.now() - joining_date).days // 30,
            "phone": f"9{random.randint(100000000, 999999999)}",
            "status": random.choice(["Active"] * 95 + ["Inactive", "On Leave"])
        })
    
    return employees

def generate_putaway_data(products, employees, stores, days=90):
    """Generate putaway/stock placement transactions"""
    putaway_records = []
    
    for _ in range(500):  # 500 putaway transactions
        transaction_date = datetime.now() - timedelta(days=random.randint(0, days))
        store_id = random.choice(list(stores.keys()))
        employee = random.choice([e for e in employees if e["store_id"] == store_id])
        product = random.choice(products)
        
        putaway_records.append({
            "putaway_id": f"PUT{len(putaway_records)+1:06d}",
            "transaction_date": transaction_date.strftime("%Y-%m-%d"),
            "transaction_time": f"{random.randint(6, 23):02d}:{random.randint(0, 59):02d}",
            "store_id": store_id,
            "employee_id": employee["employee_id"],
            "employee_name": employee["employee_name"],
            "product_id": product["product_id"],
            "sku": product["sku"],
            "quantity_received": random.randint(5, 50),
            "quantity_putaway": random.randint(3, 50),
            "shelf_location": f"{chr(65+random.randint(0,4))}{random.randint(1,10)}-{random.randint(1,5)}",
            "status": random.choice(putaway_status),
            "time_to_putaway_minutes": random.randint(5, 120),
            "quality_check_passed": random.choice([True] * 90 + [False] * 10),
            "remarks": random.choice(["None", "Damaged items separated", "Quantity mismatch", "Temperature issue"] + ["None"]*96)
        })
    
    return putaway_records

def generate_damaged_products(products, employees, stores, days=90):
    """Generate damaged product records with employee who reported it"""
    damaged_records = []
    
    for _ in range(200):  # 200 damaged product incidents
        transaction_date = datetime.now() - timedelta(days=random.randint(0, days))
        store_id = random.choice(list(stores.keys()))
        employee = random.choice([e for e in employees if e["store_id"] == store_id])
        product = random.choice(products)
        
        damage_date = transaction_date - timedelta(days=random.randint(0, 30))
        
        damaged_records.append({
            "damage_id": f"DMG{len(damaged_records)+1:06d}",
            "report_date": transaction_date.strftime("%Y-%m-%d"),
            "report_time": f"{random.randint(6, 23):02d}:{random.randint(0, 59):02d}",
            "reported_by_emp_id": employee["employee_id"],
            "reported_by_emp_name": employee["employee_name"],
            "reported_by_role": employee["role"],
            "store_id": store_id,
            "product_id": product["product_id"],
            "sku": product["sku"],
            "product_name": product["product_name"],
            "quantity_damaged": random.randint(1, 20),
            "unit_price": product["unit_price"],
            "total_loss_value": round(product["unit_price"] * random.randint(1, 20), 2),
            "damage_reason": random.choice(damage_reasons),
            "damage_date": damage_date.strftime("%Y-%m-%d"),
            "days_before_reported": (transaction_date - damage_date).days,
            "category": product["category"],
            "severity": random.choice(["Low", "Medium", "High"] + ["Low"]*70 + ["Medium"]*20),
            "approver": random.choice(["MGR_001", "MGR_002", "AMGR_001"]),
            "status": random.choice(["Approved", "Rejected", "Under Review"] + ["Approved"]*80),
            "notes": random.choice(["Verified and written off", "Partial recovery", "Escalated to vendor", "None"] + ["None"]*96)
        })
    
    return damaged_records

def generate_employee_performance(employees, damaged_products, putaway_data, days=90):
    """Generate employee performance metrics"""
    performance_records = []
    
    for employee in employees:
        # Count damaged products reported by this employee
        damages_reported = len([d for d in damaged_products if d["reported_by_emp_id"] == employee["employee_id"]])
        
        # Count putaway transactions by this employee
        putaway_transactions = len([p for p in putaway_data if p["employee_id"] == employee["employee_id"]])
        
        # Calculate quality score
        quality_putaway = len([p for p in putaway_data 
                               if p["employee_id"] == employee["employee_id"] and p["quality_check_passed"]])
        quality_score = (quality_putaway / putaway_transactions * 100) if putaway_transactions > 0 else 0
        
        # Attendance score (random for demo)
        attendance_score = round(random.uniform(70, 100), 1)
        
        # Punctuality score
        punctuality_score = round(random.uniform(75, 100), 1)
        
        performance_records.append({
            "performance_id": f"PERF{len(performance_records)+1:06d}",
            "employee_id": employee["employee_id"],
            "employee_name": employee["employee_name"],
            "store_id": employee["store_id"],
            "role": employee["role"],
            "experience_months": employee["experience_months"],
            "report_period": f"2026-05-01 to 2026-07-31",  # Last 3 months
            "putaway_transactions_count": putaway_transactions,
            "damages_reported_count": damages_reported,
            "avg_time_per_putaway_minutes": round(np.mean([p["time_to_putaway_minutes"] 
                                                            for p in putaway_data 
                                                            if p["employee_id"] == employee["employee_id"]]) 
                                                   if putaway_transactions > 0 else 0, 1),
            "quality_score": round(quality_score, 1),
            "attendance_score": attendance_score,
            "punctuality_score": punctuality_score,
            "overall_performance_rating": round((quality_score + attendance_score + punctuality_score) / 3, 1),
            "damages_per_transaction_ratio": round(damages_reported / (putaway_transactions + 1), 3),
            "promotion_eligible": "Yes" if (quality_score > 80 and attendance_score > 85) else "No",
            "performance_level": "Excellent" if round((quality_score + attendance_score + punctuality_score) / 3, 1) >= 85 
                                else "Good" if round((quality_score + attendance_score + punctuality_score) / 3, 1) >= 70 
                                else "Average"
        })
    
    return performance_records

def generate_inventory_audit(products, employees, stores, days=90):
    """Generate inventory audit records"""
    audit_records = []
    audit_id = 1
    
    for _ in range(100):  # 100 audit records
        audit_date = datetime.now() - timedelta(days=random.randint(0, days))
        store_id = random.choice(list(stores.keys()))
        
        # Find auditor - prefer Inventory role, fallback to any store employee
        auditors = [e for e in employees if e["store_id"] == store_id and "Inventory" in e["role"]]
        if not auditors:
            auditors = [e for e in employees if e["store_id"] == store_id]
        auditor = random.choice(auditors)
        product = random.choice(products)
        
        system_qty = random.randint(20, 100)
        finding = random.choice(audit_findings)
        
        if finding == "Overstock":
            physical_qty = system_qty + random.randint(1, 10)
        elif finding == "Understock":
            physical_qty = system_qty - random.randint(1, 10)
        elif finding == "Stock Match":
            physical_qty = system_qty
        else:
            physical_qty = system_qty + random.randint(-5, 5)
        
        variance = physical_qty - system_qty
        
        audit_records.append({
            "audit_id": f"AUD{audit_id:06d}",
            "audit_date": audit_date.strftime("%Y-%m-%d"),
            "audit_time": f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}",
            "store_id": store_id,
            "auditor_emp_id": auditor["employee_id"],
            "auditor_name": auditor["employee_name"],
            "product_id": product["product_id"],
            "sku": product["sku"],
            "product_name": product["product_name"],
            "category": product["category"],
            "system_quantity": system_qty,
            "physical_quantity": physical_qty,
            "quantity_variance": variance,
            "variance_percentage": round((variance / system_qty * 100) if system_qty > 0 else 0, 2),
            "finding": finding,
            "shelf_location": f"{chr(65+random.randint(0,4))}{random.randint(1,10)}-{random.randint(1,5)}",
            "expiry_date_found": (datetime.now() - timedelta(days=random.randint(-100, 200))).strftime("%Y-%m-%d"),
            "action_taken": random.choice(["Corrected", "Under Investigation", "Marked for Disposal", "Restocked"]),
            "resolution_date": (audit_date + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d"),
            "rectification_remarks": random.choice(["Corrected in system", "Waiting for supplier response", "None"] + ["None"]*97)
        })
        audit_id += 1
    
    return audit_records

# ----------------------------------
# GENERATE ALL DATASETS
# ----------------------------------
print("=" * 80)
print("GENERATING BLINKIT-LIKE OPERATIONAL DATASET")
print("=" * 80)

print("\n[1/6] Generating Products Master Data...")
products = generate_product_data(NUM_PRODUCTS)
df_products = pd.DataFrame(products)

print("[2/6] Generating Employee Data...")
employees = generate_employee_data(NUM_EMPLOYEES)
df_employees = pd.DataFrame(employees)

print("[3/6] Generating Putaway/Stock Placement Data...")
putaway_data = generate_putaway_data(products, employees, stores, DATE_RANGE_DAYS)
df_putaway = pd.DataFrame(putaway_data)

print("[4/6] Generating Damaged Products Data...")
damaged_products = generate_damaged_products(products, employees, stores, DATE_RANGE_DAYS)
df_damaged = pd.DataFrame(damaged_products)

print("[5/6] Generating Employee Performance Metrics...")
performance = generate_employee_performance(employees, damaged_products, putaway_data, DATE_RANGE_DAYS)
df_performance = pd.DataFrame(performance)

print("[6/6] Generating Inventory Audit Data...")
audit_data = generate_inventory_audit(products, employees, stores, DATE_RANGE_DAYS)
df_audit = pd.DataFrame(audit_data)

# Create directory if it doesn't exist
os.makedirs("data/blinkit_operations", exist_ok=True)

# Save all datasets
datasets = {
    "products_master": df_products,
    "employees_master": df_employees,
    "putaway_transactions": df_putaway,
    "damaged_products": df_damaged,
    "employee_performance": df_performance,
    "inventory_audit": df_audit
}

print("\n" + "=" * 80)
print("SAVING DATASETS")
print("=" * 80)

for dataset_name, df in datasets.items():
    filepath = f"data/blinkit_operations/{dataset_name}.csv"
    df.to_csv(filepath, index=False)
    print(f"✅ {dataset_name:.<40} {len(df):>5} rows")

# ----------------------------------
# SUMMARY STATISTICS
# ----------------------------------
print("\n" + "=" * 80)
print("DATASET SUMMARY STATISTICS")
print("=" * 80)

print(f"\n📦 PRODUCTS: {len(df_products)} total products")
print(df_products['category'].value_counts().to_string())

print(f"\n👥 EMPLOYEES: {len(df_employees)} total employees")
print("\nBy Role:")
print(df_employees['role'].value_counts().to_string())
print("\nBy Store:")
print(df_employees['store_id'].value_counts().to_string())

print(f"\n📤 PUTAWAY TRANSACTIONS: {len(df_putaway)} total transactions")
print(f"   Average time to putaway: {df_putaway['time_to_putaway_minutes'].mean():.1f} minutes")
print(f"   Quality check pass rate: {(df_putaway['quality_check_passed'].sum() / len(df_putaway) * 100):.1f}%")

print(f"\n❌ DAMAGED PRODUCTS: {len(df_damaged)} total records")
print(f"   Total loss value: ₹{df_damaged['total_loss_value'].sum():,.2f}")
print(f"   Average loss per incident: ₹{df_damaged['total_loss_value'].mean():.2f}")
print("\nTop Damage Reasons:")
print(df_damaged['damage_reason'].value_counts().head(5).to_string())
print("\nBy Severity:")
print(df_damaged['severity'].value_counts().to_string())

print(f"\n⭐ EMPLOYEE PERFORMANCE: {len(df_performance)} employees rated")
print(f"   Average overall rating: {df_performance['overall_performance_rating'].mean():.2f}/100")
print("\nPerformance Levels:")
print(df_performance['performance_level'].value_counts().to_string())
print(f"\nPromotion Eligible: {len(df_performance[df_performance['promotion_eligible'] == 'Yes'])} employees")

print(f"\n📊 INVENTORY AUDIT: {len(df_audit)} total audit records")
print(f"   Average variance: {df_audit['quantity_variance'].mean():.2f} units")
print("\nAudit Findings:")
print(df_audit['finding'].value_counts().to_string())

print("\n" + "=" * 80)
print("SAMPLE DATA PREVIEW")
print("=" * 80)

print("\n📦 Products Sample:")
print(df_products.head(5).to_string())

print("\n\n👥 Employees Sample:")
print(df_employees.head(5).to_string())

print("\n\n📤 Putaway Sample:")
print(df_putaway.head(3).to_string())

print("\n\n❌ Damaged Products Sample:")
print(df_damaged.head(3).to_string())

print("\n\n⭐ Employee Performance Sample:")
print(df_performance.head(5)[['employee_id', 'employee_name', 'role', 'putaway_transactions_count', 
                               'damages_reported_count', 'quality_score', 'overall_performance_rating']].to_string())

print("\n\n📊 Inventory Audit Sample:")
print(df_audit.head(3).to_string())

print("\n" + "=" * 80)
print("✨ ALL DATASETS GENERATED SUCCESSFULLY!")
print("=" * 80)
df.to_csv(filepath, index=False)
import os
print(os.path.abspath(filepath))