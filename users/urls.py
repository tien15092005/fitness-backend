from django.urls import path
from .views import (
    get_all_exercises,
    get_exercise_detail,
    search_exercise,
    user_settings,
    get_user_history,
    login,
    get_all_courses,
    get_course_detail,
    get_courses_by_goal,
)

urlpatterns = [
    path('exercises/', get_all_exercises),
    path('exercises/search/', search_exercise),
    path('exercises/<str:exercise_id>/', get_exercise_detail),

    path('users/<str:user_id>/settings/', user_settings),
    path('users/<str:user_id>/history/', get_user_history),
    path('login/', login),

    path('courses/', get_all_courses),
    path('courses/goal/', get_courses_by_goal),
    path('courses/<str:course_id>/', get_course_detail),
]