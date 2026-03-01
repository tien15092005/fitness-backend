from django.urls import path
from .views import get_user_history
from .views import (
    get_all_exercises,
    get_exercise_detail,
    search_exercise,
    user_settings
)

urlpatterns = [
    path('exercises/', get_all_exercises),
    path('exercises/search/', search_exercise),
    path('exercises/<str:exercise_id>/', get_exercise_detail),

    path('users/<str:user_id>/settings/', user_settings),
    path('users/<str:user_id>/history/', get_user_history),
]

