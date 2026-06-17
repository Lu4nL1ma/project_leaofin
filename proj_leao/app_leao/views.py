from django.shortcuts import render, redirect, get_object_or_404
from app_leao.models import ContaPagar
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime
from django.http import JsonResponse

def home(request):
    # 1. Busca todos os registros do banco (a ordenação padrão [-vencimento] vem do Model Meta)
    queryset = ContaPagar.objects.all()

    # 2. Captura os filtros que o usuário digitou na barra superior do HTML (via método GET)
    filtro_fornecedor = request.GET.get('fornecedor')
    filtro_categoria = request.GET.get('categoria')
    filtro_data = request.GET.get('data')

    # 3. Aplica os filtros no ORM caso o usuário tenha digitado algo (o __icontains ignora maiúsculas/minúsculas)
    if filtro_fornecedor and filtro_fornecedor.strip():
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)
        
    if filtro_categoria and filtro_categoria.strip():
        queryset = queryset.filter(categoria__icontains=filtro_categoria)

    # CORRIGIDO: Só tenta converter e filtrar a data se ela foi preenchida
    if filtro_data and filtro_data.strip():
        try:
            data_objeto = datetime.strptime(filtro_data.strip(), '%d/%m/%Y')
            filtro_data_formatada = data_objeto.strftime('%Y-%m-%d')
            
            # CORRIGIDO: Atribuído ao queryset e usando a variável correta
            queryset = queryset.filter(vencimento=filtro_data_formatada)
        except ValueError:
            # Caso o usuário digite uma data maluca (ex: 99/99/9999)
            messages.error(request, "Formato de data inválido. Use DD/MM/AAAA.")

    # 4. Configura a Paginação para exibir estritamente 20 linhas por página
    paginator = Paginator(queryset, 15)
    
    # Captura o número da página atual na URL (ex: ?page=2). Se não houver, assume a página 1.
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 5. Envia o 'page_obj' para o HTML. O seu template já está programado para ler essa variável!
    context = {
        'page_obj': page_obj
    }
    
    return render(request, 'home.html', context)

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

    # Redireciona de volta para a função home (sua tabela)
    return redirect('homes') # Use uma string com o nome que está no urls.py

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