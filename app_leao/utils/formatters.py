import re
from datetime import date, datetime
from decimal import Decimal
import openpyxl

def extrair_texto(celula):
    if celula is None:
        return ""
    return str(celula).strip()

def limpar_cnpj(val):
    return re.sub(r'\D', '', extrair_texto(val))

def formatar_cnpj(c):
    if len(c) == 14:
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"
    return c

def parse_valor(val):
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    texto = extrair_texto(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
    return Decimal(texto) if texto else Decimal('0.00')

def parse_data(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, (int, float)):
        try:
            return openpyxl.utils.datetime.from_excel(val).date()
        except Exception:
            pass
    texto = extrair_texto(val).split(' ')[0]
    formatos = [
        '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d.%m.%Y',
        '%d/%m/%y', '%Y/%m/%d', '%m/%d/%Y'
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            pass
    return None