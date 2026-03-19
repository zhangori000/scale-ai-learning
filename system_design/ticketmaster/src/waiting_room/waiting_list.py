import time
import logging
from typing import List, Optional

class WaitingListService:
    """
    Durable Orchestrator for the Post-Sell-Out Waiting List.
    Built for stability and auditability (Postgres + Kafka).
    """
    def __init__(self, db_client, redis_client, notification_client):
        self.db = db_client
        self.redis = redis_client
        self.notify = notification_client
        self.event_id = "bruno_mars_2026"

    def join_waiting_list(self, user_id: str, preferences: dict):
        """
        Adds a user to the persistent waitlist in Postgres.
        Uses serial/auto-incrementing ID for First-Come-First-Served (FCFS).
        """
        self.db.execute(
            "INSERT INTO waiting_list (user_id, event_id, status, joined_at) "
            "VALUES (%s, %s, 'WAITING', NOW())",
            (user_id, self.event_id)
        )
        return "You have been added to the waiting list."

    def on_inventory_available(self, seat_id: str):
        """
        KAFKA CONSUMER: Triggered when a seat becomes AVAILABLE 
        (Refund, Expiry, or Payment Failure).
        """
        # 1. FIND THE NEXT PERSON IN LINE (Atomic Lock to avoid double-offer)
        # SQL: SELECT * FROM waiting_list WHERE status = 'WAITING' 
        #      ORDER BY id ASC LIMIT 1 FOR UPDATE SKIP LOCKED
        user = self.db.get_next_waiting_user(self.event_id)
        
        if not user:
            # If no one is waiting, the seat is just made public.
            return

        # 2. CREATE PRIVATE RESERVATION
        # This keeps the seat 'Invisible' to the public.
        offer_expiry = time.time() + 86400 # 24 Hours
        
        self.db.update_offer_status(user['id'], "OFFERED", seat_id, offer_expiry)
        
        # 3. SET LONG REDIS LOCK
        # This protects the seat during the 24-hour claim window.
        self.redis.set(f"seat_lock:{seat_id}", user['user_id'], nx=True, ex=86400)

        # 4. DISPATCH NOTIFICATION (Asynchronous)
        self.notify.send_offer(
            user['user_id'], 
            seat_id, 
            claim_url=f"/claim?token={user['offer_token']}"
        )

    def sweep_expired_offers(self):
        """
        CRON WORKER (Runs every minute):
        Reclaims seats from users who didn't buy within the 24h window.
        """
        # SQL: UPDATE waiting_list SET status = 'EXPIRED' 
        #      WHERE status = 'OFFERED' AND offer_expires_at < NOW()
        #      RETURNING seat_id
        expired_seats = self.db.release_expired_offers(self.event_id)
        
        for seat_id in expired_seats:
            # Remove the Redis lock and trigger the cycle again for the next person.
            self.redis.delete(f"seat_lock:{seat_id}")
            self.on_inventory_available(seat_id)

    def anti_entropy_reconciliation(self):
        """
        RECONCILIATION WORKER (Sanity Check):
        Finds 'Dangling' available seats that are stuck in limbo 
        (e.g. if the notify process crashed).
        """
        # Finds seats marked 'AVAILABLE' but no one on the waitlist has an active OFFER.
        stuck_seats = self.db.find_available_unassigned_seats(self.event_id)
        
        for seat_id in stuck_seats:
            logging.warn(f"Reconciliation: Seat {seat_id} was stuck. Re-offering.")
            self.on_inventory_available(seat_id)
