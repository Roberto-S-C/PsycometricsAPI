from django.contrib import admin
from django.urls import path, include
from PsycometricsAPI.views import candidate_views, hr_views, test_views, result_views, email_auth_views 
from PsycometricsAPI.views.microsoft_auth_view import microsoft_auth
from PsycometricsAPI.views.google_auth_views import google_auth
from PsycometricsAPI.views.hr_views import generate_candidate_code
from PsycometricsAPI.views.candidate_views import verify_candidate_code
from PsycometricsAPI.views.candidate_views import verify_completed_test


urlpatterns = [
    path('api/candidates/', candidate_views.candidate_list),
    path('api/candidates/verify-code/', verify_candidate_code),
    path('api/candidates/completed-test/', verify_completed_test),
    path("api/candidates/<str:id>/", candidate_views.candidate_detail),

    path('api/hrs/', hr_views.hr_list),
    path("api/hrs/<str:id>/", hr_views.hr_detail),
    path('api/hrs/generate-code/', generate_candidate_code),

    path('api/tests/', test_views.test_list),
    path("api/tests/<str:id>/", test_views.test_detail),

    path('api/results/', result_views.result_list),
    path("api/results/<str:id>/", result_views.result_detail),

    path('api/signup/', email_auth_views.signup),
    path('api/login/', email_auth_views.login),

    path('api/microsoft/auth/', microsoft_auth),
    path('api/google/auth/', google_auth),
]
