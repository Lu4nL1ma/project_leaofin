# app_leao/views/caixa_views.py

from datetime import datetime
import openpyxl
from django.contrib import messages
from django.shortcuts import redirect, render
from app_leao.models import BancoSaldo, FechamentoCaixa, Deposito


def saldo(request):
    """
    Exibe o painel de saldos consolidados e sangrias por unidade.
    O import do pandas é feito sob demanda para não onerar o startup do servidor.
    """
    import pandas as pd  # Carregamento apenas quando a view for chamada

    bancos = BancoSaldo.objects.all().order_by('nome')

    dados = FechamentoCaixa.objects.all().values_list(
        'data',        
        'unidade', 
        'abertura', 
        'suprimento', 
        'saidas', 
        'troco', 
        'vendas', 
        'total_dinheiro', 
        'sangria'
    )

    df = pd.DataFrame(
        list(dados), 
        columns=['Data', 'Unidade', 'Abertura', 'Suprimento', 'Saídas', 'Troco', 'Vendas', 'Total Dinheiro', 'Sangria']
    )

    if not df.empty:
        df['Unidade'] = df['Unidade'].str.strip()
        total = df['Sangria'].sum()
        saldo_aero = df[df['Unidade'] == 'AEROPORTO']['Sangria'].sum()
        saldo_casta = df[df['Unidade'] == 'BR 316']['Sangria'].sum()
        saldo_baenoso = df[df['Unidade'] == 'ESTADIO BAENAO']['Sangria'].sum()
        saldo_patio = df[df['Unidade'] == 'PADRE EUTIQUIO']['Sangria'].sum()
    else:
        total = saldo_aero = saldo_casta = saldo_baenoso = saldo_patio = 0

    context = {
        'total': total,
        'saldo_aero': saldo_aero,
        'saldo_casta': saldo_casta,
        'saldo_baenoso': saldo_baenoso,
        'saldo_patio': saldo_patio,
        'bancos': bancos,
    }

    return render(request, "caixa_fisico/saldo.html", context)


def deposito(request):
    """
    Registra um novo depósito manual enviado pelo formulário.
    """
    if request.method == 'POST':
        unidade = request.POST.get('unidade')
        data_deposito = request.POST.get('data_deposito')
        valor = request.POST.get('valor')
        destino = request.POST.get('destino')
        comprovante = request.FILES.get('comprovante')
        observacao = request.POST.get('observacao')

        if unidade and data_deposito and valor:
            Deposito.objects.create(
                unidade=unidade,
                data_deposito=data_deposito,
                valor=valor,
                destino=destino,
                comprovante=comprovante,
                observacao=observacao
            )
            messages.success(request, 'Depósito registrado com sucesso!')
        else:
            messages.error(request, 'Erro ao registrar: preencha todos os campos obrigatórios.')

    return redirect(request.META.get('HTTP_REFERER', '/'))


def importar_fechamento_caixa(request):
    """
    Processa e importa via openpyxl a planilha de fechamento de caixa diário.
    """
    if request.method == 'POST':
        if 'arquivo' not in request.FILES:
            messages.error(request, 'Nenhum arquivo foi selecionado.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        arquivo = request.FILES['arquivo']

        # Validação de extensão
        if not arquivo.name.endswith(('.xlsx', '.xlsm')):
            messages.error(request, 'Envie um arquivo do Excel (.xlsx). Para CSV, salve em .xlsx.')
            return redirect(request.META.get('HTTP_REFERER', '/'))

        try:
            wb = openpyxl.load_workbook(arquivo, data_only=True)
            sheet = wb.active

            primeira_linha = [str(cell.value or '').strip().lower() for cell in sheet[1]]

            def get_col_index(nome_coluna):
                try:
                    return primeira_linha.index(nome_coluna)
                except ValueError:
                    return None

            col_data = get_col_index('data')
            col_unidade = get_col_index('unidade')
            col_abertura = get_col_index('abertura')
            col_suprimento = get_col_index('suprimento')
            col_saidas = get_col_index('saidas') or get_col_index('saídas')
            col_troco = get_col_index('troco')
            col_vendas = get_col_index('vendas')
            col_total_dinheiro = get_col_index('total dinheiro')
            col_sangria = get_col_index('sangria')

            if col_data is None:
                messages.error(request, "Cabeçalho 'Data' não encontrado na planilha.")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            registros = []

            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not any(row):
                    continue

                val_data = row[col_data] if col_data is not None else None
                data_formatada = None

                if isinstance(val_data, datetime):
                    data_formatada = val_data.date()
                elif isinstance(val_data, str) and val_data.strip():
                    try:
                        data_formatada = datetime.strptime(val_data.strip(), "%d/%m/%Y").date()
                    except ValueError:
                        try:
                            data_formatada = datetime.strptime(val_data.strip(), "%Y-%m-%d").date()
                        except ValueError:
                            pass

                if not data_formatada:
                    continue

                def clean_decimal(val):
                    if val is None:
                        return 0.0
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return 0.0

                registros.append(
                    FechamentoCaixa(
                        data=data_formatada,
                        unidade=str(row[col_unidade]) if col_unidade is not None and row[col_unidade] else '',
                        abertura=clean_decimal(row[col_abertura] if col_abertura is not None else 0),
                        suprimento=clean_decimal(row[col_suprimento] if col_suprimento is not None else 0),
                        saidas=clean_decimal(row[col_saidas] if col_saidas is not None else 0),
                        troco=clean_decimal(row[col_troco] if col_troco is not None else 0),
                        vendas=clean_decimal(row[col_vendas] if col_vendas is not None else 0),
                        total_dinheiro=clean_decimal(row[col_total_dinheiro] if col_total_dinheiro is not None else 0),
                        sangria=clean_decimal(row[col_sangria] if col_sangria is not None else 0),
                    )
                )

            if registros:
                FechamentoCaixa.objects.bulk_create(registros)
                messages.success(request, f'{len(registros)} registros importados com sucesso!')
            else:
                messages.warning(request, 'Nenhum dado válido encontrado na planilha.')

        except Exception as e:
            messages.error(request, f'Erro ao ler o arquivo Excel: {str(e)}')

        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')