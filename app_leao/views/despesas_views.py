# app_leao/views/despesas_views.py

from datetime import datetime, timedelta
from decimal import InvalidOperation
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from app_leao.models import ContaPagar, BancoSaldo, Fornecedor, Categoria
from app_leao.utils.formatters import parse_valor


def despesas(request):
    """Lista as despesas cadastradas com filtros dinâmicos e paginação."""
    data_atual = timezone.localdate()

    # Atualização automática de contas atrasadas no banco de dados[cite: 1]
    ContaPagar.objects.filter(vencimento__lt=data_atual).exclude(status__icontains="Pago").update(status="Atrasado")

    queryset = ContaPagar.objects.all()

    # Captura de Filtros Dinâmicos[cite: 1]
    filtro_conciliacao = request.GET.get("conciliacao")
    filtro_data = request.GET.get("data")
    filtro_fornecedor = request.GET.get("fornecedor")
    filtro_categoria = request.GET.get("categoria")
    filtro_banco = request.GET.get("banco")
    filtro_parcela = request.GET.get("parcela")
    filtro_valor = request.GET.get("valor")
    filtro_observacao = request.GET.get("observacao")
    filtro_status = request.GET.get("status")
    filtro_nota_fiscal = request.GET.get("nota_fiscal")
    filtro_linha_digitavel = request.GET.get("linha_digitavel")

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
    if filtro_nota_fiscal and filtro_nota_fiscal.strip():
        queryset = queryset.filter(nota_fiscal__icontains=filtro_nota_fiscal)
    if filtro_linha_digitavel and filtro_linha_digitavel.strip():
        queryset = queryset.filter(linha_digitavel__icontains=filtro_linha_digitavel)

    if filtro_data and filtro_data.strip():
        try:
            data_objeto = datetime.strptime(filtro_data.strip(), "%d/%m/%Y")
            queryset = queryset.filter(vencimento=data_objeto.strftime("%Y-%m-%d"))
        except ValueError:
            messages.error(request, "Formato de data inválido. Use DD/MM/AAAA.")

    paginator = Paginator(queryset, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')
    fornecedores = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
    categorias = Categoria.objects.all().order_by('nome')

    context = {
        "page_obj": page_obj,
        "bancos_disponiveis": bancos_disponiveis,
        "fornecedores": fornecedores,
        "categorias": categorias,
        "bancos": bancos_disponiveis,
    }
    return render(request, "contas_pagar/despesas.html", context)


def form(request):
    """Criação manual de despesas (à vista ou parceladas)."""
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
                valor=parse_valor(valor_str),
                vencimento=vencimento_base,
                status="Pendente",
            )
            return redirect("home")

        valor_parcela = parse_valor(valor_str)

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
        return redirect("home")

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
    return render(request, "contas_pagar/form.html", contexto)


def provisao_periodo(request):
    """Consulta de despesas previstas para um determinado intervalo de tempo."""
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
    return render(request, "contas_pagar/provisao.html", context)


def atualizar_registro(request):
    """Edição e atualização de campos de uma conta a pagar via modal/form."""
    url_anterior = request.META.get("HTTP_REFERER")
    destino = url_anterior if url_anterior else redirect('home').url

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
            novo_valor = parse_valor(valor_str)
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


def atualizar_status_json(request, identi):
    """Atualização rápida do status da conta via requisição POST / AJAX."""
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


def cadastrar_fornecedor(request):
    """Cadastro manual de novos fornecedores no sistema."""
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
                razao_social=razao_social,
                nome_fantasia=nome_fantasia,
                cnpj=cnpj,
                email=email,
                telefone=telefone,
                logradouro=logradouro,
                cidade=cidade,
                estado=estado,
            )
            messages.success(request, f"Fornecedor '{nome_fantasia or razao_social}' cadastrado com sucesso!")
            return redirect('home')
        except Exception as e:
            messages.error(request, f"Erro ao cadastrar fornecedor: {e}")

    return render(request, 'contas_pagar/cadastrar_fornecedor.html')