from django.contrib import admin
from app_leao.models import ContaPagar, TransacaoExtrato, ConciliacaoBancaria, Categoria, Fornecedor, BancoSaldo

# ==============================================================================
# 🏷️ CATEGORIA ADMIN
# ==============================================================================
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'criado_em')
    list_filter = ('tipo',)
    search_fields = ('nome', 'descricao')
    ordering = ('nome',)

# ==============================================================================
# 📦 CONTAS A PAGAR ADMIN (PLANEJAMENTO)
# ==============================================================================
@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('fornecedor', 'vencimento', 'categoria', 'banco', 'valor', 'parcela', 'status')
    list_filter = ('status', 'banco', 'categoria', 'vencimento')
    search_fields = ('fornecedor', 'nota_fiscal', 'observacao')
    ordering = ('-vencimento',)
    date_hierarchy = 'vencimento'

# ==============================================================================
# 🏦 TRANSAÇÕES DO EXTRATO ADMIN (REALIDADE DO OFX)
# ==============================================================================
@admin.register(TransacaoExtrato)
class TransacaoExtratoAdmin(admin.ModelAdmin):
    list_display = ('banco_origem', 'data_banco', 'descricao_ofx', 'valor_extrato', 'fitid')
    list_filter = ('banco_origem', 'data_banco')
    search_fields = ('descricao_ofx', 'fitid')
    ordering = ('-data_banco',)
    date_hierarchy = 'data_banco'

# ==============================================================================
# 🔗 CONCILIAÇÃO BANCÁRIA ADMIN (VÍNCULOS DE AUDITORIA)
# ==============================================================================
@admin.register(ConciliacaoBancaria)
class ConciliacaoBancariaAdmin(admin.ModelAdmin):
    # ⚠️ CORREÇÃO: Mudado de atributos diretos para métodos dinâmicos que consultam os IDs
    list_display = (
        'id', 
        'get_fornecedor_sistema', 
        'banco_pago', 
        'data_conciliacao', 
        'get_valor_sistema', 
        'get_valor_banco', 
        'get_juros_calculados', 
        'get_desconto_calculado'
    )
    list_filter = ('banco_pago', 'data_conciliacao')
    search_fields = ('conta_pagar_id', 'transacao_extrato_id', 'banco_pago')
    ordering = ('-data_conciliacao',)
    date_hierarchy = 'data_conciliacao'

    # 👤 Busca o fornecedor dinamicamente usando o ID puro da conta
    @admin.display(description='Fornecedor (Sistema)')
    def get_fornecedor_sistema(self, obj):
        conta = ContaPagar.objects.filter(id=obj.conta_pagar_id).first()
        return conta.fornecedor if conta else f"Conta ID {obj.conta_pagar_id} (Removida)"

    # 💰 Busca o valor planejado original da conta pelo ID
    @admin.display(description='Valor Sistema (R$)')
    def get_valor_sistema(self, obj):
        conta = ContaPagar.objects.filter(id=obj.conta_pagar_id).first()
        return f"R$ {conta.valor:.2f}" if conta else "R$ 0,00"

    # 🏦 Busca o valor que de fato saiu do extrato pelo ID
    @admin.display(description='Valor Extrato (R$)')
    def get_valor_banco(self, obj):
        extrato = TransacaoExtrato.objects.filter(id=obj.transacao_extrato_id).first()
        return f"R$ {extrato.valor_extrato:.2f}" if extrato else "R$ 0,00"

    # 📈 Exibe a propriedade matemática calculada de Juros
    @admin.display(description='Juros (R$)')
    def get_juros_calculados(self, obj):
        # Como o cálculo de .juros depende de conta e extrato, tratamos em fallback
        conta = ContaPagar.objects.filter(id=obj.conta_pagar_id).first()
        extrato = TransacaoExtrato.objects.filter(id=obj.transacao_extrato_id).first()
        if conta and extrato:
            diferenca = extrato.valor_extrato - conta.valor
            return f"R$ {diferenca:.2f}" if diferenca > 0 else "R$ 0,00"
        return "R$ 0,00"

    # 📉 Exibe a propriedade matemática calculada de Desconto
    @admin.display(description='Desconto (R$)')
    def get_desconto_calculado(self, obj):
        conta = ContaPagar.objects.filter(id=obj.conta_pagar_id).first()
        extrato = TransacaoExtrato.objects.filter(id=obj.transacao_extrato_id).first()
        if conta and extrato:
            diferenca = extrato.valor_extrato - conta.valor
            return f"R$ {abs(diferenca):.2f}" if diferenca < 0 else "R$ 0,00"
        return "R$ 0,00"

# ==============================================================================
# 👤 REGISTROS COMPLEMENTARES
# ==============================================================================
@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'cnpj', 'cidade', 'estado')
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj')
    ordering = ('razao_social',)

@admin.register(BancoSaldo)
class BancoSaldoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj_unidade')
    search_fields = ('nome',)
    ordering = ('nome',)