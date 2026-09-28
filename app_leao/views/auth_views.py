from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

def tela_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'login.html')

def login_usuario(request):
    if request.method == "POST":
        usuario_post = request.POST.get("username")
        senha_post = request.POST.get("password")

        user = authenticate(request, username=usuario_post, password=senha_post)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Usuário ou senha incorretos. Tente novamente.")
            return redirect('tela_login')
    return redirect('tela_login')

def logout_usuario(request):
    logout(request)
    return redirect('tela_login')