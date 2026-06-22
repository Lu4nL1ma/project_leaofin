// ==========================================================================
// 1. FUNÇÃO PARA ABRIR O MODAL E PREENCHER OS DADOS INFORMATIVOS
// ==========================================================================
function abrirModal(id, dataPagamento, juros, fornecedor, vencimento, valor) {
    console.log("-> Abrindo modal para o ID:", id); // Log de teste no console

    // Injeta o ID no input oculto do formulário
    document.getElementById('modal-item-id').value = id;
    
    // Preenche os campos informativos do topo do modal
    if (fornecedor) document.getElementById('modal-texto-fornecedor').innerText = fornecedor;
    if (valor) document.getElementById('modal-texto-valor').innerText = 'R$ ' + valor;

    // Formata a data de vencimento (AAAA-MM-DD -> DD/MM/AAAA)
    if (vencimento && vencimento !== 'None' && vencimento !== '') {
        const partes = vencimento.split('-');
        if (partes.length === 3) {
            document.getElementById('modal-texto-vencimento').innerText = `${partes[2]}/${partes[1]}/${partes[0]}`;
        } else {
            document.getElementById('modal-texto-vencimento').innerText = vencimento;
        }
    } else {
        document.getElementById('modal-texto-vencimento').innerText = '-';
    }

    // Configura a data de pagamento padrão (se não houver, sugere hoje)
    const inputData = document.getElementById('modal-data-input');
    if (dataPagamento && dataPagamento !== 'None' && dataPagamento !== '') {
        inputData.value = dataPagamento;
    } else {
        const hoje = new Date().toISOString().split('T')[0];
        inputData.value = hoje;
    }

    // Configura os juros
    const inputJuros = document.getElementById('modal-juros-input');
    if (juros && juros !== 'None' && juros !== '0') {
        inputJuros.value = parseFloat(juros).toFixed(2);
    } else {
        inputJuros.value = '';
    }

    // Abre o modal adicionando a classe do CSS
    document.getElementById('statusModal').classList.add('active');
}

// ==========================================================================
// 2. FUNÇÃO PARA FECHAR O MODAL
// ==========================================================================
function fecharModal() {
    document.getElementById('statusModal').classList.remove('active');
    document.getElementById('statusForm').reset();
}

// ==========================================================================
// 3. CAPTURA O ENVIO DO FORMULÁRIO (REQUISIÇÃO AJAX/FETCH BLINDADA)
// ==========================================================================
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('statusForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Impede o recarregamento tradicional da página
            
            console.log("-> Formulário enviado! Processando requisição...");

            const itemId = document.getElementById('modal-item-id').value;
            const formData = new FormData(this);

            // Garante que a URL use a barra no início e no fim para casar com o urls.py do Django
            const url = `/atualizar-status-json/${itemId}/`;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => {
                console.log("-> Status de resposta do servidor:", response.status);
                if (!response.ok) {
                    throw new Error('Resposta do servidor não foi OK');
                }
                return response.json();
            })
            .then(data => {
                console.log("-> Dados retornados pelo Django:", data);
                if (data.success) {
                    fecharModal();
                    window.location.reload(); // Recarrega a página atualizada
                } else {
                    alert('Erro ao atualizar: ' + (data.error || 'Erro interno do servidor.'));
                }
            })
            .catch(error => {
                console.error('-> Erro crítico detectado:', error);
                alert('Erro na comunicação com o sistema. Verifique o console.');
            });
        });
    } else {
        console.error("-> ATENÇÃO: O formulário 'statusForm' não foi encontrado na página.");
    }
});