from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/documents/', consumers.DashboardConsumer.as_asgi()),
    path('ws/document/<int:document_id>/', consumers.DocumentConsumer.as_asgi()),
]
