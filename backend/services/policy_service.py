from database import get_sync_db
from typing import Optional
from datetime import datetime


class PolicyService:
    def verify_policy(self, db, policy_number: str) -> Optional[dict]:
        """Verify if a policy exists and is valid in MongoDB"""
        # Get MongoDB database
        mongo_db = get_sync_db()
        
        # Find policy by policy_number
        policy = mongo_db.policies.find_one({"policy_number": policy_number})
        
        if policy:
            # Check if policy is expired
            if policy.get("expiry_date") and policy["expiry_date"] < datetime.now():
                return None  # Policy expired
            
            # Return policy as dict (MongoDB already returns dict)
            return policy
        
        return None
