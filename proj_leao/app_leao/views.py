from django.shortcuts import render, redirect, get_object_or_404
from app_leao.models import ContaPagar, Fornecedor, BancoSaldo # 📦 IMPORTADO O NOVO MODEL DE BANCOS
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt # Caso precise para o Fetch
from django.contrib.auth import authenticate, login, logout
import json
import io
from datetime import date
from ofxtools.Parser import OFXTree


def tela_login(request):
    # Se o usuário já estiver logado e tentar acessar o login, manda direto para a home
    if request.user.is_authenticated:
        return redirect('homes')
    return render(request, 'login.html')

def login_usuario(request):
    if request.method == "POST":
        usuario_post = request.POST.get("username")
        senha_post = request.POST.get("password")
        
        # O Django valida a senha criptografada de forma nativa aqui:
        user = authenticate(request, username=usuario_post, password=senha_post)
        
        if user is not None:
            login(request, user) # Inicia a sessão salva no navegador
            return redirect('homes') # Direciona para a sua página inicial
        else:
            messages.error(request, "Usuário ou senha incorretos. Tente novamente.")
            return redirect('tela_login')
            
    return redirect('tela_login')

def logout_usuario(request):
    logout(request) # Destrói a sessão do navegador
    return redirect('tela_login')

def home(request):
    # ==========================================================================
    # 🔄 ATUALIZAÇÃO AUTOMÁTICA DE STATUS (CONTAS ATRASADAS)
    # ==========================================================================
    data_atual = timezone.localdate()

    # Filtra contas vencidas (vencimento < hoje) que NÃO estão com status 'Pago'
    # e atualiza todas de uma vez só no banco com o status "Atrasado"
    ContaPagar.objects.filter(
        vencimento__lt=data_atual,
    ).exclude(
        status__icontains="Pago"  # Ignora maiúsculas/minúsculas caso venha diferente do Excel
    ).update(status="Atrasado")
    # ==========================================================================

    # 1. Busca todos os registros atualizados do banco
    queryset = ContaPagar.objects.all()

    # 2. Captura TODOS os filtros que o usuário digitou na barra superior (via método GET)
    filtro_conciliacao = request.GET.get("conciliacao")
    filtro_data = request.GET.get("data")
    filtro_fornecedor = request.GET.get("fornecedor")
    filtro_categoria = request.GET.get("categoria")
    filtro_banco = request.GET.get("banco")
    filtro_parcela = request.GET.get("parcela")
    filtro_valor = request.GET.get("valor")
    filtro_observacao = request.GET.get("observacao")
    filtro_status = request.GET.get("status")

    # 3. Aplica os filtros no ORM caso tenham sido preenchidos

    # Filtro: Conciliação
    if filtro_conciliacao and filtro_conciliacao.strip():
        queryset = queryset.filter(conciliado__icontains=filtro_conciliacao)

    # Filtro: Fornecedor
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)

    # Filtro: Categoria
    if filtro_categoria and filtro_categoria.strip():
        queryset = queryset.filter(categoria__icontains=filtro_categoria)

    # Filtro: Banco
    if filtro_banco and filtro_banco.strip():
        queryset = queryset.filter(banco__icontains=filtro_banco)

    # Filtro: Parcela
    if filtro_parcela and filtro_parcela.strip():
        queryset = queryset.filter(parcela__icontains=filtro_parcela)

    # Filtro: Valor
    if filtro_valor and filtro_valor.strip():
        queryset = queryset.filter(valor__icontains=filtro_valor)

    # Filtro: Observação
    if filtro_observacao and filtro_observacao.strip():
        queryset = queryset.filter(observacao__icontains=filtro_observacao)

    # Filtro: Status
    if filtro_status and filtro_status.strip():
        queryset = queryset.filter(status__icontains=filtro_status)

    # Filtro Especial de Data: Converte DD/MM/AAAA para AAAA-MM-DD
    if filtro_data and filtro_data.strip():
        try:
            data_objeto = datetime.strptime(filtro_data.strip(), "%d/%m/%Y")
            filtro_data_formatada = data_objeto.strftime("%Y-%m-%d")

            queryset = queryset.filter(vencimento=filtro_data_formatada)
        except ValueError:
            messages.error(request, "Formato de data inválido. Use DD/MM/AAAA.")

    # 4. Configura a Paginação para exibir estritamente 15 linhas por página
    paginator = Paginator(queryset, 15)

    # Captura o número da página atual na URL
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 🔄 BUSCA OS BANCOS CADASTRADOS DINAMICAMENTE PARA O MODAL DE PAGAMENTO DA HOME
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')

    # 5. Envia o 'page_obj' e 'bancos_disponiveis' para o HTML
    context = {
        "page_obj": page_obj,
        "bancos_disponiveis": bancos_disponiveis
    }

    return render(request, "home.html", context)

def processar_ofx_ajax(request):
    if request.method == "POST" and request.FILES.get("arquivo_ofx"):
        banco_destino = request.POST.get("banco_destino")
        arquivo_ofx = request.FILES.get("arquivo_ofx")
        
        try:
            # 1. Lê o arquivo vindo do upload diretamente como texto (string)
            conteudo = arquivo_ofx.read().decode("utf-8", errors="ignore")
            
            # 2. Aplica a sua correção cirúrgica para datas zeradas que quebram o parser
            conteudo_corrigido = conteudo.replace("00000000000000", "20000101120000")
            conteudo_corrigido = conteudo_corrigido.replace("00000000", "20000101")
            
            # 3. Transforma o texto corrigido de volta em bytes na memória usando BytesIO
            conteudo_em_bytes = conteudo_corrigido.encode("utf-8")
            arquivo_virtual_binario = io.BytesIO(conteudo_em_bytes)
            
            # 4. Faz o parse do arquivo limpo na memória
            parser = OFXTree()
            parser.parse(arquivo_virtual_binario) 
            obj = parser.convert()
            
            # 5. Acessa o primeiro extrato de forma direta (igual à sua função inspiradora)
            extrato = obj.statements[0]
            transacoes = extrato.banktranlist
            
            transacoes_ofx = []
            
            # 6. Percorre as transações e extrai os campos no padrão que o JS espera
            for tx in transacoes:
                # O valor no OFX pode vir negativo para saídas, usamos abs() para o cruzamento com o sistema
                valor_ajustado = float(abs(tx.trnamt))
                
                # Converte a data para o formato brasileiro DD/MM/AAAA
                data_formatada = tx.dtposted.strftime('%d/%m/%Y') if tx.dtposted else '-'
                
                transacoes_ofx.append({
                    'data': data_formatada,
                    'descricao': tx.memo if tx.memo else (tx.name or "Transação sem descrição"),
                    'valor': valor_ajustado
                })
            
            # ==================================================================
            # 🏦 BUSCA NO BANCO DE DADOS (CONTAS DO SISTEMA)
            # ==================================================================
            # Busca as contas Pagas pelo banco selecionado no Modal 1 e que NÃO foram conciliadas
            contas_sistema = ContaPagar.objects.filter(
            status__icontains="Pago",
            conciliado="Não"
        ).order_by('-ultimo_pagamento')
            
            contas_pendentes = []

            for conta in contas_sistema:
                contas_pendentes.append({
                    'id': conta.id,
                    'fornecedor': conta.fornecedor,
                    'valor': float(conta.valor),
                    'data_pagamento': conta.ultimo_pagamento.strftime('%d/%m/%Y') if conta.ultimo_pagamento else '-'
                })
                
            # Retorna o JSON de sucesso completo para o frontend
            return JsonResponse({
                'success': True,
                'banco': banco_destino,
                'transacoes_ofx': transacoes_ofx,
                'contas_pendentes': contas_pendentes
            })
            
        except Exception as e:
            # Captura o erro amigavelmente e joga no alert do cliente
            return JsonResponse({'success': False, 'error': f"Erro ao processar OFX: {str(e)}"})
            
    return JsonResponse({'success': False, 'error': 'Método inválido ou arquivo não enviado.'})

def form(request):
    if request.method == 'POST':
        # Captura os dados do formulário usando o atributo 'name' do HTML
        vencimento = request.POST.get('vencimento')
        valor = request.POST.get('valor')
        fornecedor = request.POST.get('fornecedor')
        categoria = request.POST.get('categoria')
        banco = request.POST.get('banco')
        parcela = request.POST.get('parcela')
        observacao = request.POST.get('observacao')

        # Cria e salva o registro no banco de dados
        try:
            ContaPagar.objects.create(
                vencimento=vencimento, 
                valor=valor,
                fornecedor=fornecedor,
                categoria=categoria,
                banco=banco,
                parcela=parcela,
                observacao=observacao
            )
            messages.success(request, "Lançamento cadastrado com sucesso!")

            return redirect('homes') 
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {e}")

    # 🔄 SE FOR GET, CARREGA OS BANCOS CASO SEU FORMULÁRIO DE CADASTRO TAMBÉM PRECISE DELES
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')
    context = {"bancos_disponiveis": bancos_disponiveis}

    return render(request, 'form.html', context) 


def aba_conciliacao(request):
    # ==========================================================================
    # 🏦 RECEBIMENTO E VALIDAÇÃO DO OFX (VIA MODAL)
    # ==========================================================================
    if request.method == "POST":
        banco_destino = request.POST.get("banco_destino")
        arquivo_ofx = request.FILES.get("arquivo_ofx")
        
        if banco_destino and arquivo_ofx:
            try:
                # 🛠️ POST PRONTO: Aqui você vai injetar a lógica de leitura do OFX
                # usando as variáveis 'banco_destino' e 'arquivo_ofx'
                
                messages.success(request, f"Arquivo enviado com sucesso para validação no banco: {banco_destino}!")
            except Exception as e:
                messages.error(request, f"Erro ao processar o arquivo: {e}")
                
            return redirect('aba_conciliacao')

    # ==========================================================================
    # 📊 LEITURA E FILTROS DA TELA (SEU CÓDIGO ORIGINAL)
    # ==========================================================================
    # 1. Busca TODAS as contas que já foram pagas (independente de estarem conciliadas ou não)
    queryset = ContaPagar.objects.filter(status__icontains="Pago").order_by("-ultimo_pagamento")

    # Filtro rápido de busca por fornecedor
    filtro_fornecedor = request.GET.get("fornecedor")
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)

    # 2. CÁLCULO DOS TOTAIS DO PAINEL DE AUDITORIA
    total_conciliado = queryset.filter(conciliado="Sim").aggregate(
        total=Sum('valor') + Sum('juros')
    )['total'] or 0.00

    total_pendente = queryset.exclude(conciliado="Sim").aggregate(
        total=Sum('valor') + Sum('juros')
    )['total'] or 0.00

    # 3. PAGINAÇÃO
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # 🔄 4. CARREGA OS BANCOS CADASTRADOS PARA ALIMENTAR O SEU MODAL OFX
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')

    context = {
        'page_obj': page_obj,
        'total_conciliado': total_conciliado,
        'total_pendente': total_pendente,
        'bancos_disponiveis': bancos_disponiveis, # << INJETADO NO CONTEXTO
    }
    return render(request, 'conciliacao.html', context)

def conciliar(request, identi):
    print(f"ID recebido para conciliação: {identi}")

    # Busca a linha no SQLite
    conta = get_object_or_404(ContaPagar, id=identi)

    # Altera o status baseado no que está atualmente no banco
    if conta.conciliado == "Sim":
        conta.conciliado = "Não"
    else:
        conta.conciliado = "Sim"

    conta.save()

    # Captura a URL exata (com todas as buscas GET) de onde o botão foi clicado
    url_anterior = request.META.get("HTTP_REFERER")

    if url_anterior:
        return redirect(url_anterior)  

    return redirect("homes")


def atualizar_status_json(request, identi):
    if request.method == 'POST':
        conta = get_object_or_404(ContaPagar, id=identi)
        
        # 1. Coleta os dados do POST do formulário do Modal
        novo_status = request.POST.get('status')
        nova_data = request.POST.get('ultimo_pagamento')
        novo_juros = request.POST.get('juros')
        nova_conta_origem = request.POST.get('conta_origem') # 🔄 RECOLHE A CONTA DO FORMULÁRIO DO MODAL
        
        # 2. Aplica as validações e atualiza o objeto
        if novo_status:
            conta.status = novo_status
            
        if nova_data:  
            conta.ultimo_pagamento = nova_data
        else:          
            conta.ultimo_pagamento = None
            
        if novo_juros:
            conta.juros = novo_juros
            
        if nova_conta_origem: # 🔄 INJETA A CONTA SELECIONADA COMO TEXTO COMUM NO MODEL
            conta.conta_origem = nova_conta_origem
            
        # 3. Salva de vez no SQLite
        conta.save()
        return JsonResponse({'success': True})
            
    return JsonResponse({'success': False}, status=400)


def provisao_periodo(request):
    # 1. Configura as datas padrão (Hoje até daqui a 30 dias) se o usuário não filtrar
    hoje = timezone.localdate()
    futuro_padrao = hoje + timedelta(days=30)

    # Captura as datas vindas do formulário de período
    data_inicio_str = request.GET.get("data_inicio")
    data_fim_str = request.GET.get("data_fim")

    # Tratamento e conversão das datas informadas
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

    # 2. Filtra as contas que vencem dentro do período e que NÃO estão pagas
    contas_periodo = (
        ContaPagar.objects.filter(vencimento__range=(data_inicio, data_fim))
        .exclude(status__icontains="Pago")
        .order_by("vencimento")  
    )

    # 3. MÁGICA DO ORM: Soma todos os valores do campo 'valor' das contas filtradas
    soma_total = contas_periodo.aggregate(Sum("valor"))["valor__sum"] or 0.00

    # Contagem de quantos boletos existem no período
    total_registros = contas_periodo.count()

    # 🔄 BUSCA OS BANCOS CADASTRADOS DINAMICAMENTE PARA O MODAL DE PAGAMENTO DA PROVISÃO
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')

    context = {
        "contas": contas_periodo,
        "total_valor": soma_total,
        "total_registros": total_registros,
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),
        "bancos_disponiveis": bancos_disponiveis # 🔄 ENVIADO PARA O TEMPLATE DA PROVISÃO
    }

    return render(request, "provisao.html", context)


def cadastrar_fornecedor(request):
    if request.method == 'POST':
        # Coleta os dados do formulário
        razao_social = request.POST.get('razao_social')
        nome_fantasia = request.POST.get('nome_fantasia')
        cnpj = request.POST.get('cnpj')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        logradouro = request.POST.get('logradouro')
        cidade = request.POST.get('cidade')
        estado = request.POST.get('estado')

        # Validação simples
        if not razao_social or not cnpj:
            messages.error(request, "Razão Social e CNPJ são obrigatórios.")
            return render(request, 'cadastrar_fornecedor.html', {'dados': request.POST})

        if Fornecedor.objects.filter(cnpj=cnpj).exists():
            messages.error(request, "Este CNPJ já está cadastrado.")
            return render(request, 'cadastrar_fornecedor.html', {'dados': request.POST})

        try:
            # Cria e salva o fornecedor
            Fornecedor.objects.create(
                razao_social=razao_social,
                nome_fantasia=nome_fantasia,
                cnpj=cnpj,
                email=email,
                telefone=telefone,
                logradouro=logradouro,
                cidade=cidade,
                estado=estado
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
    
    # 1. Agregação de alta performance para os Cards Estratégicos
    metricas = ContaPagar.objects.aggregate(
        # Card 1: Juros absolutos jogados no lixo (Vazamento de Caixa)
        total_juros=Sum('juros', filter=Q(status="Pago")),
        
        # Card 2: Acurácia de Conciliação (Pagos e Conciliados / Total de Pagos)
        total_pagos=Count('id', filter=Q(status="Pago")),
        pagos_conciliados=Count('id', filter=Q(status="Pago", conciliado="Sim")),
        
        # Card 3: Volume Crítico (Contas pendentes que já passaram do vencimento)
        volume_atrasado=Sum('valor', filter=Q(status="Pendente", vencimento__lt=hoje))
    )
    
    # Tratamento de valores nulos e cálculo de porcentagem
    total_juros = metricas['total_juros'] or 0
    volume_atrasado = metricas['volume_atrasado'] or 0
    
    total_pagos = metricas['total_pagos'] or 1
    taxa_conciliacao = (metricas['pagos_conciliados'] / total_pagos) * 100

    # 2. Dados do Gráfico: Desperdício de juros acumulado por Categoria
    dados_grafico = ContaPagar.objects.filter(status="Pago", juros__gt=0) \
        .values('categoria') \
        .annotate(total_juros=Sum('juros')) \
        .order_by('-total_juros')

    categorias = [item['categoria'] for item in dados_grafico]
    juros_valores = [float(item['total_juros']) for item in dados_grafico]

    # 3. Lista Operacional: Top 5 maiores contas pagas que ainda NÃO foram conciliadas
    pendentes_conciliacao = ContaPagar.objects.filter(status="Pago", conciliado="Não") \
        .order_by('-valor')[:5]

    context = {
        'total_juros': total_juros,
        'taxa_conciliacao': round(taxa_conciliacao, 1),
        'volume_atrasado': volume_atrasado,
        'categorias_json': json.dumps(categorias),
        'juros_json': json.dumps(juros_valores),
        'pendentes_conciliacao': pendentes_conciliacao,
    }
    
    return render(request, 'dashboard.html', context)