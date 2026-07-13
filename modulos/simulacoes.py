import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from .graficos_common import plotly_fig, configurar_layout

def simulador_poupanca(renda, despesas, saldo_inicial, meses):
    valor_poup = st.slider("Quanto deseja poupar por mês (R$)?", 0, 5000, 500, step=50)
    if valor_poup == 0:
        return
    saldo = saldo_inicial
    saldos = []
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i] - valor_poup
        saldos.append(saldo)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses, y=saldos, mode='lines+markers', name='Saldo', line=dict(color='green')))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    configurar_layout(fig, f'Impacto da poupança de R$ {valor_poup:,.2f}/mês', xlabel='Mês', ylabel='Saldo (R$)')
    plotly_fig(fig)
    st.info(f"Saldo final após {len(meses)} meses: R$ {saldos[-1]:,.2f}")

def simulador_cenarios(renda, despesas, meses, categorias_despesas):
    st.subheader("🔧 Ajuste de Gastos")
    ajustes = {}
    for cat in categorias_despesas:
        ajustes[cat] = st.slider(f"Redução em {cat} (%)", -50, 50, 0, key=cat)
    despesas_ajustadas = despesas.copy()
    for i, cat in enumerate(categorias_despesas):
        if ajustes[cat] != 0:
            despesas_ajustadas += (despesas_ajustadas * (ajustes[cat] / 100))
    saldo = saldo_inicial
    saldos = []
    for i in range(len(renda)):
        saldo += renda[i] - despesas_ajustadas[i]
        saldos.append(saldo)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses, y=saldos, mode='lines+markers', name='Saldo ajustado', line=dict(color='purple')))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    configurar_layout(fig, 'Saldo com ajustes de gastos', xlabel='Mês', ylabel='Saldo (R$)')
    plotly_fig(fig)

def meta_emergencia(despesas, saldo_inicial, renda, meses):
    custo_mensal = despesas.mean()
    meta = custo_mensal * 6
    saldo_atual = saldo_inicial
    saldo_medio = renda.mean() - despesas.mean()
    if saldo_medio <= 0:
        st.warning("Com o saldo médio negativo, você não está acumulando reserva.")
        return
    meses_necessarios = (meta - saldo_atual) / saldo_medio
    if meses_necessarios <= 0:
        st.success(f"✅ Você já tem reserva para {meses_necessarios:.0f} meses!")
    else:
        st.info(f"⏳ Faltam aproximadamente {meses_necessarios:.0f} meses para atingir a meta de 6 meses de custo.")

def stress_test(renda, despesas, saldo_inicial, meses):
    meses_sem_renda = st.slider("Quantos meses sem renda?", 0, 12, 3)
    if meses_sem_renda == 0:
        return
    renda_ajustada = renda.copy()
    for i in range(min(meses_sem_renda, len(renda))):
        renda_ajustada[i] = 0
    saldo = saldo_inicial
    saldos = []
    for i in range(len(renda)):
        saldo += renda_ajustada[i] - despesas[i]
        saldos.append(saldo)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=meses, y=saldos, mode='lines+markers', name='Saldo sem renda', line=dict(color='darkred')))
    fig.add_hline(y=0, line_dash="dash", line_color="blue")
    configurar_layout(fig, f'Simulação: {meses_sem_renda} meses sem renda', xlabel='Mês', ylabel='Saldo (R$)')
    plotly_fig(fig)
    if min(saldos) < 0:
        st.error(f"⚠️ O saldo fica negativo em alguns meses. Você precisaria de R$ {-min(saldos):,.2f} para cobrir o déficit.")
    else:
        st.success("✅ Mesmo sem renda, seu saldo se mantém positivo.")

def previsao_gastos(despesas, meses):
    try:
        model = ExponentialSmoothing(despesas, trend='add', seasonal=None, seasonal_periods=None)
        fit = model.fit()
        pred = fit.forecast(1)[0]
        st.metric("Previsão de gastos para o próximo mês", f"R$ {pred:,.2f}")
        st.caption("Baseado em suavização exponencial (Holt-Winters simples).")
    except Exception as e:
        st.warning("Não foi possível fazer a previsão. Usando média simples.")
        pred = despesas.mean()
        st.metric("Previsão de gastos (média histórica)", f"R$ {pred:,.2f}")

def aposentadoria(saldo_inicial, renda, despesas, meses):
    taxa = st.slider("Taxa de retorno anual (%)", 0.0, 20.0, 5.0, step=0.5) / 100
    anos_ate_65 = st.number_input("Quantos anos até a aposentadoria?", min_value=1, max_value=50, value=30)
    poupanca_mensal = renda.mean() - despesas.mean()
    if poupanca_mensal < 0:
        st.warning("Você está gastando mais do que ganha. Não é possível poupar.")
        return
    meses_total = anos_ate_65 * 12
    montante = saldo_inicial
    for _ in range(meses_total):
        montante += poupanca_mensal
        montante *= (1 + taxa/12)
    st.metric("Montante acumulado na aposentadoria", f"R$ {montante:,.2f}")