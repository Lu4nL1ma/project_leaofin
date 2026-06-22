from django.shortcuts import render, redirect, get_object_or_404
from app_leao.models import ContaPagar, Fornecedor
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum


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

    # 5. Envia o 'page_obj' para o HTML
    context = {"page_obj": page_obj}

    return render(request, "home.html", context)

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
                vencimento=vencimento, # Ajuste os nomes dos campos de acordo com seu Model
                valor=valor,
                fornecedor=fornecedor,
                categoria=categoria,
                banco=banco,
                parcela=parcela,
                observacao=observacao
            )
            messages.success(request, "Lançamento cadastrado com sucesso!")

            return redirect('homes') # Mude para a sua rota de sucesso
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {e}")

    # Se for GET, apenas renderiza a página do formulário
    return render(request, 'form.html') # Ajuste o caminho do seu HTML


def aba_conciliacao(request):
    # 1. Busca TODAS as contas que já foram pagas (independente de estarem conciliadas ou não)
    queryset = ContaPagar.objects.filter(status__icontains="Pago").order_by("-ultimo_pagamento")

    # Filtro rápido de busca por fornecedor
    filtro_fornecedor = request.GET.get("fornecedor")
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)

    # 2. CÁLCULO DOS TOTAIS DO PAINEL DE AUDITORIA
    # Soma o valor + juros das contas que já estão com conciliado = "Sim"
    total_conciliado = queryset.filter(conciliado="Sim").aggregate(
        total=Sum('valor') + Sum('juros')
    )['total'] or 0.00

    # Soma o valor + juros das contas que estão pagas, mas com conciliado diferente de "Sim"
    total_pendente = queryset.exclude(conciliado="Sim").aggregate(
        total=Sum('valor') + Sum('juros')
    )['total'] or 0.00

    # 3. PAGINAÇÃO
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_conciliado': total_conciliado,
        'total_pendente': total_pendente,
    }
    return render(request, 'conciliacao.html', context)

def conciliar(request, identi):
    # O Django já recebe o ID direto da URL
    print(f"ID recebido para conciliação: {identi}")

    # Busca a linha no SQLite
    conta = get_object_or_404(ContaPagar, id=identi)

    # Altera o status baseado no que está atualmente no banco
    if conta.conciliado == "Sim":
        conta.conciliado = "Não"
    else:
        conta.conciliado = "Sim"

    conta.save()

    # ==========================================================================
    # CORREÇÃO DO PROBLEMA: MANTÉM OS FILTROS DA URL ATIVOS
    # ==========================================================================
    # Captura a URL exata (com todas as buscas GET) de onde o botão foi clicado
    url_anterior = request.META.get("HTTP_REFERER")

    if url_anterior:
        return redirect(url_anterior)  # Recarrega a página mantendo a busca ativa

    # Fallback de segurança (se o navegador não enviar o referer, usa a rota limpa)
    return redirect("homes")

def atualizar_status_json(request, identi):
    if request.method == 'POST':
        conta = get_object_or_404(ContaPagar, id=identi)
        
        # 1. Coleta os dados do POST do formulário do Modal
        novo_status = request.POST.get('status')
        nova_data = request.POST.get('ultimo_pagamento')
        novo_juros = request.POST.get('juros')
        
        # 2. Aplica as validações e atualiza o objeto
        if novo_status:
            conta.status = novo_status
            
        if nova_data:  # Se houver data preenchida
            conta.ultimo_pagamento = nova_data
        else:          # Se estiver vazia, salva como nulo (conforme seu model)
            conta.ultimo_pagamento = None
            
        if novo_juros:
            conta.juros = novo_juros
            
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
    # (Buscamos o que 'vai ser pago', logo ignoramos o status 'Pago')
# ... código anterior ...
    contas_periodo = (
        ContaPagar.objects.filter(vencimento__range=(data_inicio, data_fim))
        .exclude(status__icontains="Pago")
        .order_by("vencimento")  #  Corrigido! Ordena do mais próximo ao mais distante
    )

    # 3. MÁGICA DO ORM: Soma todos os valores do campo 'valor' das contas filtradas
    # O resultado vem num dicionário tipo: {'valor__sum': 1500.50}
    soma_total = contas_periodo.aggregate(Sum("valor"))["valor__sum"] or 0.00

    # Contagem de quantos boletos existem no período
    total_registros = contas_periodo.count()

    context = {
        "contas": contas_periodo,
        "total_valor": soma_total,
        "total_registros": total_registros,
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),
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

        # Validação simples (exemplo: CNPJ obrigatório e único)
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
            return redirect('homes') # Altere para a rota desejada após o sucesso
            
        except Exception as e:
            messages.error(request, f"Erro ao cadastrar fornecedor: {e}")

    return render(request, 'cadastrar_fornecedor.html')

def saldo(request):
    return render(request, "saldo.html")