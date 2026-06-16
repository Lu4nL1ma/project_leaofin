from django.contrib import admin
from app_leao.models import ContaPagar

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    # 1. Colunas que vão aparecer na listagem geral (estilo tabela)
    list_display = (
        'vencimento', 
        'fornecedor', 
        'categoria', 
        'banco', 
        'valor', 
        'status', 
        'conciliado'
    )
    
    # 2. Transforma esses campos em links clicáveis para abrir a edição
    list_display_links = ('vencimento', 'fornecedor')
    
    # 3. Cria uma barra de pesquisa para buscar rapidamente por texto
    search_fields = ('fornecedor', 'categoria', 'observacao', 'banco')
    
    # 4. Filtros práticos na lateral direita (as novas colunas ajudam muito aqui)
    list_filter = ('status', 'conciliado', 'vencimento', 'banco', 'categoria')
    
    # 5. Permite editar o Status e a Conciliação direto na tabela, sem ter que abrir o registro (opcional, muito produtivo!)
    list_editable = ('status', 'conciliado')
    
    # 6. Paginação: exibe 20 contas por página
    list_per_page = 20
    
    # 7. Organiza a estrutura da tela de formulário/edição do Admin em blocos
    fieldsets = (
        ('Informações Principais', {
            'fields': ('vencimento', 'valor', 'fornecedor')
        }),
        ('Classificação e Meio de Pagamento', {
            'fields': ('categoria', 'banco', 'parcela')
        }),
        ('Controlo de Pagamento e Fluxo', {
            'fields': ('ultimo_pagamento', 'status', 'conciliado')
        }),
        ('Informações Adicionais', {
            'fields': ('observacao',),
            'classes': ('collapse',), # Deixa o bloco de texto de observações recolhido por padrão
        }),
    )