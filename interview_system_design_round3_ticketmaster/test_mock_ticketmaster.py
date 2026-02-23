from __future__ import annotations

import unittest

from mock_ticketmaster import HoldSource, HoldStatus, TicketmasterMock


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class TicketmasterMockTest(unittest.TestCase):
    def test_virtual_queue_controls_rush(self) -> None:
        clock = FakeClock()
        tm = TicketmasterMock(total_tickets=2, enable_virtual_queue=True, clock=clock)

        tm.join_rush_queue("u1")
        tm.join_rush_queue("u2")

        # Not admitted yet
        blocked = tm.create_hold("u1", 1)
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["reason"], "not_admitted")

        tm.admit_next_in_queue(1)
        allowed = tm.create_hold("u1", 1)
        self.assertTrue(allowed["ok"])

    def test_checkout_timeout_releases_tickets(self) -> None:
        clock = FakeClock()
        tm = TicketmasterMock(
            total_tickets=1,
            hold_timeout_s=5,
            enable_virtual_queue=False,
            clock=clock,
        )

        hold = tm.create_hold("u1", 1)
        self.assertTrue(hold["ok"])
        self.assertEqual(tm.snapshot()["available_tickets"], 0)

        clock.advance(6)
        result = tm.process_timeouts()
        self.assertEqual(result["expired_hold_ids"], [hold["hold_id"]])
        self.assertEqual(tm.snapshot()["available_tickets"], 1)

    def test_waitlist_gets_offer_on_cancel(self) -> None:
        clock = FakeClock()
        tm = TicketmasterMock(
            total_tickets=1,
            enable_virtual_queue=False,
            waitlist_offer_timeout_s=30,
            clock=clock,
        )

        hold = tm.create_hold("buyer", 1)
        payment = tm.pay_for_hold(hold["hold_id"], idempotency_key="p1")
        self.assertTrue(payment["ok"])

        tm.join_waitlist("waiter-1", 1)
        cancel = tm.cancel_purchase(payment["purchase_id"])
        self.assertTrue(cancel["ok"])
        self.assertEqual(len(cancel["waitlist_notifications"]), 1)

        snap = tm.snapshot()
        self.assertEqual(snap["waitlist_count"], 0)
        self.assertEqual(len(snap["active_holds"]), 1)
        self.assertEqual(snap["active_holds"][0]["user_id"], "waiter-1")
        self.assertEqual(snap["active_holds"][0]["source"], HoldSource.WAITLIST_OFFER.value)

    def test_payment_idempotency_does_not_oversell(self) -> None:
        clock = FakeClock()
        tm = TicketmasterMock(total_tickets=2, enable_virtual_queue=False, clock=clock)

        hold = tm.create_hold("u1", 2)
        p1 = tm.pay_for_hold(hold["hold_id"], idempotency_key="idem-1")
        p2 = tm.pay_for_hold(hold["hold_id"], idempotency_key="idem-1")

        self.assertTrue(p1["ok"])
        self.assertTrue(p2["ok"])
        self.assertEqual(p1["purchase_id"], p2["purchase_id"])
        self.assertTrue(p2["idempotent_replay"])

        snap = tm.snapshot()
        self.assertEqual(snap["sold_tickets"], 2)
        self.assertEqual(snap["available_tickets"], 0)
        self.assertEqual(snap["active_holds_count"], 0)

    def test_failed_payment_releases_hold(self) -> None:
        clock = FakeClock()
        tm = TicketmasterMock(total_tickets=1, enable_virtual_queue=False, clock=clock)

        hold = tm.create_hold("u1", 1)
        fail = tm.pay_for_hold(
            hold_id=hold["hold_id"],
            idempotency_key="idem-fail",
            force_fail=True,
        )

        self.assertFalse(fail["ok"])
        self.assertEqual(tm.snapshot()["available_tickets"], 1)
        self.assertEqual(tm.holds[hold["hold_id"]].status, HoldStatus.RELEASED)


if __name__ == "__main__":
    unittest.main()
