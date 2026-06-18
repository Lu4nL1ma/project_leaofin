from django.db import models

class ContaPagar(models.Model):
    
    # Data de vencimento da fatura/conta
    vencimento = models.DateField(
        verbose_name="Data de Vencimento",
        db_index=True
    )
    
    # Nome do fornecedor
    fornecedor = models.CharField(
        max_length=150, 
        verbose_name="Fornecedor",
        db_index=True
    )
    
    # Categoria do gasto (ex: Energia Elétrica, Aluguel)
    categoria = models.CharField(
        max_length=100, 
        verbose_name="Categoria",
        db_index=True
    )
    
    # Banco ou Meio de Pagamento (ex: Mercado Pago, Itaú)
    banco = models.CharField(
        max_length=100, 
        verbose_name="Banco / Meio de Pagamento"
    )
    
    # Formato de parcela (ex: "1/1" ou "3/12")
    parcela = models.CharField(
        max_length=20, 
        verbose_name="Parcela", 
        default="1/1"
    )
    
    # Valor financeiro (até 999.999.999,99)
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor (R$)"
    )
    
    # Observações adicionais sobre a conta (Opcional)
    observacao = models.TextField(
        verbose_name="Observação",
        blank=True,
        null=True
    )

    # ==========================================================================
    # NOVAS COLUNAS AJUSTADAS PARA NÃO DAR ERRO DE MIGRAÇÃO
    # ==========================================================================

    # Corrigido: Campo de data não aceita "" como padrão. Mudado para aceitar nulo.
    ultimo_pagamento = models.DateField(
        verbose_name="Último Pagamento",
        db_index=True,
        blank=True,
        null=True
    )

    # Valor financeiro (até 999.999.999,99)
    juros = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Juros (R$)",
        default=0
    )

    # Corrigido: Mudado para CharField (texto curto) e definido um valor padrão de texto
    status = models.CharField(
        max_length=30,
        verbose_name="Status",
        default="Pendente",
        blank=True
    )

    # Corrigido: Fechado o parêntese e adicionado null/blank para aceitar dados antigos vazios
    conciliado = models.CharField(
        max_length=20,
        verbose_name="Conciliado",
        default="Não",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"
        ordering = ['-vencimento']

    def __str__(self):
        return f"{self.fornecedor} - {self.vencimento} - R$ {self.valor}"