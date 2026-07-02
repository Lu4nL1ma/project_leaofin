from django.contrib import admin
from .models import ContaPagar, Fornecedor, BancoSaldo, Categoria


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = (
        "vencimento",
        "fornecedor",
        "categoria",
        "valor",
        "juros",
        "status",
        "banco",
        "banco_pago",
        "conciliado",
    )

    list_filter = (
        "status",
        "categoria",
        "banco",
        "banco_pago",
        "conciliado",
        "vencimento",
        "ultimo_pagamento",
    )

    search_fields = (
        "fornecedor",
        "categoria",
        "banco",
        "banco_pago",
        "observacao",
    )

    ordering = ("-vencimento",)

    list_per_page = 30

    date_hierarchy = "vencimento"

    readonly_fields = ()

    fieldsets = (
        ("Dados da Conta", {
            "fields": (
                "vencimento",
                "fornecedor",
                "categoria",
                "parcela",
            )
        }),
        ("Valores", {
            "fields": (
                "valor",
                "juros",
            )
        }),
        ("Pagamento", {
            "fields": (
                "status",
                "ultimo_pagamento",
                "banco",
                "banco_pago",
                "conciliado",
            )
        }),
        ("Observações", {
            "fields": (
                "observacao",
            )
        }),
    )


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = (
        "razao_social",
        "nome_fantasia",
        "cnpj",
        "telefone",
        "email",
        "cidade",
        "estado",
        "ativo",
    )

    list_filter = (
        "ativo",
        "estado",
        "cidade",
    )

    search_fields = (
        "razao_social",
        "nome_fantasia",
        "cnpj",
        "email",
        "telefone",
    )

    ordering = ("razao_social",)

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    list_per_page = 30

    fieldsets = (
        ("Dados Gerais", {
            "fields": (
                "razao_social",
                "nome_fantasia",
                "cnpj",
                "ativo",
            )
        }),
        ("Contato", {
            "fields": (
                "email",
                "telefone",
            )
        }),
        ("Endereço", {
            "fields": (
                "logradouro",
                "cidade",
                "estado",
            )
        }),
        ("Controle", {
            "fields": (
                "criado_em",
                "atualizado_em",
            )
        }),
    )


@admin.register(BancoSaldo)
class BancoSaldoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    ordering = ("nome",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "grupo",
        "tipo",
        "criado_em",
    )

    list_filter = (
        "tipo",
        "grupo",
    )

    search_fields = (
        "nome",
        "grupo",
        "descricao",
    )

    ordering = ("nome",)

    readonly_fields = (
        "criado_em",
    )

    fieldsets = (
        ("Informações", {
            "fields": (
                "nome",
                "grupo",
                "tipo",
                "descricao",
            )
        }),
        ("Controle", {
            "fields": (
                "criado_em",
            )
        }),
    )