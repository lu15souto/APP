import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

def plotly_fig(fig):
    """Exibe uma figura Plotly no Streamlit com largura total."""
    st.plotly_chart(fig, use_container_width=True)

def configurar_layout(fig, titulo, xlabel=None, ylabel=None, template='plotly_white'):
    """Aplica configurações comuns de layout."""
    fig.update_layout(
        title=titulo,
        xaxis_title=xlabel,
        yaxis_title=ylabel,
        template=template,
        hovermode='x unified'
    )
    return fig