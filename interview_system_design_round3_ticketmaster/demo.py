from __future__ import annotations

from pprint import pprint

from mock_ticketmaster import TicketmasterMock


def line(title: str) -> None:
    print("\n" + "=" * 16 + f" {title} " + "=" * 16)


def main() -> None:
    system = TicketmasterMock(
        total_tickets=3,
        hold_timeout_s=120,
        waitlist_offer_timeout_s=60,
        enable_virtual_queue=True,
    )

    line("1) Rush Queue Join")
    for user in ["u1", "u2", "u3", "u4"]:
        print(user, system.join_rush_queue(user))
    pprint(system.snapshot())

    line("2) Admit 2 Users")
    print("admitted:", system.admit_next_in_queue(2))
    pprint(system.snapshot())

    line("3) Create Holds")
    hold_u1 = system.create_hold("u1", 1)
    hold_u2 = system.create_hold("u2", 2)
    hold_u3 = system.create_hold("u3", 1)  # not admitted yet
    print("u1:", hold_u1)
    print("u2:", hold_u2)
    print("u3:", hold_u3)
    pprint(system.snapshot())

    line("4) Sold Out + Waitlist")
    print("u4 join waitlist:", system.join_waitlist("u4", 1))
    pprint(system.snapshot())

    line("5) Payment Guarantee")
    payment1 = system.pay_for_hold(
        hold_id=hold_u1["hold_id"],
        idempotency_key="idem-u1-order-1",
    )
    replay = system.pay_for_hold(
        hold_id=hold_u1["hold_id"],
        idempotency_key="idem-u1-order-1",
    )
    print("first payment:", payment1)
    print("idempotent replay:", replay)
    pprint(system.snapshot())

    line("6) Cancel One Purchase -> Waitlist Offer")
    if payment1["ok"]:
        print("cancel:", system.cancel_purchase(payment1["purchase_id"]))
    pprint(system.snapshot())


if __name__ == "__main__":
    main()
