from django.contrib import admin
from app_leao.models import ContaPagar

# Register your models here.

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    # Colunas que vão aparecer na listagem geral do painel
    list_display = ('vencimento', 'fornecedor', 'categoria', 'banco', 'parcela', 'valor')
    
    # Transforma esses campos em links para clicar e editar a conta
    list_display_links = ('vencimento', 'fornecedor')
    
    # Cria uma barra de pesquisa útil para buscar por fornecedor ou categoria
    search_fields = ('fornecedor', 'categoria', 'observacao')
    
    # Filtros laterais para facilitar a navegação (ajuda muito quando tiver muitas contas)
    list_filter = ('vencimento', 'categoria', 'banco')
    
    # Paginação: exibe 20 contas por página
    list_per_page = 20
    
    # Organiza os campos dentro da tela de edição/cadastro em blocos
    fieldsets = (
        ('Informações Principais', {
            'fields': ('vencimento', 'valor', 'fornecedor')
        }),
        ('Classificação e Pagamento', {
            'fields': ('categoria', 'banco', 'parcela')
        }),
        ('Informações Adicionais', {
            'fields': ('observacao',),
            'classes': ('collapse',), # Deixa o bloco de observação recolhido por padrão
        }),
    )