import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from .simulacao import simular_fluxo, calcular_saldo_mensal
from .graficos_common import plotly_fig, configurar_layout

def analise_risco(renda, despesas, saldo_inicial):
    saldos = []
    saldo = saldo_inicial
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldos.append(saldo)
    if len(saldos) > 1:
        desvio = np.std(saldos)
        media_saldo = np.mean(saldos)
        if min(saldos) < 0:
            st.error(f"⚠️ Risco de inadimplência ALTO: saldo mínimo de R$ {min(saldos):,.2f}")
        elif desvio > (media_saldo * 0.3):
            st.warning(f"⚠️ Risco médio: variabilidade de saldo elevada (desvio R$ {desvio:,.2f})")
        else:
            st.success("✅ Risco baixo: saldo estável e positivo.")
    else:
        st.info("Dados insuficientes para análise de risco.")

def criar_boxplot_juros_plotly(df_resultados, melhor):
    fig = px.box(df_resultados, x='Prazo (meses)', y='Juros Total', color='Prazo (meses)',
                 title='Distribuição de Juros Total por Prazo',
                 labels={'Juros Total': 'Juros Total (R$)'})
    fig.add_hline(y=melhor['Juros Total'], line_dash="dash", line_color="red",
                  annotation_text=f'Melhor: R$ {melhor["Juros Total"]:,.2f}')
    fig.update_layout(showlegend=False, template='plotly_white')
    return fig

def criar_scatter_custo_plotly(df_resultados, melhor):
    fig = px.scatter(df_resultados, x='Valor Empréstimo', y='Custo Total', 
                     color='Prazo (meses)', title='Custo Total vs Valor Empréstimo',
                     labels={'Valor Empréstimo': 'Valor Empréstimo (R$)', 'Custo Total': 'Custo Total (R$)'})
    fig.add_trace(go.Scatter(x=[melhor['Valor Empréstimo']], y=[melhor['Custo Total']],
                             mode='markers', marker=dict(size=15, color='red', symbol='star'),
                             name='Melhor'))
    return fig

def criar_parcela_vs_valor_plotly(df_resultados, melhor):
    fig = go.Figure()
    for prazo in sorted(df_resultados['Prazo (meses)'].unique()):
        subset = df_resultados[df_resultados['Prazo (meses)'] == prazo]
        fig.add_trace(go.Scatter(x=subset['Valor Empréstimo'], y=subset['Parcela'],
                                 mode='lines+markers', name=f'{prazo} meses'))
    fig.add_trace(go.Scatter(x=[melhor['Valor Empréstimo']], y=[melhor['Parcela']],
                             mode='markers', marker=dict(size=15, color='red', symbol='star'),
                             name='Melhor'))
    configurar_layout(fig, 'Parcela vs Valor Empréstimo por Prazo',
                      xlabel='Valor Empréstimo (R$)', ylabel='Parcela (R$)')
    return fig

def criar_saldo_mensal_plotly(meses_labels, saldos_melhor, melhor):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses_labels, y=saldos_melhor, mode='lines+markers',
                             name='Saldo', line=dict(color='green', width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    titulo = f'Evolução do Saldo para o Melhor Cenário<br>(Valor: R$ {melhor["Valor Empréstimo"]:,.2f} | Prazo: {melhor["Prazo (meses)"]} meses | Parcela: R$ {melhor["Parcela"]:,.2f})'
    configurar_layout(fig, titulo, xlabel='Período', ylabel='Saldo (R$)')
    return fig