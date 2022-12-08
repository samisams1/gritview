from django.contrib import admin
from django.urls import path
from . import app

urlpatterns = [
    path('professor/', app.professor),
    path('course/', app.course),
    path('review/', app.review),
    path('reviewapproval/', app.review_approval),
    path('trending/', app.trending),
    path('track/', app.track),
    path('signup/', app.signup),
    path('login/', app.login),
    path('logout/', app.logout),
]