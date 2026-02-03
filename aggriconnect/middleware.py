from urllib.parse import parse_qs
from Admin.models import Admin
from farmer.models import Farmer
from wholesaler.models import Wholesaler
from django.contrib.auth.models import AnonymousUser
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.exceptions import TokenError,InvalidToken
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async

@database_sync_to_async
def get_user(user_id,role:str):
    try:
        if role.lower() == "admin":
            user = Admin.objects.get(id = user_id)
        elif role.lower() == "farmer":
            user = Farmer.objects.get(f_id = user_id)
        elif role.lower() == "wholesaler":
            user = Wholesaler.objects.get(w_id = user_id)
        return user
    except(Admin.DoesNotExist,Farmer.DoesNotExist,Wholesaler.DoesNotExist):
        return AnonymousUser()
    
class JwtAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode("utf8"))
        token_key = query_string.get("token")
        role = query_string.get("role")
        if token_key and role:
            try:
                access_token = AccessToken(token_key[0])
                scope["user"] = await get_user(access_token["user_id"],role[0])
            except(TokenError,InvalidToken) as e:
                print(f"JWT Authentication Failed : {e}")
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope,receive,send)
    
def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)