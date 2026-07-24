import io
import json
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal, InvalidOperation
import openpyxl
from openpyxl import Workbook
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.paginator import Paginator
from django.db import transaction  # <-- ADICIONADO (para transaction.atomic)
from django.db.models import (
    Count, 
    Q, 
    Sum, 
    Value, 
    FloatField, 
    DecimalField  # <-- ADICIONADO (caso precise tratar Decimal no banco)
)
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from app_leao.models import (
    BancoSaldo,
    Categoria,
    ConciliacaoBancaria,
    ContaPagar,
    Fornecedor,
    TransacaoExtrato,
)

try:
    from ofxtools.Parser import OFXTree
except ImportError:
    OFXTree = None
from django.views.decorators.http import require_POST

STATUS_VALIDOS = [choice[0] for choice in ContaPagar.STATUS_CHOICES]


def parse_valor_brl(valor_str):
    """
    Converte texto de valor em formato brasileiro (2.089,78 ou 2089,78)
    ou já em formato com ponto (2089.78) para Decimal.
    Levanta InvalidOperation se o texto não for um número válido.
    """
    valor_str = valor_str.strip()
    if ',' in valor_str:
        # formato brasileiro: remove separador de milhar (.) e troca decimal (,) por (.)
        valor_str = valor_str.replace('.', '').replace(',', '.')
    return Decimal(valor_str)


def tela_login(request):
    if request.user.is_authenticated:
        return redirect('homes')
    return render(request, 'login.html')


def normalizar_data(val):
    """ Converte o valor retornado pelo openpyxl em um objeto datetime.date válido """
    if not val:
        return None
    
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val

    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                pass
                
    return None


def login_usuario(request):
    if request.method == "POST":
        usuario_post = request.POST.get("username")
        senha_post = request.POST.get("password")

        user = authenticate(request, username=usuario_post, password=senha_post)
        if user is not None:
            login(request, user)
            return redirect('homes')
        else:
            messages.error(request, "Usuário ou senha incorretos. Tente novamente.")
            return redirect('tela_login')

    return redirect('tela_login')


def logout_usuario(request):
    logout(request)
    return redirect('tela_login')


def home(request):
    data_atual = timezone.localdate()

    # Atualização automática de contas atrasadas no banco de dados
    ContaPagar.objects.filter(vencimento__lt=data_atual).exclude(status__icontains="Pago").update(status="Atrasado")

    queryset = ContaPagar.objects.all()

    # Captura de Filtros Dinâmicos
    filtro_conciliacao = request.GET.get("conciliacao")
    filtro_data = request.GET.get("data")
    filtro_fornecedor = request.GET.get("fornecedor")
    filtro_categoria = request.GET.get("categoria")
    filtro_banco = request.GET.get("banco")
    filtro_parcela = request.GET.get("parcela")
    filtro_valor = request.GET.get("valor")
    filtro_observacao = request.GET.get("observacao")
    filtro_status = request.GET.get("status")

    if filtro_conciliacao and filtro_conciliacao.strip():
        queryset = queryset.filter(conciliado__icontains=filtro_conciliacao)
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)
    if filtro_categoria and filtro_categoria.strip():
        queryset = queryset.filter(categoria__icontains=filtro_categoria)
    if filtro_banco and filtro_banco.strip():
        queryset = queryset.filter(banco__icontains=filtro_banco)
    if filtro_parcela and filtro_parcela.strip():
        queryset = queryset.filter(parcela__icontains=filtro_parcela)
    if filtro_valor and filtro_valor.strip():
        queryset = queryset.filter(valor__icontains=filtro_valor)
    if filtro_observacao and filtro_observacao.strip():
        queryset = queryset.filter(observacao__icontains=filtro_observacao)
    if filtro_status and filtro_status.strip():
        queryset = queryset.filter(status__icontains=filtro_status)

    if filtro_data and filtro_data.strip():
        try:
            data_objeto = datetime.strptime(filtro_data.strip(), "%d/%m/%Y")
            queryset = queryset.filter(vencimento=data_objeto.strftime("%Y-%m-%d"))
        except ValueError:
            messages.error(request, "Formato de data inválido. Use DD/MM/AAAA.")

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Listas usadas pra popular os <select> do modal de edição
    # (fornecedor/categoria/banco no ContaPagar são CharField de texto
    # puro, mas o valor digitado precisa vir padronizado dessas tabelas)
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
    categorias = Categoria.objects.all().order_by('nome')

    context = {
        "page_obj": page_obj,
        "bancos_disponiveis": bancos_disponiveis,  # usado em outros pontos do template
        "fornecedores": fornecedores,
        "categorias": categorias,
        "bancos": bancos_disponiveis,  # mesmo queryset, nome que o modal de edição espera
    }
    return render(request, "home.html", context)


def aba_conciliacao(request):
    # 1. Coletamos a lista de IDs de contas que JÁ FORAM conciliadas
    ids_conciliados = ConciliacaoBancaria.objects.values_list('conta_pagar_id', flat=True).distinct()

    # 2. MODIFICAÇÃO: Removemos o .exclude() para que tudo continue aparecendo na tela!
    queryset = ContaPagar.objects.filter(status__icontains="Pago").order_by("-vencimento")

    # Aplica o filtro de fornecedor se houver
    filtro_fornecedor = request.GET.get("fornecedor")
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)

    # 3. Cálculo dos totais direto no banco de dados (Mantido exatamente igual)
    ids_conta_manual = ConciliacaoBancaria.objects.filter(
        transacao_extrato_id=0
    ).values_list('conta_pagar_id', flat=True)
    
    total_manual = ContaPagar.objects.filter(
        id__in=ids_conta_manual
    ).aggregate(
        total=Coalesce(Sum('valor'), Value(0.0), output_field=FloatField())
    )['total']

    ids_extrato_ofx = ConciliacaoBancaria.objects.exclude(
        transacao_extrato_id=0
    ).values_list('transacao_extrato_id', flat=True)
    
    total_ofx = TransacaoExtrato.objects.filter(
        id__in=ids_extrato_ofx
    ).aggregate(
        total=Coalesce(Sum('valor_extrato'), Value(0.0), output_field=FloatField())
    )['total']

    total_conciliado = total_manual + total_ofx

    total_pendente = queryset.exclude(id__in=ids_conciliados).aggregate(
        total=Coalesce(Sum('valor'), Value(0.0), output_field=FloatField())
    )['total']

    # 4. Paginação
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')

    context = {
        'page_obj': page_obj,
        'total_conciliado': total_conciliado,
        'total_pendente': total_pendente, 
        'bancos_disponiveis': bancos_disponiveis,
        # Convertemos para set para busca ultra rápida no template com o operador "in"
        'ids_conciliados': set(ids_conciliados), 
        'filtro_fornecedor': filtro_fornecedor,
    }
    return render(request, 'conciliacao.html', context)


def processar_ofx_ajax(request):
    if request.method != "POST" or not request.FILES.get("arquivo_ofx"):
        return JsonResponse({'success': False, 'error': 'Método inválido ou arquivo não enviado.'})

    banco_destino = request.POST.get("banco_destino")
    arquivo_ofx = request.FILES.get("arquivo_ofx")

    if OFXTree is None:
        return JsonResponse({'success': False, 'error': 'Biblioteca ofxtools não está instalada no ambiente.'})

    try:
        # 1. Lê o arquivo vindo do upload diretamente como texto (string)
        conteudo = arquivo_ofx.read().decode("utf-8", errors="ignore")

        # 2. Correção cirúrgica para datas zeradas que quebram o parser
        conteudo_corrigido = conteudo.replace("00000000000000", "20000101120000").replace("00000000", "20000101")

        # 3. Transforma o texto corrigido de volta em bytes na memória e faz o parse
        parser = OFXTree()
        parser.parse(io.BytesIO(conteudo_corrigido.encode("utf-8")))
        obj = parser.convert()

        # 4. Acessa o primeiro extrato de forma direta
        transacoes = obj.statements[0].banktranlist
        transacoes_ofx = []
        datas_transacoes = []  # Lista auxiliar para capturar o período real das transações

        # --- BUSCA DE HISTÓRICO: Pegamos os IDs de transações do extrato que JÁ foram conciliadas ---
        extratos_ja_conciliados = set(
            ConciliacaoBancaria.objects.exclude(
                transacao_extrato_id=0
            ).values_list('transacao_extrato_id', flat=True)
        )

        # Usamos uma transação atômica para salvar tudo de uma vez com máxima performance
        with transaction.atomic():
            # 5. Percorre as transações filtrando estritamente as saídas do extrato (débitos)
            for tx in transacoes:
                # Converte o valor original do extrato para Decimal com segurança
                valor_trnamt = Decimal(str(tx.trnamt))
                if valor_trnamt >= 0:
                    continue  # Entrada (crédito) -> ignora

                valor_ajustado = abs(valor_trnamt)
                
                # --- TRATAMENTO ROBUSTO DE DATA ---
                # Garante que dtposted vire um objeto date puro do Python para evitar TypeErrors
                data_real = None
                if tx.dtposted:
                    if isinstance(tx.dtposted, (datetime, date)):
                        data_real = tx.dtposted if isinstance(tx.dtposted, date) else tx.dtposted.date()
                    else:
                        # Se por acaso o parser trouxe como string, tenta converter
                        try:
                            data_real = datetime.strptime(str(tx.dtposted)[:10], '%Y-%m-%d').date()
                        except ValueError:
                            pass

                if data_real:
                    datas_transacoes.append(data_real)

                # Mantém a formatação segura para gravação e exibição
                data_iso = data_real.strftime('%Y-%m-%d') if data_real else None
                data_formatada = data_real.strftime('%d/%m/%Y') if data_real else '-'

                transacao_banco, _ = TransacaoExtrato.objects.update_or_create(
                    fitid=tx.fitid,
                    defaults={
                        'banco_origem': banco_destino,
                        'data_banco': data_iso,
                        'descricao_ofx': tx.memo if tx.memo else (tx.name or "Transação sem descrição"),
                        'valor_extrato': valor_ajustado,
                    }
                )

                # Verifica se este registro do extrato já possui conciliação
                ja_conciliado = transacao_banco.id in extratos_ja_conciliados

                transacoes_ofx.append({
                    'id': transacao_banco.id,
                    'data': data_formatada,
                    'descricao': transacao_banco.descricao_ofx,
                    'valor': str(valor_ajustado),  # Retorna como string para garantir precisão no JS
                    'ja_conciliado': ja_conciliado,
                })

        # --- FLUXO DE AUDITORIA (D+1) INTELIGENTE COM LIMITE DE DATA ---

        # Query de IDs que já foram conciliados
        ids_ja_conciliados = ConciliacaoBancaria.objects.values_list('conta_pagar_id', flat=True)

        # Filtro base de contas que ainda não foram conciliadas no banco de destino
        contas_filtro = ContaPagar.objects.filter(
            banco=banco_destino,
            status__icontains="Pago",
        ).exclude(
            id__in=ids_ja_conciliados,
        )

        # Se o extrato continha transações com datas válidas, aplicamos a janela de tolerância de data
        if datas_transacoes:
            menor_data_ofx = min(datas_transacoes)
            maior_data_ofx = max(datas_transacoes)

            # Define uma margem de segurança de 7 dias para antes da menor transação e depois da maior.
            data_inicio_limite = menor_data_ofx - timedelta(days=7)
            data_fim_limite = maior_data_ofx + timedelta(days=7)

            # Filtra o vencimento da conta dentro do intervalo correspondente ao período do OFX
            contas_filtro = contas_filtro.filter(
                vencimento__range=(data_inicio_limite, data_fim_limite)
            )

        # Executa a busca otimizada trazendo apenas as colunas essenciais como dicionário
        contas_sistema = contas_filtro.order_by('vencimento').values('id', 'fornecedor', 'valor', 'vencimento')

        # Monta a estrutura de retorno para o frontend
        contas_pendentes = [
            {
                'id': conta['id'],
                'fornecedor': conta['fornecedor'],
                'valor': str(conta['valor']),  # Enviado como string para preservar os centavos
                'data_pagamento': conta['vencimento'].strftime('%d/%m/%Y') if conta['vencimento'] else '-',
            }
            for conta in contas_sistema
        ]

        return JsonResponse({
            'success': True,
            'banco': banco_destino,
            'transacoes_ofx': transacoes_ofx,
            'contas_pendentes': contas_pendentes,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f"Erro ao processar OFX: {str(e)}"})


def gravar_conciliacao_lote(request):
    if request.method == "POST":
        try:
            dados = json.loads(request.body)
            vinculos = dados.get("vinculos", [])
            banco_pago = dados.get("banco", "Definir")

            for item in vinculos:
                c_id = int(item['conta_id'])
                e_id = int(item['extrato_id'])

                conta = ContaPagar.objects.get(id=c_id)
                extrato = TransacaoExtrato.objects.get(id=e_id)

                ConciliacaoBancaria.objects.create(
                    conta_pagar_id=conta.id,
                    transacao_extrato_id=extrato.id,
                    data_conciliacao=extrato.data_banco,
                    banco_pago=banco_pago,
                    valor_original_conta=conta.valor,
                    valor_pago_extrato=extrato.valor_extrato,
                )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Erro na gravação: {str(e)}"})

    return JsonResponse({"success": False, "error": "Método inválido."})


def form(request):
    if request.method == "POST":
        fornecedor = request.POST.get("fornecedor")
        banco_nome = request.POST.get("banco")
        categoria_nome = request.POST.get("categoria")
        parcelas = request.POST.get("parcela")
        valor_str = request.POST.get("valor")
        vencimento_data = request.POST.get("vencimento_manual")

        vencimento_base = datetime.strptime(vencimento_data, "%Y-%m-%d").date()

        if int(parcelas) == 1:
            ContaPagar.objects.create(
                fornecedor=fornecedor,
                banco=banco_nome,
                categoria=categoria_nome,
                parcela=f'0{parcelas}/0{parcelas}',
                valor=parse_valor_brl(valor_str),
                vencimento=vencimento_base,
                status="Pendente",
            )
            return redirect("homes")

        valor_parcela = parse_valor_brl(valor_str)

        for i in range(1, int(parcelas) + 1):
            vencimento_parcela = vencimento_base + relativedelta(months=i - 1)
            ContaPagar.objects.create(
                fornecedor=fornecedor,
                banco=banco_nome,
                categoria=categoria_nome,
                parcela=f'0{i}/0{parcelas}',
                valor=valor_parcela,
                vencimento=vencimento_parcela,
                status="Pendente",
            )
        return redirect("homes")

    fornecedores_reais = Fornecedor.objects.values_list('razao_social', flat=True).distinct().order_by('razao_social')
    bancos_reais = BancoSaldo.objects.values_list('nome', flat=True).distinct().order_by('nome')
    categorias_reais = Categoria.objects.all().order_by('grupo')

    opcoes_parcelas = [f'{i}' for i in range(1, 25)]

    contexto = {
        "fornecedores": list(fornecedores_reais),
        "bancos": list(bancos_reais),
        "categorias": categorias_reais,
        "opcoes_parcelas": opcoes_parcelas,
    }
    return render(request, "form.html", contexto)


def conciliar(request, identi):
    # Verifica se a conta já possui uma conciliação ativa para inverter o status
    if ConciliacaoBancaria.objects.filter(conta_pagar_id=identi).exists():
        ConciliacaoBancaria.objects.filter(conta_pagar_id=identi).delete()
    else:
        conta = get_object_or_404(ContaPagar, id=identi)

        ConciliacaoBancaria.objects.create(
            conta_pagar_id=conta.id,
            transacao_extrato_id=0,  # 0 indica ajuste manual sem arquivo OFX
            data_conciliacao=date.today(),
            banco_pago=conta.banco,
        )

    url_anterior = request.META.get("HTTP_REFERER")
    return redirect(url_anterior) if url_anterior else redirect("homes")


def atualizar_status_json(request, identi):
    if request.method == 'POST':
        conta = get_object_or_404(ContaPagar, id=identi)
        novo_status = request.POST.get('status')
        nova_data = request.POST.get('ultimo_pagamento')
        novo_juros = request.POST.get('juros')
        nova_conta_origem = request.POST.get('conta_origem')

        if novo_status:
            conta.status = novo_status
        conta.ultimo_pagamento = nova_data if nova_data else None
        if novo_juros:
            conta.juros = novo_juros
        if nova_conta_origem:
            conta.banco_pago = nova_conta_origem

        conta.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False}, status=400)


def provisao_periodo(request):
    hoje = timezone.localdate()
    futuro_padrao = hoje + timedelta(days=30)

    data_inicio_str = request.GET.get("data_inicio")
    data_fim_str = request.GET.get("data_fim")

    data_inicio = hoje
    data_fim = futuro_padrao

    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    contas_periodo = ContaPagar.objects.filter(
        vencimento__range=(data_inicio, data_fim)
    ).exclude(status__icontains="Pago").order_by("vencimento")

    soma_total = contas_periodo.aggregate(Sum("valor"))["valor__sum"] or 0.00
    total_registros = contas_periodo.count()
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')

    # Listas usadas pra popular os <select> do modal de editar registro
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
    categorias = Categoria.objects.all().order_by('nome')

    context = {
        "contas": contas_periodo,
        "total_valor": soma_total,
        "total_registros": total_registros,
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),
        "bancos_disponiveis": bancos_disponiveis,
        "fornecedores": fornecedores,
        "categorias": categorias,
        "bancos": bancos_disponiveis,
    }
    return render(request, "provisao.html", context)


def cadastrar_fornecedor(request):
    if request.method == 'POST':
        razao_social = request.POST.get('razao_social')
        nome_fantasia = request.POST.get('nome_fantasia')
        cnpj = request.POST.get('cnpj')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        logradouro = request.POST.get('logradouro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')

        if not razao_social or not cnpj:
            messages.error(request, "Razão Social e CNPJ são obrigatórios.")
            return render(request, 'cadastrar_fornecedor.html', {'dados': request.POST})

        if Fornecedor.objects.filter(cnpj=cnpj).exists():
            messages.error(request, "Este CNPJ já está cadastrado.")
            return render(request, 'cadastrar_fornecedor.html', {'dados': request.POST})

        try:
            Fornecedor.objects.create(
                razao_social=razao_social, nome_fantasia=nome_fantasia, cnpj=cnpj,
                email=email, telefone=telefone, logradouro=logradouro, cidade=cidade, estado=estado,
            )
            messages.success(request, f"Fornecedor '{nome_fantasia or razao_social}' cadastrado com sucesso!")
            return redirect('homes')
        except Exception as e:
            messages.error(request, f"Erro ao cadastrar fornecedor: {e}")

    return render(request, 'cadastrar_fornecedor.html')


def saldo(request):
    return render(request, "saldo.html")


def dashboard_leve(request):
    hoje = date.today()
    ids_conciliados = ConciliacaoBancaria.objects.values_list('conta_pagar_id', flat=True).distinct()

    metricas = ContaPagar.objects.aggregate(
        total_pagos=Count('id', filter=Q(status="Pago")),
        volume_atrasado=Sum('valor', filter=Q(status="Pendente", vencimento__lt=hoje)),
    )

    total_juros = sum(c.juros for c in ConciliacaoBancaria.objects.all() if hasattr(c, 'juros'))
    volume_atrasado = metricas['volume_atrasado'] or 0
    total_pagos = metricas['total_pagos'] or 1

    pagos_conciliados_count = len(ids_conciliados)
    taxa_conciliacao = (pagos_conciliados_count / total_pagos) * 100

    dados_grafico = ConciliacaoBancaria.objects.all()
    categoria_dict = {}
    for c in dados_grafico:
        juros_val = float(getattr(c, 'juros', 0) or 0)
        if juros_val > 0:
            conta = ContaPagar.objects.filter(id=c.conta_pagar_id).first()
            cat_nome = conta.categoria if conta else "Sem Categoria"
            categoria_dict[cat_nome] = categoria_dict.get(cat_nome, 0) + juros_val

    categorias = list(categoria_dict.keys())
    juros_valores = list(categoria_dict.values())

    pendentes_conciliacao = ContaPagar.objects.filter(status="Pago").exclude(id__in=ids_conciliados)[:5]

    context = {
        'total_juros': total_juros,
        'taxa_conciliacao': round(taxa_conciliacao, 1),
        'volume_atrasado': volume_atrasado,
        'categorias_json': json.dumps(categorias),
        'juros_json': json.dumps(juros_valores),
        'pendentes_conciliacao': pendentes_conciliacao,
    }
    return render(request, 'dashboard.html', context)


def salvar_conciliacao_lote(request):
    if request.method == "POST":
        try:
            dados = json.loads(request.body)
            vinculos = dados.get("vinculos", [])

            if not vinculos:
                return JsonResponse({'success': False, 'error': 'Nenhum vínculo selecionado.'})

            agora = timezone.now()

            for item in vinculos:
                conta_id = item.get("conta_id")
                extrato_id = item.get("extrato_id")

                ConciliacaoBancaria.objects.get_or_create(
                    conta_pagar_id=conta_id,
                    defaults={
                        'transacao_extrato_id': extrato_id,
                        'data_conciliacao': agora,
                    }
                )
                # Se no seu fluxo precisar marcar a conta como liquidada/auditada:
                # ContaPagar.objects.filter(id=conta_id).update(status="Pago e Conciliado")

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Erro interno ao salvar lote: {str(e)}"})

    return JsonResponse({'success': False, 'error': 'Método não permitido.'})

@require_POST
def importar_xlsx(request):
    if 'arquivo_xlsx' not in request.FILES:
        return JsonResponse({'sucesso': False, 'erro': 'Nenhum arquivo enviado.'}, status=400)

    excel_file = request.FILES['arquivo_xlsx']

    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        sheet = wb.active
    except Exception as e:
        return JsonResponse({'sucesso': False, 'erro': f'Erro ao ler o arquivo Excel: {str(e)}'}, status=400)

    rows = list(sheet.iter_rows(values_only=True))
    if not rows or len(rows) < 2:
        return JsonResponse({'sucesso': False, 'erro': 'A planilha está vazia ou não possui dados suficientes.'}, status=400)

    # 1. Mapeamento dos Cabeçalhos (Linha 1)
    headers = [str(cell).strip().lower() if cell is not None else '' for cell in rows[0]]

    def get_col_index(possible_names):
        for name in possible_names:
            if name in headers:
                return headers.index(name)
        return None

    idx_fornecedor = get_col_index(['fornecedor', 'razão social', 'razao social', 'razao_social'])
    idx_banco      = get_col_index(['banco', 'conta', 'banco/saldo', 'bancosaldo'])
    idx_categoria  = get_col_index(['categoria', 'classificação', 'classificacao'])
    idx_valor      = get_col_index(['valor', 'valor (r$)', 'valorpago'])
    idx_vencimento = get_col_index(['vencimento', 'data vencimento', 'dt_vencimento'])

    if idx_fornecedor is None or idx_banco is None or idx_categoria is None or idx_vencimento is None:
        return JsonResponse({
            'sucesso': False, 
            'erro': 'Cabeçalhos não identificados. Certifique-se de que a planilha possui colunas para Fornecedor, Banco, Categoria e Vencimento.'
        }, status=400)

    # 2. Caching para Alta Performance (Usando razao_social no Fornecedor)
    fornecedores_cache = {
        f.razao_social.strip().lower(): f 
        for f in Fornecedor.objects.all() if getattr(f, 'razao_social', None)
    }
    
    bancos_cache = {
        b.nome.strip().lower(): b 
        for b in BancoSaldo.objects.all() if getattr(b, 'nome', None)
    }
    
    categorias_cache = {
        c.nome.strip().lower(): c 
        for c in Categoria.objects.all() if getattr(c, 'nome', None)
    }

    novas_contas = []
    erros = []
    importados_count = 0
    duplicados_count = 0

    # 3. Leitura e Validação Linha por Linha
    for index, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue

        raw_fornecedor = str(row[idx_fornecedor]).strip() if row[idx_fornecedor] is not None else ''
        raw_banco      = str(row[idx_banco]).strip() if row[idx_banco] is not None else ''
        raw_categoria  = str(row[idx_categoria]).strip() if row[idx_categoria] is not None else ''
        
        val_valor      = row[idx_valor] if idx_valor is not None else 0
        raw_vencimento = row[idx_vencimento] if idx_vencimento is not None else None
        
        # Converte e valida o Vencimento
        val_vencimento = normalizar_data(raw_vencimento)

        # Busca nos Caches
        obj_fornecedor = fornecedores_cache.get(raw_fornecedor.lower())
        obj_banco      = bancos_cache.get(raw_banco.lower())
        obj_categoria  = categorias_cache.get(raw_categoria.lower())

        # Validação de Relações e Campos Obrigatórios
        faltantes = []
        if not obj_fornecedor:
            faltantes.append(f"Fornecedor '{raw_fornecedor}'")
        if not obj_banco:
            faltantes.append(f"Banco '{raw_banco}'")
        if not obj_categoria:
            faltantes.append(f"Categoria '{raw_categoria}'")
        if not val_vencimento:
            faltantes.append("Vencimento inválido/ausente")

        if faltantes:
            erros.append(f"Linha {index}: Problema em -> {', '.join(faltantes)}.")
            continue

        # Checagem de Duplicidade
        ja_existe = ContaPagar.objects.filter(
            fornecedor=obj_fornecedor,
            banco=obj_banco,
            categoria=obj_categoria,
            valor=val_valor,
            vencimento=val_vencimento
        ).exists()

        if ja_existe:
            duplicados_count += 1
            continue

        # Criação do Objeto em Memória
        novas_contas.append(
            ContaPagar(
                fornecedor=obj_fornecedor,
                banco=obj_banco,
                categoria=obj_categoria,
                valor=val_valor,
                vencimento=val_vencimento
            )
        )
        importados_count += 1

    # 4. Inserção em Lote no Banco de Dados
    if novas_contas:
        with transaction.atomic():
            ContaPagar.objects.bulk_create(novas_contas)

    return JsonResponse({
        'sucesso': True,
        'importados': importados_count,
        'duplicados': duplicados_count,
        'erros': erros
    })

def baixar_planilha_padrao(request):
    workbook = Workbook()
    aba = workbook.active
    aba.title = "Modelo"

    cabecalho = ["Vencimento", "Fornecedor", "Categoria", "Banco", "Parcela", "Valor", "Observação", "Status"]
    aba.append(cabecalho)
    aba.append(["12/12/2026", "Seu Fornecedor", "Energia", "Nome Banco", "1/1", 150.00, "Sua Observação", "Pendente"])

    for coluna in aba.columns:
        maior_largura = max(len(str(celula.value)) for celula in coluna)
        aba.column_dimensions[coluna[0].column_letter].width = maior_largura + 4

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="modelo_contas_a_pagar.xlsx"'
    workbook.save(response)
    return response


def atualizar_registro(request):
    # Volta pra página de onde o form foi enviado (home, provisao, etc.),
    # em vez de sempre mandar pra "homes" -- mesmo padrão já usado em
    # conciliar().
    url_anterior = request.META.get("HTTP_REFERER")
    destino = url_anterior if url_anterior else redirect('homes').url

    if request.method != "POST":
        return redirect(destino)

    registro_id = request.POST.get('id')
    registro = get_object_or_404(ContaPagar, id=registro_id)

    campos_alterados = []

    vencimento_str = request.POST.get('vencimento', '').strip()
    if vencimento_str:
        try:
            nova_vencimento = datetime.strptime(vencimento_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Data de vencimento inválida.")
            return redirect(destino)
        if nova_vencimento != registro.vencimento:
            registro.vencimento = nova_vencimento
            campos_alterados.append('vencimento')

    novo_fornecedor = request.POST.get('fornecedor', '').strip()
    if novo_fornecedor and novo_fornecedor != registro.fornecedor:
        registro.fornecedor = novo_fornecedor
        campos_alterados.append('fornecedor')

    nova_categoria = request.POST.get('categoria', '').strip()
    if nova_categoria != (registro.categoria or ''):
        registro.categoria = nova_categoria or None
        campos_alterados.append('categoria')

    novo_banco = request.POST.get('banco', '').strip()
    if novo_banco and novo_banco != registro.banco:
        registro.banco = novo_banco
        campos_alterados.append('banco')

    nova_parcela = request.POST.get('parcela', '').strip()
    if nova_parcela and nova_parcela != registro.parcela:
        registro.parcela = nova_parcela
        campos_alterados.append('parcela')

    nova_observacao = request.POST.get('observacao', '').strip()
    if nova_observacao != (registro.observacao or ''):
        registro.observacao = nova_observacao
        campos_alterados.append('observacao')

    valor_str = request.POST.get('valor', '').strip()
    if valor_str:
        try:
            novo_valor = parse_valor_brl(valor_str)
        except InvalidOperation:
            messages.error(request, f"Valor inválido: “{valor_str}”.")
            return redirect(destino)
        if novo_valor != registro.valor:
            registro.valor = novo_valor
            campos_alterados.append('valor')

    if campos_alterados:
        registro.save(update_fields=campos_alterados)
        messages.success(request, "Registro atualizado com sucesso.")
    else:
        messages.info(request, "Nenhuma alteração foi detectada.")

    return redirect(destino)