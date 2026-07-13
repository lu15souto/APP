import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
from sklearn.cluster import KMeans
from .graficos_common import plotly_fig, configurar_layout

def sazonalidade_tendencia(renda, despesas, meses):
    saldo = renda - despesas
    df = pd.DataFrame({'Saldo': saldo}, index=pd.to_datetime(meses, format='%b/%Y'))
    df['Média Móvel 3m'] = df['Saldo'].rolling(window=3).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Saldo'], mode='lines+markers', name='Saldo mensal', opacity=0.5))
    fig.add_trace(go.Scatter(x=df.index, y=df['Média Móvel 3m'], mode='lines', name='Tendência (média 3 meses)', line=dict(color='red', width=3)))
    configurar_layout(fig, 'Sazonalidade e Tendência', xlabel='Mês', ylabel='Saldo (R$)')
    plotly_fig(fig)

def meses_criticos(renda, despesas, saldo_inicial, meses):
    saldos = []
    saldo = saldo_inicial
    criticos = []
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldos.append(saldo)
        if saldo < 0:
            criticos.append((meses[i], saldo))
    if criticos:
        st.warning(f"Meses críticos (saldo negativo): {len(criticos)} ocorrências.")
        df_crit = pd.DataFrame(criticos, columns=['Mês', 'Déficit (R$)'])
        st.dataframe(df_crit.style.format({'Déficit (R$)': 'R$ {:,.2f}'}))
        deficits = [abs(s) for _, s in criticos]
        st.info(f"💡 Seria necessário um aporte extra de R$ {max(deficits):,.2f} no mês mais crítico.")
    else:
        st.success("Nenhum mês crítico identificado.")

def detectar_outliers(df, categorias_despesas, meses):
    outliers = {}
    for cat in categorias_despesas:
        serie = df.loc[cat].abs()
        if len(serie) > 1:
            z = np.abs(stats.zscore(serie))
            limiar = 2.5
            idx_out = np.where(z > limiar)[0]
            if len(idx_out) > 0:
                outliers[cat] = [(meses[i], serie.iloc[i]) for i in idx_out]
    if outliers:
        st.subheader("🔍 Gastos Atípicos Detectados")
        for cat, lista in outliers.items():
            st.write(f"**{cat}** – valores acima do normal:")
            for mes, valor in lista:
                st.write(f"- {mes}: R$ {valor:,.2f}")
    else:
        st.info("Nenhum gasto atípico identificado.")

def clusterizar_meses(renda, despesas, meses):
    saldo = renda - despesas
    despesas_totais = despesas
    X = np.column_stack((saldo, despesas_totais))
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    df_cluster = pd.DataFrame({'Mês': meses, 'Saldo': saldo, 'Despesas': despesas_totais, 'Cluster': labels})
    st.subheader("📌 Agrupamento de Meses (K-Means)")
    fig = px.scatter(df_cluster, x='Despesas', y='Saldo', color='Cluster', 
                     title='Clusters de meses', labels={'Despesas': 'Despesas Totais (R$)', 'Saldo': 'Saldo (R$)'})
    plotly_fig(fig)
    st.dataframe(df_cluster)