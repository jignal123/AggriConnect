from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .models import Bidding, Wholesaler
from farmer.models import Listing
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from .biddingOpr import add_bid, update_bid, delete_bid
from urllib.parse import parse_qs
from django.db.models.functions import Cast
from django.db.models.expressions import F
from django.db.models.fields import CharField


class MyBiddingConsumers(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.listing_id = self.scope["url_route"]["kwargs"]["l_id"]
            self.group_name = f"bids-of-{self.listing_id}"
            listing = await sync_to_async(
                Listing.objects.filter(l_id=self.listing_id).exclude(status="S").exists
            )()
            await self.accept()
            if listing:
                await self.channel_layer.group_add(
                    group=self.group_name, channel=self.channel_name
                )

                bids = await sync_to_async(list)(
                    Bidding.objects.filter(l_id=self.listing_id, bidder_id__status="V")
                    .select_related("bidder_id")
                    .order_by("-price_per_unit")
                    .annotate(
                        price_per_unit_str=Cast("price_per_unit", CharField()),
                        wholesaler_name=F("bidder_id__business_name"),
                    )
                    .values(
                        "b_id",
                        "price_per_unit_str",
                        "wholesaler_name",
                        "status",
                        "bidder_id",
                    )
                )

                await self.send_json(
                    content={"success": True, "type": "initial_bids", "bids": bids}
                )
            else:
                winner_bid = await find_winner_bid(self.listing_id)
                await self.send_json(
                    content = {
                        **winner_bid
                    }
                    
                )
        else:
            await self.send_json(
                content={"success": False, "message": "You are not Authorized!"}
            )

    async def receive_json(self, content, **kwargs):
        if self.scope["user"].is_authenticated:
            action = content.get("action")
            qry_string = parse_qs(self.scope["query_string"].decode("utf8"))
            role = qry_string["role"][0]
            if role != "farmer":
                try:
                    listing = await sync_to_async(
                        Listing.objects.filter(l_id=self.listing_id)
                        .exclude(status="S")
                        .only("l_id")
                        .first
                    )()
                    result = {}
                    if listing:
                        if action == "add_bid":
                            if role == "admin":
                                w_id = content.get("w_id", None)
                                if w_id:
                                    user = await sync_to_async(
                                        Wholesaler.objects.filter(status="V").get
                                    )(w_id=w_id)
                                else:
                                    await self.send_json(
                                        content={
                                            "success": False,
                                            "message": "Wholesaler Id not provided!",
                                        }
                                    )
                                    return
                            elif role == "wholesaler":
                                user = self.scope["user"]
                            result = await add_bid(
                                user=user,
                                l_id=listing,
                                price=float(content["price_per_unit_str"]),
                            )
                            type = "bid_added"
                        elif action == "update_bid":
                            result = await update_bid(
                                b_id=content["b_id"],
                                price_per_unit=float(content["price_per_unit_str"]),
                            )
                            type = "bid_updated"
                        elif action == "delete_bid":
                            result = await delete_bid(b_id=content["b_id"])
                            type = "bid_deleted"
                        if result["success"]:
                            await self.channel_layer.group_send(
                                self.group_name, message={"type": type, **result}
                            )
                        else:
                            await self.send_json(content={**result})
                    else:
                        winner_bid = await find_winner_bid(self.listing_id)
                        await self.send_json(content={
                            **winner_bid
                        })
                except KeyError:
                    await self.send_json(
                        content={
                            "success": False,
                            "message": "Bidding Details are incomplete",
                        }
                    )
                    return
                except Wholesaler.DoesNotExist:
                    await self.send_json(
                        content={
                            "success": False,
                            "message": "No Verified Wholesaler Found of given details",
                        }
                    )
                    return
        else:
            await self.send_json(
                content={"success": False, "message": "You are not Authorized!"}
            )

    async def bid_added(self, event):
        await self.send_json(content={"type": "bid_added", **event})

    async def bid_updated(self, event):
        await self.send_json(content={"type": "bid_updated", **event})

    async def bid_deleted(self, event):
        await self.send_json(content={"type": "bid_deleted", **event})

    async def bid_closed(self, event):
        await self.send_json(content={"type": "bid_closed", **event})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)


@database_sync_to_async
def find_winner_bid(l_id):
    winner_bid = (
        Bidding.objects.filter(l_id=l_id, status="A")
        .select_related("bidder_id")
        .only(
            "price_per_unit",
            "bidder_id__business_name",
            "b_id",
            "status",
            "bidder_id__w_id",
        )
        .first()
    )
    if winner_bid:
        winner_bid_data = {
            "b_id": winner_bid.b_id,
            "wholesaler_name": winner_bid.bidder_id.business_name,
            "price_per_unit_str": str(winner_bid.price_per_unit),
            "bidder_id": winner_bid.bidder_id.w_id,
        }
    else:
        winner_bid_data = {}
    result = {
        "success": True,
        "message": "Bid Closed",
        "type": "bid_closed",
        "winner_bid": winner_bid_data,
    }
    return result
