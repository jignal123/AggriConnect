from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken , AuthenticationFailed
from farmer.models import Farmer
from Admin.models import Admin
from wholesaler.models import Wholesaler

class RedisBlackListJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):

        user_id = validated_token["user_id"]
        role = validated_token.get("role",None)
        try :
            if role == "farmer":
                return Farmer.objects.get(pk=user_id)

            elif role == "wholesaler":
                return Wholesaler.objects.get(pk=user_id)
            else:
                return Admin.objects.get(pk=user_id)
        except (Wholesaler.DoesNotExist,Admin.DoesNotExist,Farmer.DoesNotExist):
            raise AuthenticationFailed("User not found")

    def get_validated_token(self, raw_token):
        validated_token =  super().get_validated_token(raw_token)
        jti = validated_token.get("jti")
        if cache.get(f"blacklist({jti})",None):
            raise InvalidToken()
        
        return validated_token