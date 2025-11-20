"""
Script to seed the database with sample policies
Run this to populate initial data for testing
"""
from database import SessionLocal
from models import Policy
from datetime import datetime, timedelta

def seed_policies():
    db = SessionLocal()
    
    # Sample policies
    policies = [
        Policy(
            policy_number="POL-2024-001",
            policy_holder_name="John Doe",
            policy_type="Health Insurance Premium",
            expiry_date=datetime.now() + timedelta(days=365)
        ),
        Policy(
            policy_number="POL-2024-002",
            policy_holder_name="Jane Smith",
            policy_type="Health Insurance Standard",
            expiry_date=datetime.now() + timedelta(days=180)
        ),
        Policy(
            policy_number="POL-2024-003",
            policy_holder_name="Robert Johnson",
            policy_type="Health Insurance Basic",
            expiry_date=datetime.now() + timedelta(days=90)
        ),
    ]
    
    for policy in policies:
        existing = db.query(Policy).filter(Policy.policy_number == policy.policy_number).first()
        if not existing:
            db.add(policy)
    
    db.commit()
    print(f"Seeded {len(policies)} policies")
    db.close()

if __name__ == "__main__":
    seed_policies()

