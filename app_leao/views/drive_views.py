from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from app_leao.models import UserDocument



def upload_view(request):
    """Recebe o arquivo via formulário e cria o registro UserDocument integrado ao Drive."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        uploaded_file = request.FILES.get("file")

        if not uploaded_file:
            messages.error(request, "Nenhum arquivo foi selecionado.")
            return redirect(request.path)

        try:
            UserDocument.objects.create(
                title=title or uploaded_file.name,
                original_filename=uploaded_file.name,
                file=uploaded_file,
            )
            messages.success(
                request,
                f"Arquivo '{uploaded_file.name}' enviado com sucesso ao Google Drive!",
            )
            return redirect("file_list")

        except Exception as e:
            messages.error(
                request, f"Erro ao enviar arquivo para o Google Drive: {str(e)}"
            )
            return redirect(request.path)

    # Se o seu formulário estiver dentro de rh.html, altere aqui para 'rh.html'
    return render(request, "recursos_humanos/rh.html")


def file_list_view(request):
    """Lista todos os documentos salvos no banco de dados."""
    documentos = UserDocument.objects.all().order_by("-id")
    return render(request, "recursos_humanos/file_list.html", {"documentos": documentos})


def download_file_view(request, doc_id):
    """Recupera o arquivo salvo no Drive e dispara o download no navegador."""
    documento = get_object_or_404(UserDocument, id=doc_id)

    if not documento.file:
        raise Http404("Arquivo não encontrado no registro.")

    try:
        arquivo_drive = documento.file.open("rb")
        response = HttpResponse(
            arquivo_drive.read(), content_type="application/octet-stream"
        )
        nome_download = documento.original_filename or documento.title
        response["Content-Disposition"] = f'attachment; filename="{nome_download}"'
        return response
    except Exception as e:
        messages.error(request, f"Erro ao baixar arquivo do Google Drive: {str(e)}")
        return redirect("file_list")


def delete_file_view(request, doc_id):
    """Exclui o registro do banco e apaga o arquivo físico correspondente no Drive."""
    documento = get_object_or_404(UserDocument, id=doc_id)
    nome_arquivo = documento.original_filename or documento.title

    try:
        storage = GoogleDriveStorage()
        if documento.file:
            storage.delete(documento.file.name)

        documento.delete()
        messages.success(request, f"Arquivo '{nome_arquivo}' excluído com sucesso!")
    except Exception as e:
        messages.error(request, f"Erro ao excluir arquivo: {str(e)}")

    return redirect("file_list")