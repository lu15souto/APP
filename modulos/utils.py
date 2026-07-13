import io
import pandas as pd

def gerar_modelo_excel():
    """Gera um arquivo Excel modelo com as colunas esperadas."""
    categorias = ['Empréstimo', 'Cartão', 'Luz', 'Internet', 'Água', 'Aluguel', 'Renda']
    meses = pd.date_range(start='2026-01-01', periods=36, freq='MS').strftime('%b/%Y')
    df_modelo = pd.DataFrame(0, index=categorias, columns=meses)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, sheet_name='Folha1')
    return output.getvalue()