from datetime import datetime
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render

# Importação absoluta evitando o erro de subpasta
from app_leao.services import gerar_excel_consolidado_em_memoria

# ==============================================================================
# DICIONÁRIO / DEPARA DE CONTAS CORRENTES
# ==============================================================================
MAPEAMENTO_CONTA_CORRENTE = {
    "40147": "Bradesco (Matriz)",
    "40436": "Bradesco (Aeroporto)",
    "41835": "Bradesco (Castanheira)",
    "41828": "Bradesco (Baenão)",
    "41818": "Bradesco (Pátio Belém)",
}


def mapear_conta_corrente(valor_bruto: str) -> str:
    """Converte números de contas correntes para o nome padronizado da agência/loja."""
    if not valor_bruto:
        return "Não Identificado"

    val_str = str(valor_bruto).strip().replace(".0", "")

    for cod, nome in MAPEAMENTO_CONTA_CORRENTE.items():
        if cod in val_str:
            return nome

    return val_str


def upload_ofx_view(request):
    if request.method == "POST":
        # Captura os 5 campos do formulário
        arquivos = [
            request.FILES.get("ofx_1"),
            request.FILES.get("ofx_2"),
            request.FILES.get("ofx_3"),
            request.FILES.get("ofx_4"),
            request.FILES.get("ofx_5"),
        ]

        # Filtra apenas os inputs enviados
        arquivos_validos = [arq for arq in arquivos if arq]

        if not arquivos_validos:
            messages.error(
                request, "Selecione ao menos 1 arquivo OFX para processar."
            )
            return render(request, "contas_pagar/upload_ofx.html")

        # Validação de formato
        for arq in arquivos_validos:
            if not arq.name.lower().endswith(".ofx"):
                messages.error(
                    request,
                    f"O arquivo '{arq.name}' não possui extensão .ofx válida.",
                )
                return render(request, "contas_pagar/upload_ofx.html")

        try:
            # Chamada sem o parâmetro extra que causava o erro
            excel_bytes = gerar_excel_consolidado_em_memoria(arquivos_validos)

            nome_download = f"Consolidado_5Contas.xlsx"

            response = HttpResponse(
                excel_bytes.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{nome_download}"'
            )
            return response

        except Exception as e:
            messages.error(
                request, f"Erro ao processar os extratos OFX: {str(e)}"
            )

    return render(request, "contas_pagar/upload_ofx.html")