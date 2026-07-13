import streamlit as st
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def recomendar_reducao_gastos(df, categorias_despesas, renda_media):
    st.subheader("💡 Recomendações de Redução de Gastos")
    for cat in categorias_despesas:
        media_cat = abs(df.loc[cat].mean())
        if media_cat / renda_media > 0.10:
            st.warning(f"⚠️ Gastos com **{cat}** representam {media_cat/renda_media:.1%} da renda. Considere reduzir em 10% (economia de R$ {media_cat*0.1:,.2f}/mês).")
        else:
            st.success(f"✅ Gastos com **{cat}** estão equilibrados ({media_cat/renda_media:.1%} da renda).")

def sugestao_plano_internet(df):
    gasto_internet = df.loc['Internet'].mean() if 'Internet' in df.index else 0
    gasto_celular = df.loc['Celular'].mean() if 'Celular' in df.index else 0
    total = gasto_internet + gasto_celular
    if total > 200:
        st.warning(f"Seu gasto com Internet + Celular é de R$ {total:.2f}/mês. Planos mais econômicos podem custar cerca de R$ 100/mês, gerando economia de R$ {total-100:.2f}/mês.")
    else:
        st.success("Seus gastos com comunicação estão dentro do esperado.")

def editor_categorias(df):
    st.subheader("✏️ Editor de Categorias")
    cat_selecionada = st.selectbox("Selecione a categoria para renomear:", df.index.tolist())
    novo_nome = st.text_input("Novo nome:", value=cat_selecionada)
    if st.button("Renomear"):
        if novo_nome and novo_nome != cat_selecionada:
            df.rename(index={cat_selecionada: novo_nome}, inplace=True)
            st.success("Categoria renomeada com sucesso!")
            st.rerun()

def gerar_relatorio_pdf(df, renda_real, despesas_totais, meses, melhor_emprestimo=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Relatório de Saúde Financeira")
    c.drawString(100, 730, f"Data: {pd.Timestamp.now().strftime('%d/%m/%Y')}")
    c.drawString(100, 700, f"Renda média: R$ {renda_real.mean():.2f}")
    c.drawString(100, 680, f"Despesas médias: R$ {despesas_totais.mean():.2f}")
    c.drawString(100, 660, f"Saldo médio: R$ {renda_real.mean() - despesas_totais.mean():.2f}")
    if melhor_emprestimo is not None:
        c.drawString(100, 640, f"Melhor empréstimo: R$ {melhor_emprestimo['Valor Empréstimo']:.2f} em {melhor_emprestimo['Prazo (meses)']} meses, parcela de R$ {melhor_emprestimo['Parcela']:.2f}")
    c.save()
    buffer.seek(0)
    st.download_button(
        label="📄 Baixar Relatório PDF",
        data=buffer,
        file_name="relatorio_financeiro.pdf",
        mime="application/pdf"
    )