from django.shortcuts import render
from app_leao.models import ContaPagar
from django.core.paginator import Paginator

def home(request):
    # 1. Busca todos os registros do banco (a ordenação padrão [-vencimento] vem do Model Meta)
    queryset = ContaPagar.objects.all()

    # 2. Captura os filtros que o usuário digitou na barra superior do HTML (via método GET)
    filtro_fornecedor = request.GET.get('fornecedor')
    filtro_categoria = request.GET.get('categoria')

    # 3. Aplica os filtros no ORM caso o usuário tenha digitado algo (o __icontains ignora maiúsculas/minúsculas)
    if filtro_fornecedor:
        queryset = queryset.filter(fornecedor__icontains=filtro_fornecedor)
        
    if filtro_categoria:
        queryset = queryset.filter(categoria__icontains=filtro_categoria)

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
    return render(request, 'form.html')