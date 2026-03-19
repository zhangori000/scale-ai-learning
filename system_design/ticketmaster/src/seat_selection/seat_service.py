import time
import uuid
import logging
from dataclasses import dataclass
from typing import Optional, Dict

class SeatSelectionService:
    """
    Enhanced Seat Service with Payment Retry Grace Periods and CS Overrides.
    """
    def __init__(self, redis_client, db_client, payment_gateway, event_id="bruno_mars_2026"):
        self.redis = redis_client
        self.db = db_client
        self.payment = payment_gateway
        self.event_id = event_id

    def purchase_seat(self, user_id: str, seat_id: str, payment_info: Dict):
        lock_key = f"seat_lock:{seat_id}"
        still_owner = self.redis.eval_lua("EXTEND_LOCK", [lock_key], [user_id, 60])
        
        if not still_owner:
            return {"status": "FAILED", "reason": "Your hold has expired."}

        idempotency_key = f"purchase:{self.event_id}:{user_id}:{seat_id}"

        try:
            payment_ref = self.payment.charge(
                amount=payment_info['amount'], 
                token=payment_info['token'],
                idempotency_key=idempotency_key
            )
        except Exception as e:
            # 1. THE RETRY GRACE PERIOD (New Logic)
            # Instead of failing, we move the seat to a 'PAYMENT_RETRY' state.
            # We extend the Redis lock by 30 minutes.
            self.redis.expire(lock_key, 1800) 
            self.db.update_status(seat_id, "PAYMENT_RETRY", retry_expires_at=time.time() + 1800)
            
            return {
                "status": "PAYMENT_FAILED", 
                "message": "Card declined. You have 30 minutes to fix this before the seat is released.",
                "retry_allowed": True
            }

        # 2. ATOMIC DB COMMIT
        db_success = self.db.execute_atomic_buy(user_id, seat_id, payment_ref)

        if db_success:
            self.redis.delete(lock_key)
            return {"status": "SUCCESS", "order_id": payment_ref}
        else:
            self.payment.refund(payment_ref, idempotency_key=idempotency_key)
            return {"status": "FAILED", "reason": "Seat finalized by another process."}

    def cs_manual_override(self, agent_id: str, seat_id: str, action: str):
        """
        Customer Service Tooling.
        Allows a human agent to 'Pause' expiry or 'Force Release' a seat.
        """
        if action == "HOLD":
            # Put the seat into 'CS_HOLD' - the automated sweep cron will skip this.
            self.db.update_status(seat_id, "CS_HOLD")
            self.redis.expire(f"seat_lock:{seat_id}", 86400) # 24h lock
            return "Seat placed on manual hold for investigation."
            
        if action == "RELEASE":
            # Agent decides the user cannot pay. Seat goes to the waiting list.
            self.db.update_status(seat_id, "AVAILABLE")
            self.redis.delete(f"seat_lock:{seat_id}")
            # This triggers the 'Inventory Available' event for the Waiting List
            self.publish_inventory_event(seat_id, "CS_RELEASE")
            return "Seat released to waiting list."
    
    def publish_inventory_event(self, seat_id, reason):
        # Kafka.send(topic="inventory_available", payload={"seat_id": seat_id, "reason": reason})
        pass
