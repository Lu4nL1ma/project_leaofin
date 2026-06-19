from django.contrib import admin
from django.urls import path
# Importe todas as suas views do app_leao diretamente aqui se este for o seu urls.py único
from app_leao.views import home, form, conciliar, aba_conciliacao, atualizar_status_json, provisao_periodo

urlpatterns = [
    path('', home, name="homes"),
    path('form/', form, name="forms"), 
    path('concili/<int:identi>/', conciliar, name="concili"), 
    path('conciliacao/', aba_conciliacao, name='aba_conciliacao'), # << O Django precisa ler isso aqui!
    path("provisao/", provisao_periodo, name="provisao"),  
    path('atualizar-status-json/<int:identi>/', atualizar_status_json, name='atualizar_status_json'),
    path("admin/", admin.site.urls),
]