from django.contrib import admin
from django.urls import path
from app_leao.views import home, form

urlpatterns = [
    path('', home, name="homes"),
    path('/form', form, name="forms"),
    path("admin/", admin.site.urls),
]
