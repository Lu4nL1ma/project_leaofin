# app_leao/views/core_views.py

from django.shortcuts import render


def home(request):
    """Renderiza a tela inicial do sistema."""
    return render(request, 'home.html')


def recursos_humanos(request):
    """Renderiza a página principal do módulo de Recursos Humanos."""
    return render(request, 'recursos_humanos/rh.html')