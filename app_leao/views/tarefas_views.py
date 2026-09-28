# app_leao/views/tarefas_views.py

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from app_leao.models import Tarefa


def tarefas(request):
    """Criação e listagem de tarefas com filtros por frequência, setor e status."""
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        setor = request.POST.get('setor', 'financeiro')
        frequencia = request.POST.get('frequencia', 'diaria')
        unidade = request.POST.get('unidade')
        responsavel = request.POST.get('responsavel')
        prioridade = request.POST.get('prioridade')
        data_limite = request.POST.get('data_limite') or None

        if titulo:
            Tarefa.objects.create(
                titulo=titulo,
                descricao=descricao,
                setor=setor,
                frequencia=frequencia,
                unidade=unidade,
                responsavel=responsavel,
                prioridade=prioridade,
                data_limite=data_limite
            )
            messages.success(request, "Atividade cadastrada com sucesso!")
        return redirect('tarefas')

    # Filtros
    frequencia_filtro = request.GET.get('frequencia')
    setor_filtro = request.GET.get('setor')
    status_filtro = request.GET.get('status')
    
    tarefas_queryset = Tarefa.objects.all()
    
    if frequencia_filtro:
        tarefas_queryset = tarefas_queryset.filter(frequencia=frequencia_filtro)
    if setor_filtro:
        tarefas_queryset = tarefas_queryset.filter(setor=setor_filtro)
    if status_filtro:
        tarefas_queryset = tarefas_queryset.filter(status=status_filtro)

    # Contadores
    total_diarias = Tarefa.objects.filter(frequencia='diaria').count()
    total_recorrentes = Tarefa.objects.filter(frequencia__in=['semanal', 'mensal']).count()
    total_avulsas = Tarefa.objects.filter(frequencia='avulsa').count()
    total_pendentes = Tarefa.objects.filter(status='pendente').count()

    context = {
        'tarefas': tarefas_queryset,
        'total_diarias': total_diarias,
        'total_recorrentes': total_recorrentes,
        'total_avulsas': total_avulsas,
        'total_pendentes': total_pendentes,
        'frequencia_filtro': frequencia_filtro,
        'setor_filtro': setor_filtro,
        'status_filtro': status_filtro,
        'setores_choices': Tarefa.SETOR_CHOICES,
    }
    return render(request, 'tarefas.html', context)


def alternar_status_tarefa(request, pk):
    """Alterna ciclicamente o status da tarefa: pendente -> em_andamento -> concluida -> pendente."""
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if tarefa.status == 'pendente':
        tarefa.status = 'em_andamento'
    elif tarefa.status == 'em_andamento':
        tarefa.status = 'concluida'
    else:
        tarefa.status = 'pendente'
    tarefa.save()
    return redirect('tarefas')


def deletar_tarefa(request, pk):
    """Remove o registro da tarefa do banco de dados."""
    tarefa = get_object_or_404(Tarefa, pk=pk)
    tarefa.delete()
    messages.info(request, "Atividade removida com sucesso.")
    return redirect('tarefas')