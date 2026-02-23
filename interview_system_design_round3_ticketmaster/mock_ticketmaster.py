from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any, Callable


class HoldStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    CONVERTED = "converted"


class HoldSource(str, Enum):
    NORMAL = "normal"
    WAITLIST_OFFER = "waitlist_offer"


@dataclass
class Hold:
    hold_id: str
    user_id: str
    quantity: int
    created_at: float
    expires_at: float
    status: HoldStatus = HoldStatus.ACTIVE
    source: HoldSource = HoldSource.NORMAL
    release_reason: str | None = None


@dataclass
class Purchase:
    purchase_id: str
    hold_id: str
    user_id: str
    quantity: int
    paid_at: float
    idempotency_key: str
    canceled: bool = False


@dataclass
class WaitlistEntry:
    seq: int
    user_id: str
    quantity: int
    joined_at: float


@dataclass
class WaitlistNotification:
    user_id: str
    hold_id: str
    quantity: int
    created_at: float
    message: str = "Tickets available from waitlist."


@dataclass
class QueueEntry:
    user_id: str
    joined_at: float


class VirtualQueue:
    """Simple FIFO waiting room to absorb traffic spikes."""

    def __init__(self) -> None:
        self._queue: deque[QueueEntry] = deque()
        self._admitted: set[str] = set()
        self._waiting_users: set[str] = set()

    def join(self, user_id: str, now: float) -> dict[str, Any]:
        if user_id in self._admitted:
            return {"status": "admitted", "position": 0}
        if user_id in self._waiting_users:
            return {"status": "queued", "position": self.position(user_id)}
        self._queue.append(QueueEntry(user_id=user_id, joined_at=now))
        self._waiting_users.add(user_id)
        return {"status": "queued", "position": len(self._queue)}

    def admit_next(self, batch_size: int) -> list[str]:
        admitted: list[str] = []
        for _ in range(max(0, batch_size)):
            if not self._queue:
                break
            entry = self._queue.popleft()
            self._waiting_users.discard(entry.user_id)
            self._admitted.add(entry.user_id)
            admitted.append(entry.user_id)
        return admitted

    def position(self, user_id: str) -> int | None:
        if user_id in self._admitted:
            return 0
        for idx, entry in enumerate(self._queue, start=1):
            if entry.user_id == user_id:
                return idx
        return None

    def consume_admission(self, user_id: str) -> bool:
        if user_id not in self._admitted:
            return False
        self._admitted.discard(user_id)
        return True

    def snapshot(self) -> dict[str, Any]:
        return {
            "queued_count": len(self._queue),
            "admitted_count": len(self._admitted),
            "queued_users": [e.user_id for e in self._queue],
            "admitted_users": sorted(self._admitted),
        }


class TicketmasterMock:
    """
    In-memory Ticketmaster-like mock to illustrate system-design requirements:
    - burst handling via virtual queue
    - checkout timeout (expiring holds)
    - sold-out behavior
    - payment guarantee via reserved holds
    - waitlist FIFO offers on release/cancel
    """

    def __init__(
        self,
        total_tickets: int,
        hold_timeout_s: float = 120.0,
        waitlist_offer_timeout_s: float = 60.0,
        enable_virtual_queue: bool = True,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if total_tickets <= 0:
            raise ValueError("total_tickets must be > 0")
        self.total_tickets = total_tickets
        self.available_tickets = total_tickets
        self.sold_tickets = 0

        self.hold_timeout_s = hold_timeout_s
        self.waitlist_offer_timeout_s = waitlist_offer_timeout_s
        self._clock = clock or monotonic
        self._lock = threading.RLock()

        self.enable_virtual_queue = enable_virtual_queue
        self.virtual_queue = VirtualQueue() if enable_virtual_queue else None

        self._hold_seq = 0
        self._purchase_seq = 0
        self._waitlist_seq = 0
        self.holds: dict[str, Hold] = {}
        self.purchases: dict[str, Purchase] = {}
        self._idempotency_index: dict[str, str] = {}
        self.waitlist: deque[WaitlistEntry] = deque()
        self.notifications: list[WaitlistNotification] = []

    def _now(self) -> float:
        return self._clock()

    # ------------------------------------------------------------------
    # Rush / queue control
    # ------------------------------------------------------------------
    def join_rush_queue(self, user_id: str) -> dict[str, Any]:
        with self._lock:
            if not self.enable_virtual_queue or self.virtual_queue is None:
                return {"status": "admitted", "position": 0}
            return self.virtual_queue.join(user_id=user_id, now=self._now())

    def admit_next_in_queue(self, batch_size: int) -> list[str]:
        with self._lock:
            if not self.enable_virtual_queue or self.virtual_queue is None:
                return []
            return self.virtual_queue.admit_next(batch_size=batch_size)

    # ------------------------------------------------------------------
    # Ticket hold / checkout
    # ------------------------------------------------------------------
    def create_hold(self, user_id: str, quantity: int) -> dict[str, Any]:
        with self._lock:
            self._sweep_expired_holds_locked()
            if quantity <= 0:
                return {"ok": False, "reason": "quantity_must_be_positive"}

            if self.enable_virtual_queue and self.virtual_queue is not None:
                if not self.virtual_queue.consume_admission(user_id):
                    return {
                        "ok": False,
                        "reason": "not_admitted",
                        "queue_position": self.virtual_queue.position(user_id),
                    }

            if self.available_tickets < quantity:
                return {
                    "ok": False,
                    "reason": "sold_out",
                    "available_tickets": self.available_tickets,
                }

            hold = self._create_hold_locked(
                user_id=user_id,
                quantity=quantity,
                timeout_s=self.hold_timeout_s,
                source=HoldSource.NORMAL,
            )
            return {
                "ok": True,
                "hold_id": hold.hold_id,
                "expires_at": hold.expires_at,
                "available_tickets": self.available_tickets,
            }

    def pay_for_hold(
        self,
        hold_id: str,
        idempotency_key: str,
        force_fail: bool = False,
    ) -> dict[str, Any]:
        with self._lock:
            self._sweep_expired_holds_locked()

            existing_purchase_id = self._idempotency_index.get(idempotency_key)
            if existing_purchase_id is not None:
                purchase = self.purchases[existing_purchase_id]
                return {
                    "ok": True,
                    "purchase_id": purchase.purchase_id,
                    "hold_id": purchase.hold_id,
                    "idempotent_replay": True,
                }

            hold = self.holds.get(hold_id)
            if hold is None:
                return {"ok": False, "reason": "hold_not_found"}
            if hold.status != HoldStatus.ACTIVE:
                return {"ok": False, "reason": f"hold_not_active:{hold.status.value}"}

            if self._now() >= hold.expires_at:
                self._expire_hold_locked(hold, reason="checkout_timeout")
                self._offer_to_waitlist_locked()
                return {"ok": False, "reason": "hold_expired"}

            if force_fail:
                self._release_hold_locked(hold, reason="payment_failed")
                self._offer_to_waitlist_locked()
                return {"ok": False, "reason": "payment_failed"}

            self._purchase_seq += 1
            purchase_id = f"p_{self._purchase_seq}"
            purchase = Purchase(
                purchase_id=purchase_id,
                hold_id=hold.hold_id,
                user_id=hold.user_id,
                quantity=hold.quantity,
                paid_at=self._now(),
                idempotency_key=idempotency_key,
            )
            self.purchases[purchase_id] = purchase
            self._idempotency_index[idempotency_key] = purchase_id

            hold.status = HoldStatus.CONVERTED
            self.sold_tickets += hold.quantity
            self._assert_invariant_locked()

            return {
                "ok": True,
                "purchase_id": purchase.purchase_id,
                "hold_id": hold.hold_id,
                "quantity": hold.quantity,
                "idempotent_replay": False,
            }

    def process_timeouts(self) -> dict[str, Any]:
        with self._lock:
            expired_ids = self._sweep_expired_holds_locked()
            notifications = self._offer_to_waitlist_locked()
            return {
                "expired_hold_ids": expired_ids,
                "waitlist_notifications": [n.hold_id for n in notifications],
            }

    # ------------------------------------------------------------------
    # Sold out / waitlist / cancellation
    # ------------------------------------------------------------------
    def join_waitlist(self, user_id: str, quantity: int) -> dict[str, Any]:
        with self._lock:
            if quantity <= 0:
                return {"ok": False, "reason": "quantity_must_be_positive"}
            self._waitlist_seq += 1
            entry = WaitlistEntry(
                seq=self._waitlist_seq,
                user_id=user_id,
                quantity=quantity,
                joined_at=self._now(),
            )
            self.waitlist.append(entry)
            # Opportunistically offer now if tickets exist.
            notifications = self._offer_to_waitlist_locked()
            return {
                "ok": True,
                "waitlist_seq": entry.seq,
                "position": len(self.waitlist),
                "notified_hold_ids": [n.hold_id for n in notifications if n.user_id == user_id],
            }

    def cancel_purchase(self, purchase_id: str) -> dict[str, Any]:
        with self._lock:
            purchase = self.purchases.get(purchase_id)
            if purchase is None:
                return {"ok": False, "reason": "purchase_not_found"}
            if purchase.canceled:
                return {"ok": False, "reason": "purchase_already_canceled"}

            purchase.canceled = True
            self.sold_tickets -= purchase.quantity
            self.available_tickets += purchase.quantity
            notifications = self._offer_to_waitlist_locked()
            self._assert_invariant_locked()
            return {
                "ok": True,
                "refunded_quantity": purchase.quantity,
                "waitlist_notifications": [n.hold_id for n in notifications],
            }

    # ------------------------------------------------------------------
    # Read model
    # ------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._sweep_expired_holds_locked()
            active_holds = [
                hold
                for hold in self.holds.values()
                if hold.status == HoldStatus.ACTIVE
            ]
            return {
                "total_tickets": self.total_tickets,
                "available_tickets": self.available_tickets,
                "sold_tickets": self.sold_tickets,
                "active_holds_count": len(active_holds),
                "active_holds": [
                    {
                        "hold_id": hold.hold_id,
                        "user_id": hold.user_id,
                        "quantity": hold.quantity,
                        "expires_at": hold.expires_at,
                        "source": hold.source.value,
                    }
                    for hold in sorted(active_holds, key=lambda h: h.hold_id)
                ],
                "waitlist_count": len(self.waitlist),
                "waitlist_users": [entry.user_id for entry in self.waitlist],
                "notification_count": len(self.notifications),
                "virtual_queue": self.virtual_queue.snapshot()
                if self.virtual_queue is not None
                else None,
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _create_hold_locked(
        self,
        user_id: str,
        quantity: int,
        timeout_s: float,
        source: HoldSource,
    ) -> Hold:
        self._hold_seq += 1
        hold_id = f"h_{self._hold_seq}"
        now = self._now()
        hold = Hold(
            hold_id=hold_id,
            user_id=user_id,
            quantity=quantity,
            created_at=now,
            expires_at=now + timeout_s,
            source=source,
        )
        self.holds[hold_id] = hold
        self.available_tickets -= quantity
        self._assert_invariant_locked()
        return hold

    def _sweep_expired_holds_locked(self) -> list[str]:
        now = self._now()
        expired: list[str] = []
        for hold in list(self.holds.values()):
            if hold.status != HoldStatus.ACTIVE:
                continue
            if now < hold.expires_at:
                continue
            self._expire_hold_locked(hold, reason="checkout_timeout")
            expired.append(hold.hold_id)
        if expired:
            self._assert_invariant_locked()
        return expired

    def _expire_hold_locked(self, hold: Hold, reason: str) -> None:
        hold.status = HoldStatus.EXPIRED
        hold.release_reason = reason
        self.available_tickets += hold.quantity

    def _release_hold_locked(self, hold: Hold, reason: str) -> None:
        if hold.status != HoldStatus.ACTIVE:
            return
        hold.status = HoldStatus.RELEASED
        hold.release_reason = reason
        self.available_tickets += hold.quantity
        self._assert_invariant_locked()

    def _offer_to_waitlist_locked(self) -> list[WaitlistNotification]:
        notifications: list[WaitlistNotification] = []
        while self.waitlist and self.available_tickets > 0:
            next_entry = self.waitlist[0]
            if next_entry.quantity > self.available_tickets:
                break

            self.waitlist.popleft()
            hold = self._create_hold_locked(
                user_id=next_entry.user_id,
                quantity=next_entry.quantity,
                timeout_s=self.waitlist_offer_timeout_s,
                source=HoldSource.WAITLIST_OFFER,
            )
            notification = WaitlistNotification(
                user_id=next_entry.user_id,
                hold_id=hold.hold_id,
                quantity=next_entry.quantity,
                created_at=self._now(),
            )
            notifications.append(notification)

        self.notifications.extend(notifications)
        return notifications

    def _assert_invariant_locked(self) -> None:
        reserved = sum(
            hold.quantity
            for hold in self.holds.values()
            if hold.status == HoldStatus.ACTIVE
        )
        sold = sum(
            purchase.quantity
            for purchase in self.purchases.values()
            if not purchase.canceled
        )
        total = self.available_tickets + reserved + sold
        if total != self.total_tickets:
            raise RuntimeError(
                "invariant broken: available + reserved + sold != total "
                f"({self.available_tickets} + {reserved} + {sold} != {self.total_tickets})"
            )


__all__ = ["TicketmasterMock", "HoldStatus", "HoldSource"]
