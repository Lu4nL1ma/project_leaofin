document.addEventListener("DOMContentLoaded", function() {
    let transacoesGlobais = [];
    let contasGlobais = [];
    let bancoAtivo = "";

    const formOfx = document.getElementById('formOfx');
    if (formOfx) {
        formOfx.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const url = this.getAttribute('action') || window.location.href;
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const modalOfxEl = document.getElementById('modalOfx');
                    const modalOfxInst = bootstrap.Modal.getInstance(modalOfxEl) || new bootstrap.Modal(modalOfxEl);
                    modalOfxInst.hide();

                    transacoesGlobais = data.transacoes_ofx;
                    contasGlobais = data.contas_pendentes;
                    bancoAtivo = data.banco;

                    montarPainelAuditoria();
                    
                    const modalLote = new bootstrap.Modal(document.getElementById('modalAuditoriaLote'));
                    modalLote.show();
                } else {
                    alert('Erro no processamento: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Erro detalhado no processamento:', error);
                alert('Falha na comunicação com o servidor ao processar arquivo.');
            });
        });
    }

    function parseDataBr(stringData) {
        if (!stringData || stringData === '-') return null;
        const partes = stringData.split('/');
        if (partes.length === 3) {
            return new Date(partes[2], partes[1] - 1, partes[0]);
        }
        return null;
    }

    function montarPainelAuditoria() {
        document.getElementById('lblBancoAtivo').innerText = bancoAtivo;
        
        const containerOfx = document.getElementById('containerTransacoesOfx');
        const containerSistema = document.getElementById('containerContasSistema');
        
        containerOfx.innerHTML = "";
        containerSistema.innerHTML = "";

        if (transacoesGlobais.length === 0) {
            containerOfx.innerHTML = '<div class="alert alert-info">Nenhum débito encontrado no arquivo OFX.</div>';
            return;
        }

        transacoesGlobais.forEach(tx => {
            const valorTxFloat = parseFloat(tx.valor) || 0;

            // Se a transação no arquivo OFX já tiver sido conciliada no banco de dados, renderiza o card travado/estilizado
            if (tx.ja_conciliado) {
                const cardTx = document.createElement('div');
                cardTx.className = "p-3 border rounded shadow-sm mb-2 position-relative";
                cardTx.style.backgroundColor = "#f0fdf4";
                cardTx.style.borderColor = "#bbf7d0";
                
                cardTx.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="badge bg-success" style="font-size: 11px;">${tx.data}</span>
                        <strong class="text-success" style="font-size: 16px;">R$ ${valorTxFloat.toFixed(2)}</strong>
                    </div>
                    <p class="small text-muted mb-2 fw-medium">${tx.descricao}</p>
                    <div class="d-flex align-items-center gap-1 text-success fw-bold small mt-3">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
                        </svg>
                        Esta transação já foi conciliada.
                    </div>
                `;
                containerOfx.appendChild(cardTx);
                return; // Pula a criação do dropdown de associação para este item
            }

            // --- FLUXO DE COMPARAÇÃO / SUGESTÃO DE CONTAS EM ABERTO ---
            let contaMatchSugerido = contasGlobais.find(conta => {
                const valorContaFloat = parseFloat(conta.valor) || 0;
                const valorIdentico = Math.abs(valorContaFloat - valorTxFloat) < 0.01;
                
                const dataTx = parseDataBr(tx.data);
                const dataConta = parseDataBr(conta.data_pagamento);
                
                let dataProxima = false;
                if (dataTx && dataConta) {
                    const diffTime = Math.abs(dataTx - dataConta);
                    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                    dataProxima = diffDays <= 5;
                }
                return valorIdentico && dataProxima;
            });

            let opcoesDropdown = `<option value="">-- Deixar sem associação --</option>`;
            contasGlobais.forEach(conta => {
                const selecionado = (contaMatchSugerido && contaMatchSugerido.id === conta.id) ? 'selected' : '';
                const valorContaFloat = parseFloat(conta.valor) || 0;
                opcoesDropdown += `<option value="${conta.id}" ${selecionado}>${conta.fornecedor} (R$ ${valorContaFloat.toFixed(2)}) - ${conta.data_pagamento}</option>`;
            });

            const cardTx = document.createElement('div');
            cardTx.className = "p-3 border rounded shadow-sm bg-light position-relative mb-2";
            cardTx.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="badge bg-secondary">${tx.data}</span>
                    <strong class="text-danger" style="font-size: 16px;">R$ ${valorTxFloat.toFixed(2)}</strong>
                </div>
                <p class="small text-muted mb-2 fw-medium">${tx.descricao}</p>
                <div class="mt-2">
                    <label class="form-label small fw-bold text-secondary mb-1">Vincular a qual conta paga do sistema?</label>
                    <select class="form-select select-vinculo-lote form-select-sm" data-extrato-id="${tx.id}" style="border-radius: 6px;">
                        ${opcoesDropdown}
                    </select>
                </div>
            `;
            containerOfx.appendChild(cardTx);
        });

        if (contasGlobais.length === 0) {
            containerSistema.innerHTML = '<div class="alert alert-warning">Nenhuma conta com status "Pago" encontrada no sistema para este banco.</div>';
        } else {
            contasGlobais.forEach(conta => {
                const cardConta = document.createElement('div');
                cardConta.className = "p-3 border rounded shadow-sm bg-white mb-2";
                const valorContaFloat = parseFloat(conta.valor) || 0;
                cardConta.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-dark">${conta.fornecedor}</strong>
                        <span class="fw-bold text-dark">R$ ${valorContaFloat.toFixed(2)}</span>
                    </div>
                    <div class="text-muted small">Data Pagamento/Vencimento: <span class="fw-semibold text-primary">${conta.data_pagamento}</span></div>
                `;
                containerSistema.appendChild(cardConta);
            });
        }
    }

    const btnGravarLote = document.getElementById('btnGravarLote');
    if (btnGravarLote) {
        btnGravarLote.addEventListener('click', function() {
            const dropdowns = document.querySelectorAll('.select-vinculo-lote');
            const vinculosParaEnviar = [];

            dropdowns.forEach(select => {
                const contaId = select.value;
                const extratoId = select.getAttribute('data-extrato-id');
                if (contaId) {
                    vinculosParaEnviar.push({
                        conta_id: contaId,
                        extrato_id: extratoId
                    });
                }
            });

            if (vinculosParaEnviar.length === 0) {
                alert('Nenhum vínculo foi selecionado nos dropdowns.');
                return;
            }

            fetch(window.urlGravarLote, { 
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    banco: bancoAtivo,
                    vinculos: vinculosParaEnviar
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Auditoria em lote realizada com sucesso!');
                    window.location.reload();
                } else {
                    alert('Erro ao gravar lote: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro de comunicação na gravação do lote.');
            });
        });
    }
});