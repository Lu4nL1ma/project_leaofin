// ==========================================
// CONTROLE DO MODAL E TROCA DE TELAS
// ==========================================

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

    if (stepResultado) stepResultado.style.display = 'none';
    if (stepUpload) {
        stepUpload.style.display = 'block';
        stepUpload.classList.add('fade-in');
    }
};

// Conclui e recarrega a página para atualizar as tabelas do dashboard
window.concluirEAtualizar = function () {
    window.location.reload();
};


// ==========================================
// TRATAMENTO DE DRAG & DROP E ENVIO (FETCH)
// ==========================================

document.addEventListener('DOMContentLoaded', function () {
    const dropzone = document.getElementById('dropzoneXlsx');
    const fileInput = document.getElementById('arquivo_xlsx');
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    const form = document.getElementById('formUploadXlsx');
    const btnImportar = document.getElementById('btnImportar');

    if (!dropzone || !fileInput) return;

    // 1. Clique no Dropzone
    dropzone.addEventListener('click', (e) => {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    // 2. Evento de Seleção de Arquivo via Input
    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
            fileNameDiv.textContent = '📄 ' + fileInput.files[0].name;
        }
    });

    // 3. Prevenção de comportamento padrão no Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // 4. Soltar arquivo no Dropzone
    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            fileInput.files = files;
            fileNameDiv.textContent = '📄 ' + files[0].name;
        }
    });

    // 5. Envio do Formulário via AJAX / Fetch
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Por favor, selecione um arquivo .xlsx.');
                return;
            }

            // Captura o Token CSRF do formulário
            const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');
            const csrfToken = csrfInput ? csrfInput.value : '';

            // Monta o FormData manualmente com o arquivo selecionado
            const formData = new FormData();
            formData.append('arquivo_xlsx', fileInput.files[0]);

            btnImportar.disabled = true;
            btnImportar.textContent = 'Processando...';

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken  // Header essencial para o Django não responder 400
                }
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(errData => { throw errData; });
                }
                return res.json();
            })
            .then(data => {
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';

                // Exibe o resultado no Passo 2 do modal
                exibirResultadoNoModal(data);
            })
            .catch(err => {
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';
                
                if (err && err.erro) {
                    exibirResultadoNoModal(err);
                } else {
                    alert('Erro na requisição. Verifique o console do navegador.');
                    console.error('Detalhes do erro:', err);
                }
            });
        });
    }
});


// ==========================================
// MONTAGEM DA TELA DE RESULTADOS (PASSO 2)
// ==========================================

function exibirResultadoNoModal(data) {
    const stepUpload = document.getElementById('modalStepUpload');
    const stepResultado = document.getElementById('modalStepResultado');
    const conteudo = document.getElementById('conteudoResultado');

    if (!stepResultado || !conteudo) return;

    let html = '';

    if (data.sucesso) {
        // Suporta tanto 'importados/duplicados' quanto 'criados/atualizados'
        const importados = data.importados !== undefined ? data.importados : (data.criados || 0);
        const duplicados = data.duplicados !== undefined ? data.duplicados : (data.atualizados || 0);

        html += `
            <div class="import-summary-grid">
                <div class="summary-card success">
                    <span class="number">${importados}</span>
                    <span class="label">Importadas</span>
                </div>
                <div class="summary-card info">
                    <span class="number">${duplicados}</span>
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
                ❌ <strong>Erro:</strong> ${data.erro || 'Falha ao processar o arquivo.'}
            </div>
        `;
    }

    conteudo.innerHTML = html;

    // Alterna visualmente para o Passo 2
    if (stepUpload) stepUpload.style.display = 'none';
    stepResultado.style.display = 'block';
    stepResultado.classList.add('fade-in');
}