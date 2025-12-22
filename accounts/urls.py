from django.urls import path 
from .views import LoginApiView, RegisterApiView

urlpatterns = [
    path('accounts/login/', LoginApiView.as_view()),
    path('accounts/register/', RegisterApiView.as_view())
]