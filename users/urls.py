from django.urls import path
from .analysis_views import upload_video, check_status, receive_result
from .views import (
    get_all_exercises,
    get_exercise_detail,
    search_exercise,
    user_settings,
    get_user_history,
    login,
    signup,
    get_all_courses,
    get_course_detail,
    get_courses_by_goal,
    get_exercises_by_type,
)

urlpatterns = [
    # Auth
    path('login/', login),
    path('signup/', signup),

    # Exercises
    path('exercises/', get_all_exercises),
    path('exercises/search/', search_exercise),
    path('exercises/type/', get_exercises_by_type),
    path('exercises/<str:exercise_id>/', get_exercise_detail),

    # Users
    path('users/<str:user_id>/settings/', user_settings),
    path('users/<str:user_id>/history/', get_user_history),

    # Courses
    path('courses/', get_all_courses),
    path('courses/goal/', get_courses_by_goal),
    path('courses/<str:course_id>/', get_course_detail),
    path('analysis/upload/', upload_video),
    path('analysis/<str:job_id>/status/', check_status),
    path('analysis/<str:job_id>/result/', receive_result),


]