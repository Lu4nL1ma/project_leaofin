from django.shortcuts import render
from app_leao.models import ContaPagar
from django.core.paginator import Paginator
from django.contrib import messages

def home(request):
    # 1. Busca todos os registros do banco (a ordenação padrão [-vencimento] vem do Model Meta)
    queryset = ContaPagar.objects.all()

    # 2. Captura os filtros que o usuário digitou na barra superior do HTML (via método GET)
    filtro_fornecedor = request.GET.get('fornecedor')
    filtro_categoria = request.GET.get('categoria')
    filtro_data = request.GET.get('data')

    # 3. Aplica os filtros no ORM caso o usuário tenha digitado algo (o __icontains ignora maiúsculas/minúsculas)
    if filtro_fornecedor:
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)
        
    if filtro_categoria:
        queryset = queryset.filter(categoria__icontains=filtro_categoria)

    if filtro_categoria:
        queryset = queryset.filter(data__icontains=filtro_data)

    # 4. Configura a Paginação para exibir estritamente 20 linhas por página
    paginator = Paginator(queryset, 20)
    
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
            return redirect('nome_da_sua_view_de_listagem') # Mude para a sua rota de sucesso
        except Exception as e:
            messages.error(request, f"Erro ao salvar: {e}")

    # Se for GET, apenas renderiza a página do formulário
    return render(request, 'form.html') # Ajuste o caminho do seu HTML