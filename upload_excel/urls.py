from django.urls import path
from .views import upload_file_view, get_schemes,success_page

urlpatterns = [
    path("", upload_file_view, name="upload_file"),
    path('success_page', success_page, name= 'success_page'),
    path("get-schemes/<int:amc_id>/", get_schemes, name="get_schemes"),
]
