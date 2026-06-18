import sqlite3
import pandas as pd


def importar_excel_para_sqlite(
    caminho_excel, nome_banco, nome_tabela, nome_aba=0
):
    conn = None
    try:
        # 1. Lê a planilha Excel usando o pandas
        # nome_aba=0 pega a primeira aba por padrão.
        df = pd.read_excel(caminho_excel, sheet_name=nome_aba)

        # Trata valores vazios/nulos do Excel para que o Python entenda como None (NULL no banco)
        df = df.where(pd.notnull(df), None)

        # 2. Conecta ao banco de dados SQLite
        conn = sqlite3.connect(nome_banco)
        cursor = conn.cursor()

        # 3. Define todas as colunas que a tabela do banco possui hoje no Django
        colunas = (
            "(vencimento, fornecedor, categoria, banco, valor, parcela, "
            "observacao, ultimo_pagamento, juros, status, conciliado)"
        )

        # 11 placeholders correspondentes às 11 colunas
        placeholders = "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        query = f"INSERT INTO {nome_tabela} {colunas} VALUES {placeholders};"

        registros_inseridos = 0

        print("Iniciando a leitura das linhas e conversão de dados...")

        # 4. Percorre cada linha da planilha Excel de forma dinâmica
        for index, linha in df.iterrows():

            # --- AJUSTE E MÁSCARA DA DATA ---
            # Converte '18/06/2026' (padrão BR) para um objeto de data e depois formata como '2026-06-18' (padrão SQLite/Django)
            data_formatada = pd.to_datetime(linha["vencimento"], dayfirst=True)
            vencimento = data_formatada.strftime("%Y-%m-%d")

            # Demais dados dinâmicos vindos do Excel
            fornecedor = linha["fornecedor"]
            categoria = linha["categoria"]
            banco = linha["banco"]
            valor = float(linha["valor"])

            # 5. Monta a tupla combinando os dados DINÂMICOS (Excel) com os DEFAULTS (Model)
            dados_registro = (
                vencimento,  # Dinâmico e Formatado (Ex: "2026-06-18")
                fornecedor,  # Dinâmico (Excel)
                categoria,  # Dinâmico (Excel)
                banco,  # Dinâmico (Excel)
                valor,  # Dinâmico (Excel)
                "1/1",  # default do model: parcela
                None,  # default do model: observacao (blank/null)
                None,  # default do model: ultimo_pagamento (blank/null)
                0.00,  # default do model: juros
                "Pendente",  # default do model: status
                "Não",  # default do model: conciliado
            )

            # Executa a inserção da linha atual na memória do cursor
            cursor.execute(query, dados_registro)
            registros_inseridos += 1

        # 6. Salva todas as inserções de uma vez só no banco de dados (Garante performance)
        conn.commit()

        print("---" * 15)
        print(
            f"Sucesso! {registros_inseridos} registros importados com sucesso para a tabela '{nome_tabela}'."
        )
        print("---" * 15)

    except Exception as e:
        # Se der qualquer erro no processo, desfaz o que foi feito para não corromper o banco
        if conn:
            conn.rollback()
        print(f"\n❌ Erro durante a importação: {e}")

    finally:
        if conn:
            conn.close()
            print("Conexão com o banco fechada.")


# --- CONFIGURAÇÃO E EXECUÇÃO ---
# 1. Coloque o nome/caminho correto do seu arquivo Excel aqui:
CAMINHO_EXCEL = "proj_leao/app_leao/bases_excel/up_finish.xlsx"

# 2. Seus caminhos de banco e tabela já configurados:
MEU_BANCO = "/workspaces/project_leaofin/proj_leao/db.sqlite3"
MINHA_TABELA = "app_leao_contapagar"

# Executa a função
importar_excel_para_sqlite(CAMINHO_EXCEL, MEU_BANCO, MINHA_TABELA)