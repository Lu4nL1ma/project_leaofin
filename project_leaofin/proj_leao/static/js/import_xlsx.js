// ==========================================================================
// 1. FUNÇÕES GLOBAIS DE ABRIR E FECHAR O MODAL (Acessíveis via onclick no HTML)
// ==========================================================================
window.abrirModalUpload = function () {
    const modal = document.getElementById('modalUpload');
    if (modal) {
        modal.style.display = 'flex';
    }
};

window.fecharModalUpload = function () {
    const modal = document.getElementById('modalUpload');
    if (modal) {
        modal.style.display = 'none';
    }
    
    const form = document.getElementById('formUploadXlsx');
    if (form) form.reset();

    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    if (fileNameDiv) fileNameDiv.textContent = '';
};

// ==========================================================================
// 2. CONFIGURAÇÃO DOS EVENTOS (DRAG & DROP, CLIQUE E SUBMIT)
// ==========================================================================
document.addEventListener('DOMContentLoaded', function () {
    const dropzone = document.getElementById('dropzoneXlsx');
    const fileInput = document.getElementById('arquivo_xlsx');
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    const form = document.getElementById('formUploadXlsx');

    if (!dropzone || !fileInput) return;

    // 1. Clique na caixa (dropzone) -> simula clique no input de arquivo
    dropzone.addEventListener('click', function (e) {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });

    // 2. Seleção via janela de arquivos -> exibe nome no HTML
    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) {
            fileNameDiv.textContent = '📄 ' + fileInput.files[0].name;
        } else {
            fileNameDiv.textContent = '';
        }
    });

    // 3. Previne que o navegador abra o arquivo diretamente na aba ao arrastar
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    // 4. Arrastar e Soltar (DROP): Transfere os arquivos para o <input>
    dropzone.addEventListener('drop', function (e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files && files.length > 0) {
            // Cria um novo DataTransfer para garantir a atribuição correta no input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(files[0]);
            fileInput.files = dataTransfer.files;

            fileNameDiv.textContent = '📄 ' + files[0].name;
        }
    });

    // 5. Validação antes de enviar o formulário
    if (form) {
        form.addEventListener('submit', function (e) {
            if (!fileInput.files || fileInput.files.length === 0) {
                e.preventDefault(); // Bloqueia o envio se não houver arquivo
                alert('Por favor, selecione ou arraste um arquivo .xlsx antes de importar.');
            }
        });
    }
});