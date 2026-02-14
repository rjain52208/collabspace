from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.DocumentViewSet, basename='document')
router.register(r'activities', views.ActivityLogViewSet, basename='activity')

urlpatterns = [
    path('register/', views.register, name='register'),
    path('me/', views.current_user, name='current_user'),
    path('', include(router.urls)),
]
