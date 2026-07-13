import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from .graficos_common import plotly_fig, configurar_layout

def resumo_financeiro(df, categoria_renda, categorias_despesas):
    renda_media = df.loc[categoria_renda].mean()
    despesas_media = abs(df.loc[categorias_despesas]).sum(axis=0).mean()
    saldo_medio = renda_media - despesas_media
    col1, col2, col3 = st.columns(3)
    col1.metric("Renda média mensal", f"R$ {renda_media:,.2f}")
    col2.metric("Despesas médias mensais", f"R$ {despesas_media:,.2f}")
    col3.metric("Saldo médio mensal", f"R$ {saldo_medio:,.2f}")
    return renda_media, despesas_media, saldo_medio

def evolucao_saldo(renda, despesas, saldo_inicial, meses):
    saldos = []
    saldo = saldo_inicial
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldos.append(saldo)
    df_saldo = pd.DataFrame({'Mês': meses, 'Saldo': saldos})
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_saldo['Mês'],
        y=df_saldo['Saldo'],
        fill='tozeroy',
        fillcolor='rgba(0,200,0,0.2)',
        line=dict(color='blue', width=2),
        name='Saldo'
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    configurar_layout(fig, 'Evolução do Saldo (sem empréstimo)', xlabel='Mês', ylabel='Saldo (R$)')
    plotly_fig(fig)

def radar_categorias(df, categorias_despesas):
    medias = abs(df.loc[categorias_despesas].mean())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=medias.values,
        theta=medias.index,
        fill='toself',
        name='Média de gastos'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title='Distribuição média de gastos por categoria',
        template='plotly_white'
    )
    plotly_fig(fig)

def classificar_50_30_20(df, categoria_renda, categorias_despesas):
    renda_media = df.loc[categoria_renda].mean()
    necessidades = [c for c in categorias_despesas if any(p in c for p in ['Aluguel', 'Luz', 'Água'])]
    desejos = [c for c in categorias_despesas if c not in necessidades]
    gasto_necessidades = abs(df.loc[necessidades]).sum(axis=0).mean() if necessidades else 0
    gasto_desejos = abs(df.loc[desejos]).sum(axis=0).mean() if desejos else 0
    poupanca = renda_media - gasto_necessidades - gasto_desejos
    if poupanca < 0:
        poupanca = 0
    pct_necess = (gasto_necessidades / renda_media) * 100 if renda_media > 0 else 0
    pct_desejos = (gasto_desejos / renda_media) * 100 if renda_media > 0 else 0
    pct_poup = (poupanca / renda_media) * 100 if renda_media > 0 else 0
    st.markdown("#### 🧾 Classificação 50/30/20")
    col1, col2, col3 = st.columns(3)
    col1.metric("Necessidades", f"{pct_necess:.1f}%", delta=f"R$ {gasto_necessidades:,.2f}")
    col2.metric("Desejos", f"{pct_desejos:.1f}%", delta=f"R$ {gasto_desejos:,.2f}")
    col3.metric("Poupança", f"{pct_poup:.1f}%", delta=f"R$ {poupanca:,.2f}")
    if pct_necess <= 50 and pct_desejos <= 30 and pct_poup >= 20:
        st.success("✅ Sua saúde financeira está ÓTIMA! Continue assim.")
    elif pct_necess > 50:
        st.warning("⚠️ Você está gastando mais de 50% em necessidades. Tente reduzir custos fixos.")
    elif pct_desejos > 30:
        st.warning("⚠️ Seus gastos com desejos estão acima de 30%. Avalie cortar supérfluos.")
    else:
        st.info("ℹ️ Sua poupança está abaixo de 20%. Considere aumentar sua reserva.")

def burn_rate(renda, despesas, saldo_inicial):
    saldo = saldo_inicial
    saldos = []
    for i in range(len(renda)):
        saldo += renda[i] - despesas[i]
        saldos.append(saldo)
    if len(saldos) > 1:
        x = np.arange(len(saldos))
        coeffs = np.polyfit(x, saldos, 1)
        taxa = coeffs[0]
        st.metric("Taxa de Queima (variação mensal do saldo)", f"R$ {taxa:,.2f}/mês")
        if taxa < 0:
            st.warning(f"Seu saldo está diminuindo em média R$ {-taxa:,.2f} por mês.")
        else:
            st.success(f"Seu saldo está aumentando em média R$ {taxa:,.2f} por mês.")
    else:
        st.info("Dados insuficientes para calcular a taxa de queima.")

def diagrama_sankey(df, categoria_renda, categorias_despesas):
    renda_total = df.loc[categoria_renda].sum()
    despesas_totais = abs(df.loc[categorias_despesas].sum(axis=1))
    despesas_totais = despesas_totais[despesas_totais > (renda_total * 0.01)]
    labels = ['Renda'] + list(despesas_totais.index)
    source = [0] * len(despesas_totais)
    target = list(range(1, len(despesas_totais)+1))
    value = despesas_totais.values.tolist()
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color="blue"
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])
    fig.update_layout(title_text="Fluxo de Caixa (Renda → Despesas)", font_size=12)
    plotly_fig(fig)