from django import template

register = template.Library()

@register.filter(name='moeda_br')
def moeda_br(valor):
    """
    Transforma qualquer número (float, int, decimal) no formato R$ 111.111,11
    """
    if valor is None or valor == '':
        return "R$ 0,00"
    
    try:
        # Força o valor a ser um float
        valor_float = float(valor)
        
        # Formata no padrão americano com duas casas decimais: 111,111.11
        texto_formatado = f"{valor_float:,.2f}"
        
        # Inverte os pontos e vírgulas para o padrão brasileiro
        texto_br = texto_formatado.replace(",", "_").replace(".", ",").replace("_", ".")
        
        # CORREÇÃO: Adicionado o R$ aqui antes da string formatada
        return f"R$ {texto_br}"
    except (ValueError, TypeError):
        # Caso ocorra um erro, retorna o valor original com o R$ (ou trate como preferir)
        return f"R$ {valor}"