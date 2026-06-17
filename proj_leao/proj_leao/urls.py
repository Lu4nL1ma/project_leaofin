from django.contrib import admin
from django.urls import path
from app_leao.views import home, form, conciliar, atualizar_status_json

urlpatterns = [
    path('', home, name="homes"),
    path('form/', form, name="forms"), # Removida a barra inicial e adicionada no final
    path('concili/<int:identi>/', conciliar, name="concili"), # Removida a barra inicial
    path('atualizar-status-json/<int:identi>/', atualizar_status_json, name='atualizar_status_json'),
    path("admin/", admin.site.urls),
]