function selecionarOuCriarOption(selectId, valor) {
    const select = document.getElementById(selectId);
    if (!select) return;

    // remove qualquer option temporária adicionada em uma edição anterior
    Array.from(select.querySelectorAll('option[data-temporaria="true"]')).forEach(opt => opt.remove());

    if (!valor) {
        select.value = '';
        return;
    }
    const existe = Array.from(select.options).some(opt => opt.value === valor);
    if (!existe) {
        const novaOption = document.createElement('option');
        novaOption.value = valor;
        novaOption.textContent = valor + ' (não padronizado)';
        novaOption.dataset.temporaria = 'true';
        select.appendChild(novaOption);
    }
    select.value = valor;
}

function abrirModalEditar(id, vencimento, fornecedor, categoria, banco, parcela, valor, observacao) {
    const modalEditar = document.getElementById('modalEditar');
    if (!modalEditar) {
        console.error('modalEditar não encontrado -- confira se {% include "modal_editar_registro.html" %} está presente na página.');
        return;
    }

    document.getElementById('editar_id').value = id;
    document.getElementById('editar_vencimento').value = vencimento;
    selecionarOuCriarOption('editar_fornecedor', fornecedor);
    selecionarOuCriarOption('editar_categoria', categoria);
    selecionarOuCriarOption('editar_banco', banco);
    document.getElementById('editar_parcela').value = parcela;
    document.getElementById('editar_valor').value = valor;
    document.getElementById('editar_observacao').value = observacao;
    modalEditar.classList.add('active');
}

function fecharModalEditar() {
    const modalEditar = document.getElementById('modalEditar');
    if (modalEditar) {
        modalEditar.classList.remove('active');
    }
}

// listeners de fechar clicando fora / ESC -- registrados uma vez,
// quando o DOM da página (incluindo o partial do modal) já está pronto.
document.addEventListener('DOMContentLoaded', function () {
    const modalEditar = document.getElementById('modalEditar');
    if (!modalEditar) return; // página não incluiu o modal -- nada a fazer

    modalEditar.addEventListener('click', function (event) {
        if (event.target === modalEditar) {
            fecharModalEditar();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && modalEditar.classList.contains('active')) {
            fecharModalEditar();
        }
    });
});