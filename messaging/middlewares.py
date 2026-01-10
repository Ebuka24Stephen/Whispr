from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from urllib.parse import parse_qs

def extract_token(scope):
    q_string = scope['query_string']
    query = parse_qs(q_string.decode())
    return query.get("token", [None])[0]



class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner 

    async def __call__(self, scope, receive, send):
        token = extract_token(scope)
        if token is None:
            scope['user'] = AnonymousUser()
        else:
            try:
                token_obj = await database_sync_to_async(
                    Token.objects.select_related('user').get
                )(key=token)
                scope['user'] = token_obj.user 
            except Token.DoesNotExist:
                    scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)
