import os
import sys
import django
from decimal import Decimal
import pandas as pd

# 1. CONFIGURAÇÃO DE AMBIENTE (Resolve o erro de ModuleNotFoundError)
# Descobre a pasta raiz do projeto (onde fica o manage.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Alerta o Django sobre qual é o arquivo de configurações do seu projeto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj_leao.settings')
django.setup()

# SÓ AGORA podemos importar o Model com segurança
from app_leao.models import ContaPagar

# 2. CARREGAMENTO DOS DADOS
caminho_excel = '/workspaces/project_leaofin/proj_leao/app_leao/bases_excel/up_fin.xlsx'
df = pd.read_excel(caminho_excel)

# Tratamento para garantir que células vazias do Excel não virem 'NaN' que quebram o banco
df = df.astype(object).where(pd.notnull(df), None)

# Ajuste da data para o formato aceito pelo Django DateField
df['Vencimento'] = pd.to_datetime(df['Vencimento']).dt.date

# 3. CONSTRUÇÃO DOS OBJETOS EM MEMÓRIA
objetos_para_salvar = []

for row in df.itertuples(index=False):
    # Usamos getattr(row, 'Nome', padrao) para evitar que o script quebre 
    # caso a coluna 'Parcela' ou 'Observação' não existam na planilha Excel.
    parcela_valor = getattr(row, 'Parcela', '1/1')
    obs_valor = getattr(row, 'Observação', None)
    
    # Se a coluna de observação no Excel se chamar apenas "Observacao" (sem acento):
    if obs_valor is None:
        obs_valor = getattr(row, 'Observacao', None)

    conta = ContaPagar(
        vencimento=row.Vencimento,    # Note a primeira letra Maiúscula!
        fornecedor=row.Fornecedor,    # Note a primeira letra Maiúscula!
        categoria=row.Categoria,      # Note a primeira letra Maiúscula!
        banco=row.Banco,              # Note a primeira letra Maiúscula!
        parcela=parcela_valor,
        valor=Decimal(str(row.Valor)), # Note a primeira letra Maiúscula!
        observacao=obs_valor
    )
    objetos_para_salvar.append(conta)

# 4. SALVAMENTO EM LOTE (BULK CREATE)
if objetos_para_salvar:
    ContaPagar.objects.bulk_create(objetos_para_salvar)
    print(f"Sucesso! {len(objetos_para_salvar)} registros incluídos no banco de dados.")
else:
    print("Nenhum registro encontrado para salvar.")