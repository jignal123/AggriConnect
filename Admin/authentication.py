from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class RedisBlackListJWTAuthentication(JWTAuthentication):
    def get_validated_token(self, raw_token):
        validated_token =  super().get_validated_token(raw_token)
        jti = validated_token.get("jti")
        if cache.get(f"blacklist({jti})",None):
            raise InvalidToken()
        
        return validated_token