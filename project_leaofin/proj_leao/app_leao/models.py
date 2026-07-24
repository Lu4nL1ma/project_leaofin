from django.db import models
from django.core.validators import RegexValidator

# ==============================================================================
# 📦 2. O PLANEJAMENTO: CONTAS A PAGAR
# ==============================================================================
class ContaPagar(models.Model):
    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Pago', 'Pago'),
    ]

    vencimento = models.DateField(verbose_name="Data de Vencimento", db_index=True)
    fornecedor = models.CharField(max_length=150, verbose_name="Fornecedor", db_index=True)
    
    # Removido FK -> Salva apenas o nome/ID da categoria como texto
    categoria = models.CharField(
        max_length=100,
        null=True, 
        blank=True, 
        verbose_name="Categoria"
    )
    
    banco = models.CharField(max_length=100, verbose_name="Banco / Meio de Pagamento Previsto")
    nota_fiscal = models.CharField(max_length=50, verbose_name="Nota Fiscal", default="", blank=True)
    parcela = models.CharField(max_length=20, verbose_name="Parcela", default="1/1")
    valor = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor Original (R$)")
    linha_boleto = models.TextField(verbose_name="Linha Digitável do Boleto", blank=True, null=True)
    observacao = models.TextField(verbose_name="Observação", blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Pendente", db_index=True)
    data_inclusao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Inclusão")

    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"
        ordering = ['-vencimento']

    def __str__(self):
        return f"{self.fornecedor} - Venc: {self.vencimento} - R$ {self.valor}"

# ==============================================================================
# 🏦 3. A REALIDADE: TRANSAÇÕES DO EXTRATO BANCÁRIO (OFX)
# ==============================================================================
class TransacaoExtrato(models.Model):
    banco_origem = models.CharField(max_length=100, verbose_name="Banco do Extrato", db_index=True)
    data_banco = models.DateField(verbose_name="Data no Extrato", db_index=True)
    descricao_ofx = models.CharField(max_length=255, verbose_name="Descrição / Memo do Banco")
    valor_extrato = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor no Extrato (R$)")
    fitid = models.CharField(max_length=100, unique=True, verbose_name="ID Único da Transação (FITID)")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transação do Extrato"
        verbose_name_plural = "Transações do Extrato"
        ordering = ['-data_banco']

    def __str__(self):
        return f"[{self.banco_origem}] {self.data_banco} - R$ {self.valor_extrato}"

# ==============================================================================
# 🔗 4. O VÍNCULO: CONCILIAÇÃO BANCÁRIA (MECANISMO DE AUDITORIA)
# ==============================================================================
class ConciliacaoBancaria(models.Model):
    # Removido FK -> Guarda apenas o ID numérico da Conta a Pagar
    conta_pagar_id = models.IntegerField(
        verbose_name="ID da Conta do Sistema",
        db_index=True
    )
    # Removido FK -> Guarda apenas o ID numérico da Transação
    transacao_extrato_id = models.IntegerField(
        verbose_name="ID da Linha do Extrato",
        db_index=True
    )
    
    data_conciliacao = models.DateField(verbose_name="Data Real do Pagamento", db_index=True)
    banco_pago = models.CharField(max_length=100, verbose_name="Banco Efetivo do Pagamento")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conciliação Bancária"
        verbose_name_plural = "Conciliações Bancárias"
        unique_together = ('conta_pagar_id', 'transacao_extrato_id')

    # Métodos auxiliares para buscar os objetos de forma segura (Prevenção de erro "Não Existe")
    @property
    def conta_pagar_obj(self):
        """Busca a conta com segurança. Se não existir, retorna None."""
        return ContaPagar.objects.filter(id=self.conta_pagar_id).first()

    @property
    def transacao_extrato_obj(self):
        """Busca a transação com segurança. Se não existir, retorna None."""
        return TransacaoExtrato.objects.filter(id=self.transacao_extrato_id).first()

    # 🧮 INTEGRAÇÃO MATEMÁTICA DE JUROS E DESCONTOS (TRATADA CONTRA ERROS)
    @property
    def diferenca(self):
        """Retorna o delta absoluto. Se algum objeto sumiu, retorna 0."""
        conta = self.conta_pagar_obj
        transacao = self.transacao_extrato_obj
        if not conta or not transacao:
            return 0
        return transacao.valor_extrato - conta.valor

    @property
    def juros(self):
        """Se o banco cobrou a mais do que o valor original, extrai o juro."""
        return self.diferenca if self.diferenca > 0 else 0

    @property
    def desconto(self):
        """Se o banco cobrou a menos do que o valor original, extrai o desconto."""
        return abs(self.diferenca) if self.diferenca < 0 else 0

    def __str__(self):
        detalhe = "Batida Exata"
        conta = self.conta_pagar_obj
        
        # Valida se o objeto pai ainda existe antes de tentar ler atributos dele
        fornecedor = conta.fornecedor if conta else f"[CONTA DELETADA ID: {self.conta_pagar_id}]"
        
        if self.juros > 0:
            detalhe = f"Juros: R$ {self.juros}"
        elif self.desconto > 0:
            detalhe = f"Desconto: R$ {self.desconto}"
            
        return f"Conciliação: {fornecedor} | {detalhe}"


class Fornecedor(models.Model):
    razao_social = models.CharField(max_length=255, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=255, verbose_name="Nome Fantasia", blank=True, null=True)
    
    cnpj_validator = RegexValidator(
        regex=r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
        message="O CNPJ deve estar no formato 00.000.000/0000-00"
    )
    cnpj = models.CharField(max_length=18, unique=True, validators=[cnpj_validator], verbose_name="CNPJ")
    
    email = models.EmailField(max_length=254, verbose_name="E-mail", blank=True, null=True)
    telefone = models.CharField(max_length=20, verbose_name="Telefone", blank=True, null=True)
    
    logradouro = models.CharField(max_length=255, verbose_name="Endereço", blank=True, null=True)
    cidade = models.CharField(max_length=100, verbose_name="Cidade", blank=True, null=True)
    estado = models.CharField(max_length=2, verbose_name="Estado (UF)", blank=True, null=True)
    
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['razao_social']

    def __str__(self):
        return self.nome_fantasia if self.nome_fantasia else self.razao_social


class BancoSaldo(models.Model):
    nome = models.CharField(max_length=50, unique=True, verbose_name="Nome do Banco/Conta")

    cnpj_unidade = models.CharField(max_length=50, unique=False, verbose_name="cnpj_unidade", default="-")
    
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