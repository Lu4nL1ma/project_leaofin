from django.contrib import admin
from django.urls import path
from app_leao.views import *

urlpatterns = [
    path('login/', tela_login, name='tela_login'),
    path('login/entrar/', login_usuario, name='login_usuario'),
    path('logout/', logout_usuario, name='logout_usuario'),
    path('', home, name="homes"),
    path('dashboard/', dashboard_leve, name='dashboard_financeiro'),
    path('form/', form, name="forms"),
    path('fornecedor/novo/', cadastrar_fornecedor, name='cadastrar_fornecedor'),
    path('concili/<int:identi>/', conciliar, name="concili"), 
    path('conciliacao/', aba_conciliacao, name='aba_conciliacao'),
    path('processar-ofx-ajax/', processar_ofx_ajax, name='processar_ofx_ajax'),
    path('importar-xlsx/', importar_xlsx, name='importar_xlsx'),
    path('baixar-planilha-padrao/', baixar_planilha_padrao, name='baixar_planilha_padrao'),
    path('atualizar-registro/', atualizar_registro, name='atualizar_registro'),
    path('importar-caixa/', importar_fechamento_caixa, name='importar_fechamento_caixa'),
    path('deposito/', deposito, name='deposito'),
    path('contas-pagar/exportar-excel/', exportar_contas_pagar_excel, name='exportar_contas_pagar_excel'),
    
    # 🔥 ADICIONE ESTA LINHA AQUI:
    path('gravar-conciliacao-lote/', salvar_conciliacao_lote, name='gravar_conciliacao_lote'),

    path("provisao/", provisao_periodo, name="provisao"),  
    path("saldo/", saldo, name="saldo"),  
    path('atualizar-status-json/<int:identi>/', atualizar_status_json, name='atualizar_status_json'),
    path("admin/", admin.site.urls),
]