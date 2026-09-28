// Funções para abrir e fechar o modal de exportação
function abrirModalExportar() {
    const modal = document.getElementById('modalExportar');
    if (modal) {
        modal.classList.add('active');
    }
}

function fecharModalExportar() {
    const modal = document.getElementById('modalExportar');
    if (modal) {
        modal.classList.remove('active');
    }
}

// Alternar visibilidade dos campos de data
function toggleDatasExportar() {
    const opPeriodo = document.getElementById('exportPeriodo');
    const camposDatas = document.getElementById('camposDatasExport');
    const inputInicio = document.getElementById('data_inicio');
    const inputFim = document.getElementById('data_fim');

    if (opPeriodo && opPeriodo.checked) {
        camposDatas.style.display = 'flex';
        inputInicio.required = true;
        inputFim.required = true;
    } else {
        camposDatas.style.display = 'none';
        inputInicio.required = false;
        inputFim.required = false;
        inputInicio.value = '';
        inputFim.value = '';
    }
}

// Fechar após iniciar o download
function fecharModalExportarAposDownload() {
    setTimeout(() => {
        fecharModalExportar();
    }, 400);
}

// Fechar ao clicar fora do card (overlay)
window.addEventListener('click', function(event) {
    const modal = document.getElementById('modalExportar');
    if (event.target === modal) {
        fecharModalExportar();
    }
});