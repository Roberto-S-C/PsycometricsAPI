from django.contrib import admin
from django.urls import path, include
from PsycometricsAPI.views import candidate_views, hr_views, test_views, result_views
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.microsoft.views import MicrosoftGraphOAuth2Adapter
from allauth.socialaccount.providers.linkedin_oauth2.views import LinkedInOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView


# Vistas personalizadas para OAuth
class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


class MicrosoftLogin(SocialLoginView):
    adapter_class = MicrosoftGraphOAuth2Adapter


class LinkedInLogin(SocialLoginView):
    adapter_class = LinkedInOAuth2Adapter


urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # OAuth
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/microsoft/', MicrosoftLogin.as_view(), name='microsoft_login'),
    path('api/auth/linkedin/', LinkedInLogin.as_view(), name='linkedin_login'),

    # API endpoints
    path('api/candidates/', candidate_views.candidate_list),
    path("api/candidates/<str:id>/", candidate_views.candidate_detail),
    path('api/hrs/', hr_views.hr_list),
    path("api/hrs/<str:id>/", hr_views.hr_detail),
    path('api/tests/', test_views.test_list),
    path("api/tests/<str:id>/", test_views.test_detail),
    path('api/results/', result_views.result_list),
    path("api/results/<str:id>/", result_views.result_detail),
]