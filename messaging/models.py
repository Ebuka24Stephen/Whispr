from django.db import models

from accounts.models import User 


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='send_message')
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='receive_message')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    