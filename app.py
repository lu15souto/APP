import streamlit as st
import pandas as pd
import numpy as np

from modulos.utils import gerar_modelo_excel
from modulos.diagnostico import (
    resumo_financeiro, evolucao_saldo, radar_categorias,
    classificar_50_30_20, burn_rate, diagrama_sankey
)
from modulos.temporal import (
    sazonalidade_tendencia, meses_criticos, detectar_outliers, clusterizar_meses
)
from modulos.simulacoes import (
    simulador_poupanca, simulador_cenarios, meta_emergencia,
    stress_test, previsao_gastos, aposentadoria
)
from modulos.recomendacoes import (
    recomendar_reducao_gastos, sugestao_plano_internet,
    editor_categorias, gerar_relatorio_pdf
)
from modulos.emprestimo import (
    analise_risco, criar_boxplot_juros_plotly, criar_scatter_custo_plotly,
    criar_parcela_vs_valor_plotly, criar_saldo_mensal_plotly
)
from modulos.simulacao import simular_fluxo, calcular_saldo_mensal
from modulos.graficos_common import plotly_fig

st.set_page_config(page_title="Analisador Financeiro Completo", layout="wide")
st.title("📊 Analisador Financeiro Inteligente")
st.markdown("---")

st.sidebar.header("📁 Dados e Parâmetros")
st.sidebar.download_button(
    label="📥 Baixar modelo de planilha",
    data=gerar_modelo_excel(),
    file_name="modelo_emprestimo.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uploaded_file = st.sidebar.file_uploader("Faça o upload da sua planilha (.xlsx)", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuração do Empréstimo (aba específica)")

taxa = st.sidebar.number_input("Taxa de juros mensal (%)", min_value=0.0, max_value=100.0, value=3.45, step=0.05) / 100
gasto_variavel = st.sidebar.number_input("Gastos variáveis adicionais (R$)", min_value=0.0, value=0.0, step=50.0)
saldo_inicial = st.sidebar.number_input("Saldo inicial (R$)", min_value=0.0, value=0.0, step=100.0)
prazo_max = st.sidebar.number_input("Prazo máximo (meses)", min_value=1, max_value=120, value=12, step=1)
valor_maximo = st.sidebar.number_input("Valor máximo a contratar (R$)", min_value=1.0, value=50000.0, step=1000.0)
passo = st.sidebar.selectbox("Precisão da simulação (passo em R$)", [1, 10, 50, 100, 500, 1000], index=1)

if uploaded_file is not None:
    try:
        df_raw = pd.read_excel(uploaded_file, index_col=0, header=0, engine='openpyxl')
        df_raw.columns = [pd.to_datetime(col).strftime('%b/%Y') for col in df_raw.columns]
        df = df_raw.map(lambda x: pd.to_numeric(x, errors='coerce') if not isinstance(x, (int, float)) else x)
        df = df.fillna(0)

        st.success("✅ Planilha carregada com sucesso!")
        st.subheader("📋 Dados carregados")
        st.dataframe(df.style.format("{:,.2f}"))

        categoria_renda = 'Renda'
        categorias_despesas = [cat for cat in df.index if cat not in [categoria_renda, 'Total', 'Total Agregado', 'Planejamento']]
        meses = df.columns.tolist()
        renda_real = df.loc[categoria_renda].values
        despesas_totais = abs(df.loc[categorias_despesas].sum(axis=0).values)
        despesas_totais_com_variavel = despesas_totais + gasto_variavel

        aba1, aba2, aba3, aba4, aba5 = st.tabs([
            "📊 Painel Geral",
            "📅 Análise Temporal",
            "🧪 Simulações",
            "💡 Recomendações",
            "🏦 Empréstimo"
        ])

        with aba1:
            st.header("📊 Diagnóstico Financeiro")
            renda_media, despesas_media, saldo_medio = resumo_financeiro(df, categoria_renda, categorias_despesas)
            evolucao_saldo(renda_real, despesas_totais_com_variavel, saldo_inicial, meses)
            radar_categorias(df, categorias_despesas)
            classificar_50_30_20(df, categoria_renda, categorias_despesas)
            burn_rate(renda_real, despesas_totais_com_variavel, saldo_inicial)
            diagrama_sankey(df, categoria_renda, categorias_despesas)

        with aba2:
            st.header("📅 Análise Temporal e Padrões")
            sazonalidade_tendencia(renda_real, despesas_totais_com_variavel, meses)
            meses_criticos(renda_real, despesas_totais_com_variavel, saldo_inicial, meses)
            detectar_outliers(df, categorias_despesas, meses)
            clusterizar_meses(renda_real, despesas_totais_com_variavel, meses)

        with aba3:
            st.header("🧪 Simulações e Planejamento")
            simulador_poupanca(renda_real, despesas_totais_com_variavel, saldo_inicial, meses)
            simulador_cenarios(renda_real, despesas_totais_com_variavel, meses, categorias_despesas)
            meta_emergencia(despesas_totais_com_variavel, saldo_inicial, renda_real, meses)
            stress_test(renda_real, despesas_totais_com_variavel, saldo_inicial, meses)
            previsao_gastos(despesas_totais_com_variavel, meses)
            aposentadoria(saldo_inicial, renda_real, despesas_totais_com_variavel, meses)

        with aba4:
            st.header("💡 Recomendações e Ações")
            recomendar_reducao_gastos(df, categorias_despesas, renda_media)
            sugestao_plano_internet(df)
            editor_categorias(df)
            st.subheader("📄 Exportar Relatório")
            gerar_relatorio_pdf(df, renda_real, despesas_totais_com_variavel, meses)

        with aba5:
            st.header("🏦 Análise de Crédito e Empréstimo")
            analise_risco(renda_real, despesas_totais_com_variavel, saldo_inicial)
            st.markdown("---")
            st.subheader("Simulação de Empréstimo")

            # Verifica se precisa de empréstimo
            saldo_sem_emp = saldo_inicial
            for i in range(len(renda_real)):
                saldo_sem_emp += renda_real[i] - despesas_totais_com_variavel[i]
                if saldo_sem_emp < 0:
                    st.warning(f"⚠️ Sem empréstimo, o saldo fica negativo em {meses[i]}. Você precisa de um empréstimo.")
                    break
            else:
                st.success("✅ Sem empréstimo, o saldo nunca fica negativo. Você não precisa de empréstimo, mas ainda assim pode simular.")

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
                melhor = df_resultados.loc[df_resultados['Juros Total'].idxmin()]
                st.subheader("🏆 Melhor Cenário (menor custo com juros)")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Valor Empréstimo", f"R$ {melhor['Valor Empréstimo']:,.2f}")
                col2.metric("Prazo", f"{melhor['Prazo (meses)']} meses")
                col3.metric("Parcela", f"R$ {melhor['Parcela']:,.2f}")
                col4.metric("Juros Total", f"R$ {melhor['Juros Total']:,.2f} ({melhor['Juros %']:.2f}%)")

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

                st.subheader("📈 Análise Gráfica dos Resultados")
                fig1 = criar_boxplot_juros_plotly(df_resultados, melhor)
                plotly_fig(fig1)
                fig2 = criar_scatter_custo_plotly(df_resultados, melhor)
                plotly_fig(fig2)
                fig3 = criar_parcela_vs_valor_plotly(df_resultados, melhor)
                plotly_fig(fig3)
                saldos_melhor = calcular_saldo_mensal(
                    renda_real, despesas_totais_com_variavel,
                    melhor['Parcela'], melhor['Valor Empréstimo'], saldo_inicial
                )
                meses_labels = ['Início'] + meses
                fig4 = criar_saldo_mensal_plotly(meses_labels, saldos_melhor, melhor)
                plotly_fig(fig4)
                st.success("🎉 Análise concluída! Os gráficos acima comprovam a escolha do melhor empréstimo.")

    except Exception as e:
        st.error(f"❌ Erro ao processar o arquivo: {e}")
else:
    st.info("👈 Faça o upload da sua planilha no menu lateral para começar.")
    st.markdown("""
    ### Como usar:
    1. Baixe o modelo de planilha.
    2. Preencha com seus dados (renda, despesas).
    3. Faça o upload.
    4. Navegue pelas abas para análises, simulações e recomendações.
    """)
