from django import template

register = template.Library()

@register.filter(name='moeda_br')
def moeda_br(valor):
    """
    Transforma qualquer número (float, int, decimal) no formato 111.111,11
    """
    if valor is None or valor == '':
        return " 0,00"
    
    try:
        # Força o valor a ser um float
        valor_float = float(valor)
        
        # Formata primeiro no padrão americano com 2 casas: 111,111.11
        texto_formatado = f"{valor_float:,.2f}"
        
        # Inverte os pontos e vírgulas para o padrão brasileiro
        texto_br = texto_formatado.replace(",", "_").replace(".", ",").replace("_", ".")
        
        return f" {texto_br}"
    except (ValueError, TypeError):
        return f" {valor}"