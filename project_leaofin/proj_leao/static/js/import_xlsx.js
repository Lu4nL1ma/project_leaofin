// =========================================================================
// Funções Globais para Controle de Abertura e Fechamento do Modal
// =========================================================================

window.abrirModalUpload = function () {
    const modal = document.getElementById('modalUpload');
    if (modal) modal.style.display = 'flex';
};

window.fecharModalUpload = function () {
    const modal = document.getElementById('modalUpload');
    if (modal) modal.style.display = 'none';
    
    // Reseta o formulário
    const form = document.getElementById('formUploadXlsx');
    if (form) form.reset();

    // Limpa a visualização do nome do arquivo
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    if (fileNameDiv) fileNameDiv.textContent = '';

    // Oculta e limpa a área de status
    const statusModal = document.getElementById('statusModal');
    if (statusModal) {
        statusModal.style.display = 'none';
        statusModal.innerHTML = '';
    }
};

// =========================================================================
// Eventos e Manipulação do Drag & Drop e Envio AJAX
// =========================================================================

document.addEventListener('DOMContentLoaded', function () {
    const dropzone = document.getElementById('dropzoneXlsx');
    const fileInput = document.getElementById('arquivo_xlsx');
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    const form = document.getElementById('formUploadXlsx');
    const statusModal = document.getElementById('statusModal');
    const btnImportar = document.getElementById('btnImportar');

    if (!dropzone || !fileInput) return;

    // 1. Clique na caixa aciona a seleção de arquivos
    dropzone.addEventListener('click', function (e) {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    // 2. Atualiza a tela quando o arquivo é selecionado via clique
    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) {
            fileNameDiv.textContent = '📄 ' + fileInput.files[0].name;
            if (statusModal) statusModal.style.display = 'none';
        }
    });

    // 3. Previne comportamento padrão do navegador ao arrastar arquivos
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    // 4. Efeito visual simples ao passar o arquivo por cima
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.style.borderColor = '#2b6cb0';
            dropzone.style.backgroundColor = '#ebf8ff';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
            dropzone.style.borderColor = '#cbd5e0';
            dropzone.style.backgroundColor = '#transparent';
        }, false);
    });

    // 5. Captura o arquivo solto no Drop
    dropzone.addEventListener('drop', function (e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files.length > 0) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            fileInput.files = dataTransfer.files;

            fileNameDiv.textContent = '📄 ' + files[0].name;
            if (statusModal) statusModal.style.display = 'none';
        }
    });

    // 6. Intercepta o envio do formulário via AJAX (fetch)
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault(); // Impede o reload da página

            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Por favor, selecione ou arraste um arquivo .xlsx antes de importar.');
                return;
            }

            const formData = new FormData(form);

            // Desabilita botão e feedback visual de processamento
            btnImportar.disabled = true;
            btnImportar.textContent = 'Processando...';

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Reabilita o botão
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';
                statusModal.style.display = 'block';

                if (data.sucesso) {
                    let html = `<div style="padding: 12px; border-radius: 6px; background-color: #e6f4ea; color: #137333; font-size: 13px; line-height: 1.5;">`;
                    html += `<strong>✅ Importação Concluída!</strong><br>`;
                    html += `• ${data.importados} conta(s) salva(s) com sucesso.<br>`;
                    
                    if (data.duplicados > 0) {
                        html += `• ${data.duplicados} registro(s) ignorado(s) por duplicidade.<br>`;
                    }

                    if (data.erros && data.erros.length > 0) {
                        html += `<hr style="margin: 8px 0; border: 0; border-top: 1px solid #ceead6;">`;
                        html += `<strong>⚠️ Linhas não importadas (${data.erros.length}):</strong><br>`;
                        const errosExibicao = data.erros.slice(0, 5).join('<br>');
                        html += errosExibicao;
                        if (data.erros.length > 5) {
                            html += `<br>... e mais ${data.erros.length - 5} erro(s).`;
                        }
                    }

                    html += `</div>`;
                    statusModal.innerHTML = html;
                } else {
                    statusModal.innerHTML = `
                        <div style="padding: 12px; border-radius: 6px; background-color: #fce8e6; color: #c5221f; font-size: 13px; line-height: 1.5;">
                            ❌ <strong>Erro:</strong> ${data.erro}
                        </div>
                    `;
                }
            })
            .catch(error => {
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';
                statusModal.style.display = 'block';
                statusModal.innerHTML = `
                    <div style="padding: 12px; border-radius: 6px; background-color: #fce8e6; color: #c5221f; font-size: 13px;">
                        ❌ Erro de conexão ou falha ao processar o arquivo.
                    </div>
                `;
            });
        });
    }
});