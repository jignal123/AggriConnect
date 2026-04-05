from channels.db import database_sync_to_async
from .models import Bidding
from farmer.models import Listing
from django.core.cache import cache
from django.db import IntegrityError

LOCK_TIMEOUT = 3


@database_sync_to_async
def add_bid(user, l_id, price):
    lock_id = f"bid-{l_id}"
    lock = cache.lock(lock_id, timeout=LOCK_TIMEOUT)

    if not lock.acquire(blocking=True):
        return {"success": False, "message": "System is Busy, Please try Again"}

    try:
        check = (
            Bidding.objects.filter(l_id=l_id)
            .order_by("-price_per_unit")
            .values("price_per_unit")
            .first()
        )
        print(check)
        # exit()
        org_price = check.get("price_per_unit",int(-1))
        
        if org_price >= price:
            return {"success": False, "message": "Bid must be higher than current bid"}
        else:
            bid = Bidding.objects.create(
                l_id=l_id, price_per_unit=price, bidder_id=user
            )

            return {
                "success": True,
                "b_id": bid.b_id,
                "price_per_unit_str": str(bid.price_per_unit),
                "wholesaler_name": bid.bidder_id.business_name,
                "bidder_id": bid.bidder_id.w_id
            }
    except IntegrityError:
        return {
            "success": False,
            "message":"Duplicate Entry!"
        }
    finally:
        lock.release()


@database_sync_to_async
def update_bid(b_id, price_per_unit):
    bid = Bidding.objects.select_related("bidder_id").get(b_id=b_id)
    l_id = bid.l_id
    
    lock_id = f"bid-{l_id}"
    lock = cache.lock(lock_id, timeout=LOCK_TIMEOUT)

    if not lock.acquire(blocking=True):
        return {"success": False, "message": "System is Busy, Please try Again"}

    try:
        check = (
            Bidding.objects.filter(l_id=l_id)
            .exclude(b_id=b_id)
            .order_by("-price_per_unit")
            .values("price_per_unit")
            .first()
        )
        # print(check)
        # exit()
        org_price = check.get("price_per_unit",int(-1)) if check!= None else -1
        if org_price >= price_per_unit:
            return {"success": False, "message": "Must be highest bid"}
        else:
            bid.price_per_unit = price_per_unit
            bid.save()
            bid.refresh_from_db()
            return {
                "success": True,
                "b_id": bid.b_id,
                "price_per_unit_str": str(bid.price_per_unit),
                "wholesaler_name": bid.bidder_id.business_name,
                "bidder_id": bid.bidder_id.w_id
            }
    finally:
        lock.release()

@database_sync_to_async
def delete_bid(b_id):
    try:
        bid = Bidding.objects.get(b_id= b_id)
        bid.delete()
        return {
            "success": True,
            "b_id": b_id,
            "message": "Bid deleted!"
        }
    except Bidding.DoesNotExist:
        return {
            "success": False,
            "message": "Can't Find the given Bid"
        }