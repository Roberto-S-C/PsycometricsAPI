from django.contrib import admin
from django.urls import path
from PsycometricsAPI.views import candidate_views, hr_views, test_views,result_views 


urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('api/candidates', candidate_views.candidate_list),
    path("api/candidates/<str:id>/", candidate_views.candidate_detail),

    path('api/hrs', hr_views.hr_list),
    path("api/hrs/<str:id>/", hr_views.hr_detail),

    path('api/tests', test_views.test_list),
    path("api/tests/<str:id>/", test_views.test_detail),

    path('api/results', result_views.result_list),
    path("api/results/<str:id>/", result_views.result_detail)
]
