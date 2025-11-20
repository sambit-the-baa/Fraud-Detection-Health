from sqlalchemy.orm import Session
from models import Policy
from typing import Optional

class PolicyService:
    def verify_policy(self, db: Session, policy_number: str) -> Optional[Policy]:
        """Verify if a policy exists and is valid"""
        policy = db.query(Policy).filter(Policy.policy_number == policy_number).first()
        
        if policy:
            # Check if policy is expired
            from datetime import datetime
            if policy.expiry_date and policy.expiry_date < datetime.now():
                return None  # Policy expired
        
        return policy

