# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('live/',views.live, name='live'),
    path('footbal/',views.football,name='football'),
    path('footbal/results',views.football_results,name='football_results'),
    path('error/',views.error,name='error'),
    path('game_detail/<int:game_id>',views.game_detail,name='game_detail'),
    path('check_codes/',views.check_codes,name="check_codes"),
    path('logout/',views.logOut,name='logOut'),
    path('football/<str:country>/<str:league>/',views.football_detail,name='football_detail'),
    path('football/<str:country>/<str:league>/<str:matches>/',views.bets,name='bets'),
]
