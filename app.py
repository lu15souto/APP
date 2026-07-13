import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Analisador de Empréstimos", layout="wide")
st.title("📊 Analisador de Empréstimos Inteligente")
st.markdown("---")

# =============================================================================
# Funções auxiliares
# =============================================================================
def gerar_modelo_excel():
    """Gera um arquivo Excel modelo com as colunas esperadas."""
    # Cria um DataFrame vazio com as categorias padrão
    categorias = ['Empréstimo', 'Cartão', 'Luz', 'Internet', 'Água', 'Aluguel', 'Renda']
    meses = pd.date_range(start='2026-01-01', periods=36, freq='MS').strftime('%b/%Y')
    df_modelo = pd.DataFrame(0, index=categorias, columns=meses)
    # Preenche com alguns valores de exemplo para ajudar
    #df_modelo.loc['Renda'] = [2000] * 36
    #df_modelo.loc['Aluguel'] = [-800] * 36
    #df_modelo.loc['Internet'] = [-30] * 36
    # Salva em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelo.to_excel(writer, sheet_name='Folha1')
    return output.getvalue()

def simular_fluxo(renda, despesas, parcela, valor_emp, saldo_ini):
    saldo = saldo_ini + valor_emp
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldo -= parcela
        if saldo < 0:
            return saldo, False
    return saldo, True

# =============================================================================
# Sidebar: Upload e parâmetros
# =============================================================================
st.sidebar.header("📁 Dados e Parâmetros")

# Download do modelo
st.sidebar.download_button(
    label="📥 Baixar modelo de planilha",
    data=gerar_modelo_excel(),
    file_name="modelo_emprestimo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Upload do arquivo do usuário
uploaded_file = st.sidebar.file_uploader("Faça o upload da sua planilha (.xlsx)", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuração do Empréstimo")

taxa = st.sidebar.number_input("Taxa de juros mensal (%)", min_value=0.0, max_value=100.0, value=3.45, step=0.05) / 100
gasto_variavel = st.sidebar.number_input("Gastos variáveis adicionais (R$)", min_value=0.0, value=0.0, step=50.0)
saldo_inicial = st.sidebar.number_input("Saldo inicial (R$)", min_value=0.0, value=0.0, step=100.0)
prazo_max = st.sidebar.number_input("Prazo máximo (meses)", min_value=1, max_value=120, value=12, step=1)
valor_maximo = st.sidebar.number_input("Valor máximo a contratar (R$)", min_value=1.0, value=50000.0, step=1000.0)
passo = st.sidebar.selectbox("Precisão da simulação (passo em R$)", [1, 10, 50, 100, 500, 1000], index=1)

# =============================================================================
# Processamento principal
# =============================================================================
if uploaded_file is not None:
    try:
        # Leitura do arquivo
        df_raw = pd.read_excel(uploaded_file, index_col=0, header=0, engine='openpyxl')
        df_raw.columns = [pd.to_datetime(col).strftime('%b/%Y') for col in df_raw.columns]
        df = df_raw.map(lambda x: pd.to_numeric(x, errors='coerce') if not isinstance(x, (int, float)) else x)
        df = df.fillna(0)

        st.success("✅ Planilha carregada com sucesso!")
        st.subheader("📋 Dados carregados")
        st.dataframe(df.style.format("{:,.2f}"))

        # Cálculo das médias
        categoria_renda = 'Renda'
        categorias_despesas = [cat for cat in df.index if cat not in [categoria_renda, 'Total', 'Total Agregado', 'Planejamento']]
        renda_media = df.loc[categoria_renda].mean()
        despesas_medias = abs(df.loc[categorias_despesas]).sum(axis=0).mean()
        saldo_medio = renda_media - despesas_medias

        st.subheader("📈 Resumo Financeiro Médio")
        col1, col2, col3 = st.columns(3)
        col1.metric("Renda média mensal", f"R$ {renda_media:,.2f}")
        col2.metric("Despesas médias mensais", f"R$ {despesas_medias:,.2f}")
        col3.metric("Saldo médio mensal", f"R$ {saldo_medio:,.2f}")

        # Preparar dados para simulação
        meses = df.columns.tolist()
        renda_real = df.loc[categoria_renda].values
        despesas_totais = abs(df.loc[categorias_despesas].sum(axis=0).values)
        despesas_totais_com_variavel = despesas_totais + gasto_variavel

        # Verificar necessidade de empréstimo
        saldo_sem_emp = saldo_inicial
        for i in range(len(renda_real)):
            saldo_sem_emp += renda_real[i] - despesas_totais_com_variavel[i]
            if saldo_sem_emp < 0:
                st.warning(f"⚠️ Sem empréstimo, o saldo fica negativo em {meses[i]}. Você precisa de um empréstimo.")
                break
        else:
            st.success("✅ Sem empréstimo, o saldo nunca fica negativo. Você não precisa de empréstimo, mas ainda assim pode simular.")

        # Simulação
        with st.spinner("🔄 Simulando cenários... Isso pode levar alguns segundos."):
            valores_teste = np.arange(1, valor_maximo + 1, passo)
            resultados = []
            for prazo in range(1, prazo_max + 1):
                for valor_emp in valores_teste:
                    if taxa == 0:
                        parcela = valor_emp / prazo
                    else:
                        parcela = valor_emp * (taxa * (1 + taxa)**prazo) / ((1 + taxa)**prazo - 1)
                    saldo_final, viavel = simular_fluxo(renda_real, despesas_totais_com_variavel, parcela, valor_emp, saldo_inicial)
                    if viavel:
                        custo_total = parcela * prazo
                        juros_total = custo_total - valor_emp
                        resultados.append({
                            'Prazo (meses)': prazo,
                            'Valor Empréstimo': valor_emp,
                            'Parcela': parcela,
                            'Custo Total': custo_total,
                            'Juros Total': juros_total,
                            'Juros %': (juros_total / valor_emp) * 100 if valor_emp > 0 else 0,
                            'Saldo Final': saldo_final
                        })
            df_resultados = pd.DataFrame(resultados)

        if len(df_resultados) == 0:
            st.error("❌ Nenhum cenário viável encontrado. Tente ajustar os parâmetros.")
            # Calcular déficit máximo e sugerir valor
            saldo = saldo_inicial
            deficit_max = 0
            for i in range(len(renda_real)):
                saldo += renda_real[i] - despesas_totais_com_variavel[i]
                if saldo < deficit_max:
                    deficit_max = saldo
            if deficit_max < 0:
                st.info(f"💡 Você precisaria de pelo menos R$ {-deficit_max:,.2f} de empréstimo para zerar o déficit máximo.")
        else:
            st.success(f"✅ Encontrados {len(df_resultados)} cenários viáveis.")

            # Melhor cenário (menor juros total)
            melhor = df_resultados.loc[df_resultados['Juros Total'].idxmin()]
            st.subheader("🏆 Melhor Cenário (menor custo com juros)")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Valor Empréstimo", f"R$ {melhor['Valor Empréstimo']:,.2f}")
            col2.metric("Prazo", f"{melhor['Prazo (meses)']} meses")
            col3.metric("Parcela", f"R$ {melhor['Parcela']:,.2f}")
            col4.metric("Juros Total", f"R$ {melhor['Juros Total']:,.2f} ({melhor['Juros %']:.2f}%)")

            # Tabela de cenários - mostrando apenas as 10 melhores e 10 piores
            st.subheader("📊 Tabela de Cenários Viáveis (10 melhores e 10 piores por juros)")
            
            df_ordenado = df_resultados.sort_values('Juros Total')
            melhores_10 = df_ordenado.head(10)
            piores_10 = df_ordenado.tail(10)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 🟢 10 Melhores (menor juros)")
                st.dataframe(melhores_10.style.format({
                    'Valor Empréstimo': 'R$ {:,.2f}',
                    'Parcela': 'R$ {:,.2f}',
                    'Custo Total': 'R$ {:,.2f}',
                    'Juros Total': 'R$ {:,.2f}',
                    'Juros %': '{:.2f}%',
                    'Saldo Final': 'R$ {:,.2f}'
                }))
            with col2:
                st.markdown("#### 🔴 10 Piores (maior juros)")
                st.dataframe(piores_10.style.format({
                    'Valor Empréstimo': 'R$ {:,.2f}',
                    'Parcela': 'R$ {:,.2f}',
                    'Custo Total': 'R$ {:,.2f}',
                    'Juros Total': 'R$ {:,.2f}',
                    'Juros %': '{:.2f}%',
                    'Saldo Final': 'R$ {:,.2f}'
                }))

            # =========================================================================
            # GRÁFICOS
            # =========================================================================
            st.subheader("📈 Análise Gráfica dos Resultados")

            def plot_grafico(fig):
                st.pyplot(fig)
                plt.close(fig)

            # Gráfico 1: Boxplot Juros por Prazo
            fig1, ax1 = plt.subplots(figsize=(12,6))
            sns.boxplot(data=df_resultados, x='Prazo (meses)', y='Juros Total', palette='Blues', ax=ax1)
            ax1.axhline(y=melhor['Juros Total'], color='red', linestyle='--', linewidth=2,
                        label=f'Melhor Juros: R$ {melhor["Juros Total"]:,.2f}')
            ax1.set_xlabel('Prazo (meses)')
            ax1.set_ylabel('Juros Total (R$)')
            ax1.set_title('Distribuição de Juros Total por Prazo')
            ax1.legend()
            ax1.grid(True)
            plot_grafico(fig1)

            # Gráfico 2: Custo Total vs Valor Empréstimo
            fig2, ax2 = plt.subplots(figsize=(12,6))
            sns.scatterplot(data=df_resultados, x='Valor Empréstimo', y='Custo Total',
                            hue='Prazo (meses)', palette='plasma', alpha=0.7, ax=ax2)
            ax2.scatter(melhor['Valor Empréstimo'], melhor['Custo Total'], color='red', s=250, marker='*',
                        label=f'Melhor (Custo Total: R$ {melhor["Custo Total"]:,.2f})', edgecolors='black', linewidth=1.5)
            ax2.set_xlabel('Valor Empréstimo (R$)')
            ax2.set_ylabel('Custo Total (R$)')
            ax2.set_title('Custo Total vs Valor Empréstimo (por prazo)')
            ax2.legend(title='Prazo (meses)')
            ax2.grid(True)
            plot_grafico(fig2)

            # Gráfico 3: Parcela vs Valor Empréstimo (linhas)
            fig3, ax3 = plt.subplots(figsize=(12,6))
            for prazo in sorted(df_resultados['Prazo (meses)'].unique()):
                subset = df_resultados[df_resultados['Prazo (meses)'] == prazo]
                ax3.plot(subset['Valor Empréstimo'], subset['Parcela'], marker='o', label=f'{prazo} meses', alpha=0.7)
            ax3.scatter(melhor['Valor Empréstimo'], melhor['Parcela'], color='red', s=250, marker='*',
                        label=f'Melhor (Parcela: R$ {melhor["Parcela"]:,.2f})', edgecolors='black', linewidth=1.5)
            ax3.set_xlabel('Valor Empréstimo (R$)')
            ax3.set_ylabel('Parcela (R$)')
            ax3.set_title('Parcela vs Valor Empréstimo por Prazo')
            ax3.legend()
            ax3.grid(True)
            plot_grafico(fig3)

            # Gráfico 4: Evolução do saldo mensal para o melhor cenário
            def calcular_saldo_mensal(renda, despesas, parcela, valor_emp, saldo_ini):
                saldo = saldo_ini + valor_emp
                saldos = [saldo]
                for i in range(len(renda)):
                    saldo += renda[i] - despesas[i]
                    saldo -= parcela
                    saldos.append(saldo)
                return saldos

            saldos_melhor = calcular_saldo_mensal(renda_real, despesas_totais_com_variavel,
                                                  melhor['Parcela'], melhor['Valor Empréstimo'], saldo_inicial)
            meses_labels = ['Início'] + meses

            fig4, ax4 = plt.subplots(figsize=(12,6))
            ax4.plot(meses_labels, saldos_melhor, marker='o', color='green', linewidth=2, markersize=8)
            ax4.axhline(y=0, color='red', linestyle='--', linewidth=1.5)
            ax4.set_xlabel('Período')
            ax4.set_ylabel('Saldo (R$)')
            ax4.set_title(f'Evolução do Saldo para o Melhor Cenário\n(Valor: R$ {melhor["Valor Empréstimo"]:,.2f} | Prazo: {melhor["Prazo (meses)"]} meses | Parcela: R$ {melhor["Parcela"]:,.2f})')
            ax4.tick_params(axis='x', rotation=45)
            ax4.grid(True)
            fig4.tight_layout()
            plot_grafico(fig4)

            st.success("🎉 Análise concluída! Os gráficos acima comprovam a escolha do melhor empréstimo.")

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")

else:
    st.info("👈 Faça o upload da sua planilha no menu lateral para começar.")
    st.markdown("""
    ### Como usar:
    1. **Baixe o modelo de planilha** clicando no botão acima.
    2. Preencha com seus dados (renda, despesas, etc.) seguindo o formato.
    3. Faça o upload da planilha preenchida.
    4. Configure os parâmetros do empréstimo (taxa, prazo, valor máximo).
    5. Aguarde a simulação e veja os resultados completos!
    """)