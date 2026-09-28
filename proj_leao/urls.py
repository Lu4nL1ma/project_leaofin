# app_leao/urls.py

from django.urls import path
from app_leao.views import (
    auth_views,
    caixa_views,
    conciliacao_views,
    core_views,
    dashboard_views,
    despesas_views,
    drive_views,
    excel_views,
    tarefas_views,
    extratos_em_ofx,
    comparar_planilhas
)

urlpatterns = [
    # --- CORE & NAVEGAÇÃO BÁSICA ---
    path('', core_views.home, name='home'),
    path('rh/', core_views.recursos_humanos, name='recursosh'),
    path("consolidar-ofx/", extratos_em_ofx.upload_ofx_view, name="consolidar_ofx"),
    path("comparar-planilhas/", comparar_planilhas.comparar_planilhas_view, name="comparar_planilhas"),

    # --- AUTENTICAÇÃO ---
    path('login/', auth_views.tela_login, name='tela_login'),
    path('login/autenticar/', auth_views.login_usuario, name='login_usuario'),
    path('logout/', auth_views.logout_usuario, name='logout_usuario'),

    # --- DESPESAS & FORNECEDORES ---
    path('despesas/', despesas_views.despesas, name='despesas'),
    path('despesas/novo/', despesas_views.form, name='forms'),
    path('despesas/atualizar/', despesas_views.atualizar_registro, name='atualizar_registro'),
    path('despesas/atualizar-status/<int:identi>/', despesas_views.atualizar_status_json, name='atualizar_status_json'),
    path('provisao/', despesas_views.provisao_periodo, name='provisao'),
    path('fornecedor/cadastrar/', despesas_views.cadastrar_fornecedor, name='cadastrar_fornecedor'),

    # --- CONCILIAÇÃO BANCÁRIA & OFX ---
    path('conciliacao/', conciliacao_views.aba_conciliacao, name='aba_conciliacao'),
    path('conciliar/<int:identi>/', conciliacao_views.conciliar, name='conciliar'),
    path('conciliacao/processar-ofx/', conciliacao_views.processar_ofx_ajax, name='processar_ofx_ajax'),
    path('conciliacao/gravar-lote/', conciliacao_views.gravar_conciliacao_lote, name='gravar_conciliacao_lote'),
    path('conciliacao/salvar-lote/', conciliacao_views.salvar_conciliacao_lote, name='salvar_conciliacao_lote'),

    # --- TAREFAS ---
    path('tarefas/', tarefas_views.tarefas, name='tarefas'),
    path('tarefas/<int:pk>/status/', tarefas_views.alternar_status_tarefa, name='alternar_status_tarefa'),
    path('tarefas/<int:pk>/deletar/', tarefas_views.deletar_tarefa, name='deletar_tarefa'),

    # --- CAIXA, SALDOS & DEPÓSITOS ---
    path('saldo/', caixa_views.saldo, name='saldo'),
    path('deposito/', caixa_views.deposito, name='deposito'),
    path('caixa/importar/', caixa_views.importar_fechamento_caixa, name='importar_fechamento_caixa'),

    # --- IMPORTAÇÃO & EXPORTAÇÃO EXCEL ---
    path('excel/importar/', excel_views.importar_xlsx, name='importar_xlsx'),
    path('excel/modelo/', excel_views.baixar_planilha_padrao, name='baixar_planilha_padrao'),
    path('excel/exportar/', excel_views.exportar_contas_pagar_excel, name='exportar_contas_pagar_excel'),

    # --- DASHBOARDS & RELATÓRIOS ---
    path('dashboard/', dashboard_views.dashboard_leve, name='dashboard_financeiro'),

    # --- ARQUIVOS & GOOGLE DRIVE ---
    path('drive/upload/', drive_views.upload_view, name='upload_form'),
    path('drive/arquivos/', drive_views.file_list_view, name='file_list'),
    path('drive/download/<int:doc_id>/', drive_views.download_file_view, name='download_file'),
    path('drive/deletar/<int:doc_id>/', drive_views.delete_file_view, name='delete_file'),
]