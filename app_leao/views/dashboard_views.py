# app_leao/views/dashboard_views.py

import json
from datetime import date
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from app_leao.models import ContaPagar, ConciliacaoBancaria


def dashboard_leve(request):
    """Calcula indicadores financeiros, taxas de conciliação e dados dos gráficos."""
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