from django.db import models
from django.core.validators import RegexValidator

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

    #banco ao qual foi pago
    banco_pago = models.CharField(
        max_length=100, 
        verbose_name="Banco / Meio de Pagamento",
        default='Definir'
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


class Fornecedor(models.Model):
    # Razão Social e Nome Fantasia
    razao_social = models.CharField(
        max_length=255, 
        verbose_name="Razão Social"
    )
    nome_fantasia = models.CharField(
        max_length=255, 
        verbose_name="Nome Fantasia", 
        blank=True, 
        null=True
    )
    
    # Documentação (Validador simples para formato de CNPJ: 00.000.000/0000-00)
    cnpj_validator = RegexValidator(
        regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
        message="O CNPJ deve estar no formato 00.000.000/0000-00"
    )
    cnpj = models.CharField(
        max_length=18, 
        unique=True, 
        validators=[cnpj_validator], 
        verbose_name="CNPJ"
    )
    
    # Contato
    email = models.EmailField(
        max_length=254, 
        verbose_name="E-mail", 
        blank=True, 
        null=True
    )
    telefone = models.CharField(
        max_length=20, 
        verbose_name="Telefone", 
        blank=True, 
        null=True
    )
    
    # Endereço (Opcional, mas recomendado)
    logradouro = models.CharField(max_length=255, verbose_name="Endereço", blank=True, null=True)
    cidade = models.CharField(max_length=100, verbose_name="Cidade", blank=True, null=True)
    estado = models.CharField(max_length=2, verbose_name="Estado (UF)", blank=True, null=True)
    
    # Controle Interno
    ativo = models.BooleanField(
        default=True, 
        verbose_name="Ativo"
    )
    criado_em = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Criado em"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True, 
        verbose_name="Atualizado em"
    )

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['razao_social']

    def __str__(self):
        # Retorna o nome fantasia se houver, senão a razão social
        return self.nome_fantasia if self.nome_fantasia else self.razao_social


# NOVA TABELA INDEPENDENTE PARA VOCÊ CADASTRAR OS BANCOS QUE QUISER
class BancoSaldo(models.Model):
    nome = models.CharField(max_length=50, unique=True, verbose_name="Nome do Banco/Conta")
    
    def __str__(self):
        return self.nome
        
    class Meta:
        verbose_name = "Conta com Saldo"
        verbose_name_plural = "Contas com Saldo"

class Categoria(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria", default="-")
    grupo = models.TextField(blank=True, null=True, verbose_name="grupo", default="-")
    tipo = models.CharField(max_length=50, verbose_name="Tipo de Categoria", default="-")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição", default="-")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['nome']

    def __str__(self):
        return self.nome