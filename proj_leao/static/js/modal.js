const modal = document.getElementById('statusModal');

    function abrirModal(id, dataAtual, jurosAtual) {
        document.getElementById('modal-item-id').value = id;
        
        // Se não tiver data salva, podemos sugerir automaticamente a data de hoje!
        const hoje = new Date().toISOString().split('T')[0];
        document.getElementById('modal-data-input').value = dataAtual || hoje;
        
        document.getElementById('modal-juros-input').value = jurosAtual || 0;
        modal.classList.add('active');
    }

    function fecharModal() {
        modal.classList.remove('active');
    }

    document.getElementById('statusForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const id = document.getElementById('modal-item-id').value;
        const formData = new FormData(this);

        fetch(`/atualizar-status-json/${id}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                fecharModal();
                window.location.reload(); 
            } else {
                alert('Erro ao atualizar as informações.');
            }
        });
    });