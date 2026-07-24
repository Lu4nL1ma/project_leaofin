window.abrirModalUpload = function () {
    const modal = document.getElementById('modalUpload');
    if (modal) {
        modal.style.display = 'flex';
        voltarParaUpload();
    }
};

window.fecharModalUpload = function () {
    const modal = document.getElementById('modalUpload');
    if (modal) modal.style.display = 'none';
    
    const form = document.getElementById('formUploadXlsx');
    if (form) form.reset();

    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    if (fileNameDiv) fileNameDiv.textContent = '';
};

// Reseta o modal para a tela de envio (Passo 1)
window.voltarParaUpload = function () {
    const stepUpload = document.getElementById('modalStepUpload');
    const stepResultado = document.getElementById('modalStepResultado');
    const form = document.getElementById('formUploadXlsx');
    
    if (form) form.reset();
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    if (fileNameDiv) fileNameDiv.textContent = '';

    stepResultado.style.display = 'none';
    stepUpload.style.display = 'block';
    stepUpload.classList.add('fade-in');
};

// Conclui e recarrega a página para atualizar as tabelas do dashboard
window.concluirEAtualizar = function () {
    window.location.reload();
};

document.addEventListener('DOMContentLoaded', function () {
    const dropzone = document.getElementById('dropzoneXlsx');
    const fileInput = document.getElementById('arquivo_xlsx');
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    const form = document.getElementById('formUploadXlsx');
    const btnImportar = document.getElementById('btnImportar');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', (e) => {
        if (e.target !== fileInput) fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDiv.textContent = '📄 ' + fileInput.files[0].name;
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            const dt = new DataTransfer();
            dt.items.add(files[0]);
            fileInput.files = dt.files;
            fileNameDiv.textContent = '📄 ' + files[0].name;
        }
    });

    // Envios via AJAX e Transição Visual de Tela
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Por favor, selecione um arquivo .xlsx.');
                return;
            }

            const formData = new FormData(form);
            btnImportar.disabled = true;
            btnImportar.textContent = 'Processando...';

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(res => res.json())
            .then(data => {
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';

                // Prepara e exibe a tela de resultados (Passo 2)
                exibirResultadoNoModal(data);
            })
            .catch(() => {
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';
                alert('Erro na requisição. Tente novamente.');
            });
        });
    }
});

// Monta o visual do Passo 2 e aplica a animação
function exibirResultadoNoModal(data) {
    const stepUpload = document.getElementById('modalStepUpload');
    const stepResultado = document.getElementById('modalStepResultado');
    const conteudo = document.getElementById('conteudoResultado');

    let html = '';

    if (data.sucesso) {
        html += `
            <div class="import-summary-grid">
                <div class="summary-card success">
                    <span class="number">${data.importados}</span>
                    <span class="label">Importadas</span>
                </div>
                <div class="summary-card info">
                    <span class="number">${data.duplicados}</span>
                    <span class="label">Duplicadas</span>
                </div>
            </div>
        `;

        if (data.erros && data.erros.length > 0) {
            html += `
                <div class="error-list-container">
                    <strong>⚠️ Linhas com inconsistências (${data.erros.length}):</strong>
                    <ul>
                        ${data.erros.map(e => `<li>${e}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    } else {
        html = `
            <div style="padding: 16px; background-color: #fce8e6; color: #c5221f; border-radius: 8px;">
                ❌ <strong>Erro:</strong> ${data.erro}
            </div>
        `;
    }

    conteudo.innerHTML = html;

    // Efeito visual de troca de telas
    stepUpload.style.display = 'none';
    stepResultado.style.display = 'block';
    stepResultado.classList.add('fade-in');
}