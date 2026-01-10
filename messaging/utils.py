from channels.layers import get_channel_layer
import redis
from django.conf import settings

redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)

ONLINE_USERS_KEY = "online_users"


