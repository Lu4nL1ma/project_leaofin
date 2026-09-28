window.abrirModalUpload = function () {
    document.getElementById('modalUpload').style.display = 'flex';
    voltarParaUpload();
};

window.fecharModalUpload = function () {
    document.getElementById('modalUpload').style.display = 'none';
    const form = document.getElementById('formUploadXlsx');
    if (form) form.reset();
    document.getElementById('nomeArquivoXlsx').textContent = '';
};

window.voltarParaUpload = function () {
    const form = document.getElementById('formUploadXlsx');
    if (form) form.reset();
    document.getElementById('nomeArquivoXlsx').textContent = '';
    document.getElementById('modalStepResultado').style.display = 'none';
    document.getElementById('modalStepUpload').style.display = 'block';
};

window.concluirEAtualizar = function () {
    window.location.reload();
};

document.addEventListener('DOMContentLoaded', function () {
    const dropzone = document.getElementById('dropzoneXlsx');
    const fileInput = document.getElementById('arquivo_xlsx');
    const fileNameDiv = document.getElementById('nomeArquivoXlsx');
    const form = document.getElementById('formUploadXlsx');
    const btnImportar = document.getElementById('btnImportar');

    if (!dropzone || !fileInput || !form) return;

    // Abrir seletor de arquivo ao clicar no dropzone
    dropzone.addEventListener('click', () => fileInput.click());

    // Atualizar nome do arquivo na tela
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDiv.textContent = '📄 ' + fileInput.files[0].name;
        }
    });

    // Submissão via AJAX
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        if (!fileInput.files || fileInput.files.length === 0) {
            alert('Selecione um arquivo .xlsx antes de prosseguir.');
            return;
        }

        btnImportar.disabled = true;
        btnImportar.textContent = 'Enviando...';

        // O FormData captura automaticamente o input de arquivo e o token CSRF do form
        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(res => {
            btnImportar.disabled = false;
            btnImportar.textContent = 'Importar';

            if (res.status === 200 && res.body.sucesso) {
                exibirResultado(res.body);
            } else {
                exibirErro(res.body.erro || 'Erro ao processar arquivo.');
            }
        })
        .catch(err => {
            btnImportar.disabled = false;
            btnImportar.textContent = 'Importar';
            exibirErro('Ocorreu uma falha de comunicação com o servidor.');
        });
    });
});

function exibirResultado(data) {
    const conteudo = document.getElementById('conteudoResultado');
    
    let html = `
        <p><strong>Registros Importados:</strong> ${data.importados}</p>
    `;

    if (data.erros && data.erros.length > 0) {
        html += `<div style="color: #b91c1c; margin-top: 10px;">
            <strong>Avisos/Alertas:</strong>
            <ul>${data.erros.map(e => `<li>${e}</li>`).join('')}</ul>
        </div>`;
    }

    conteudo.innerHTML = html;
    document.getElementById('modalStepUpload').style.display = 'none';
    document.getElementById('modalStepResultado').style.display = 'block';
}

function exibirErro(mensagem) {
    const conteudo = document.getElementById('conteudoResultado');
    conteudo.innerHTML = `<div style="color: red; padding: 10px; background: #fee2e2; border-radius: 4px;">❌ ${mensagem}</div>`;
    document.getElementById('modalStepUpload').style.display = 'none';
    document.getElementById('modalStepResultado').style.display = 'block';
}