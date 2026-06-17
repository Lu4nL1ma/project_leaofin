from django.contrib import admin
from django.urls import path
from app_leao.views import home, form, conciliar

urlpatterns = [
    path('', home, name="homes"),
    path('/form', form, name="forms"),
    path('/concili', conciliar, name="concili"),
    path("admin/", admin.site.urls),
]
