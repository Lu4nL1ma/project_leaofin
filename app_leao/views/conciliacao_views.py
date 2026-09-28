import io
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Sum, Value, FloatField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from app_leao.models import ContaPagar, ConciliacaoBancaria, TransacaoExtrato, BancoSaldo

try:
    from ofxtools.Parser import OFXTree
except ImportError:
    OFXTree = None

def aba_conciliacao(request):
    ids_conciliados = ConciliacaoBancaria.objects.values_list('conta_pagar_id', flat=True).distinct()
    queryset = ContaPagar.objects.filter(status__icontains="Pago").order_by("-vencimento")

    filtro_fornecedor = request.GET.get("fornecedor")
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)

    ids_conta_manual = ConciliacaoBancaria.objects.filter(transacao_extrato_id=0).values_list('conta_pagar_id', flat=True)
    total_manual = ContaPagar.objects.filter(id__in=ids_conta_manual).aggregate(
        total=Coalesce(Sum('valor'), Value(0.0), output_field=FloatField())
    )['total']

    ids_extrato_ofx = ConciliacaoBancaria.objects.exclude(transacao_extrato_id=0).values_list('transacao_extrato_id', flat=True)
    total_ofx = TransacaoExtrato.objects.filter(id__in=ids_extrato_ofx).aggregate(
        total=Coalesce(Sum('valor_extrato'), Value(0.0), output_field=FloatField())
    )['total']

    total_conciliado = total_manual + total_ofx
    total_pendente = queryset.exclude(id__in=ids_conciliados).aggregate(
        total=Coalesce(Sum('valor'), Value(0.0), output_field=FloatField())
    )['total']

    paginator = Paginator(queryset, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    bancos_disponiveis = BancoSaldo.objects.all().order_by('nome')

    context = {
        'page_obj': page_obj,
        'total_conciliado': total_conciliado,
        'total_pendente': total_pendente,
        'bancos_disponiveis': bancos_disponiveis,
        'ids_conciliados': set(ids_conciliados),
        'filtro_fornecedor': filtro_fornecedor,
    }
    return render(request, 'conciliacao.html', context)

def conciliar(request, identi):
    if ConciliacaoBancaria.objects.filter(conta_pagar_id=identi).exists():
        ConciliacaoBancaria.objects.filter(conta_pagar_id=identi).delete()
    else:
        conta = get_object_or_404(ContaPagar, id=identi)
        ConciliacaoBancaria.objects.create(
            conta_pagar_id=conta.id,
            transacao_extrato_id=0,
            data_conciliacao=date.today(),
            banco_pago=conta.banco,
        )
    url_anterior = request.META.get("HTTP_REFERER")
    return redirect(url_anterior) if url_anterior else redirect("home")

def processar_ofx_ajax(request):
    if request.method != "POST" or not request.FILES.get("arquivo_ofx"):
        return JsonResponse({'success': False, 'error': 'Método inválido ou arquivo não enviado.'})

    banco_destino = request.POST.get("banco_destino")
    arquivo_ofx = request.FILES.get("arquivo_ofx")

    if OFXTree is None:
        return JsonResponse({'success': False, 'error': 'Biblioteca ofxtools não está instalada no ambiente.'})

    try:
        conteudo = arquivo_ofx.read().decode("utf-8", errors="ignore")
        conteudo_corrigido = conteudo.replace("00000000000000", "20000101120000").replace("00000000", "20000101")

        parser = OFXTree()
        parser.parse(io.BytesIO(conteudo_corrigido.encode("utf-8")))
        obj = parser.convert()

        transacoes = obj.statements[0].banktranlist
        transacoes_ofx = []
        datas_transacoes = []

        extratos_ja_conciliados = set(
            ConciliacaoBancaria.objects.exclude(transacao_extrato_id=0).values_list('transacao_extrato_id', flat=True)
        )

        with transaction.atomic():
            for tx in transacoes:
                valor_trnamt = Decimal(str(tx.trnamt))
                if valor_trnamt >= 0:
                    continue

                valor_ajustado = abs(valor_trnamt)
                data_real = None
                if tx.dtposted:
                    if isinstance(tx.dtposted, (datetime, date)):
                        data_real = tx.dtposted if isinstance(tx.dtposted, date) else tx.dtposted.date()
                    else:
                        try:
                            data_real = datetime.strptime(str(tx.dtposted)[:10], '%Y-%m-%d').date()
                        except ValueError:
                            pass

                if data_real:
                    datas_transacoes.append(data_real)

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

                ja_conciliado = transacao_banco.id in extratos_ja_conciliados

                transacoes_ofx.append({
                    'id': transacao_banco.id,
                    'data': data_formatada,
                    'descricao': transacao_banco.descricao_ofx,
                    'valor': str(valor_ajustado),
                    'ja_conciliado': ja_conciliado,
                })

        ids_ja_conciliados = ConciliacaoBancaria.objects.values_list('conta_pagar_id', flat=True)
        contas_filtro = ContaPagar.objects.filter(
            banco=banco_destino,
            status__icontains="Pago",
        ).exclude(id__in=ids_ja_conciliados)

        if datas_transacoes:
            menor_data_ofx = min(datas_transacoes)
            maior_data_ofx = max(datas_transacoes)
            data_inicio_limite = menor_data_ofx - timedelta(days=7)
            data_fim_limite = maior_data_ofx + timedelta(days=7)
            contas_filtro = contas_filtro.filter(vencimento__range=(data_inicio_limite, data_fim_limite))

        contas_sistema = contas_filtro.order_by('vencimento').values('id', 'fornecedor', 'valor', 'vencimento')

        contas_pendentes = [
            {
                'id': conta['id'],
                'fornecedor': conta['fornecedor'],
                'valor': str(conta['valor']),
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
                    defaults={'transacao_extrato_id': extrato_id, 'data_conciliacao': agora}
                )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f"Erro interno ao salvar lote: {str(e)}"})
    return JsonResponse({'success': False, 'error': 'Método não permitido.'})