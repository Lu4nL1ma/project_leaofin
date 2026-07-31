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

    // 1. Clique seguro no dropzone para abrir a janela de seleção
    dropzone.addEventListener('click', (e) => {
        // Evita reabrir se clicar diretamente no input invisível
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    // 2. Exibição do nome do arquivo selecionado via clique
    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
            fileNameDiv.textContent = '📄 ' + fileInput.files[0].name;
        }
    });

    // 3. Suporte a Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            fileInput.files = files; // Atribui os arquivos arrastados diretamente ao input
            fileNameDiv.textContent = '📄 ' + files[0].name;
        }
    });

    // 4. Envio do Formulário por AJAX (com tratamento defensivo do arquivo)
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            // Validação no front-end antes de disparar o fetch
            if (!fileInput.files || fileInput.files.length === 0) {
                alert('Por favor, selecione um arquivo .xlsx antes de importar.');
                return;
            }

            // Garante a montagem manual do FormData caso o form.reset() ou outro fator limpe o estado
            const formData = new FormData();
            
            // Pega o token CSRF diretamente do formulário
            const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
            formData.append('csrfmiddlewaretoken', csrfToken);
            
            // Anexa explicitamente o arquivo selecionado
            formData.append('arquivo_xlsx', fileInput.files[0]);

            btnImportar.disabled = true;
            btnImportar.textContent = 'Processando...';

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest' 
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
                exibirResultadoNoModal(data);
            })
            .catch(err => {
                btnImportar.disabled = false;
                btnImportar.textContent = 'Importar';
                
                // Se a view retornou um JSON de erro (ex: Fornecedor não encontrado)
                if (err && err.erro) {
                    exibirResultadoNoModal(err);
                } else {
                    alert('Erro na requisição ou resposta inválida do servidor.');
                }
            });
        });
    }
});