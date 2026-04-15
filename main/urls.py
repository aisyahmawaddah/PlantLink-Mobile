from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Website routes (render HTML)
    path('', views.home, name='home'),
    path('login/', views.logPlantFeed, name='logPlantFeed'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),

    # Mobile API routes (return JSON)
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
