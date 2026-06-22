from django.contrib import admin
from .models import ContaPagar, Fornecedor, BancoSaldo

@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    # Colunas que vão aparecer na listagem geral
    list_display = (
        'vencimento', 
        'fornecedor', 
        'categoria', 
        'banco', 
        'parcela', 
        'valor', 
        'status', 
        'conciliado'
    )
    
    # Filtros que vão aparecer na barra lateral direita
    list_filter = ('status', 'conciliado', 'vencimento', 'categoria', 'banco')
    
    # Campos que permitem busca digitável
    search_fields = ('fornecedor', 'categoria', 'observacao')
    
    # Permite editar o status e a conciliação direto na lista, sem abrir o registro
    list_editable = ('status', 'conciliado')
    
    # Organização visual dos campos dentro do formulário de edição
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('fornecedor', 'categoria', 'valor', 'parcela')
        }),
        ('Planejamento e Vencimento', {
            'fields': ('vencimento', 'banco')
        }),
        ('Pagamento e Conciliação', {
            'fields': ('ultimo_pagamento', 'juros', 'banco_pago', 'status', 'conciliado')
        }),
        ('Informações Adicionais', {
            'fields': ('observacao',),
            'classes': ('collapse',),  # Minimiza este bloco por padrão
        }),
    )


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'cnpj', 'telefone', 'ativo')
    list_filter = ('ativo', 'estado', 'criado_em')
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj', 'email')
    list_editable = ('ativo',)
    
    # Define quais campos não podem ser editados manualmente (são automáticos)
    readonly_fields = ('criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Dados Cadastrais', {
            'fields': ('razao_social', 'nome_fantasia', 'cnpj', 'ativo')
        }),
        ('Contato', {
            'fields': ('email', 'telefone')
        }),
        ('Endereço', {
            'fields': ('logradouro', 'cidade', 'estado')
        }),
        ('Datas de Controle', {
            'fields': ('criado_em', 'atualizado_em'),
        }),
    )


@admin.register(BancoSaldo)
class BancoSaldoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)