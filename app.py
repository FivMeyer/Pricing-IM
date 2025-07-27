import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os

# ---------------------------------------
# Configurações da Página
# ---------------------------------------
st.set_page_config(
    page_title="Painel de Pricing - Yara",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------
# Funções de Apoio
# ---------------------------------------
@st.cache_data
def carregar_dados():
    # Carregar dados do arquivo Excel
    caminho = '_data/df_case.xlsx'
    
    # Verificar se o arquivo existe
    if not os.path.exists(caminho):
        st.error(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()
    
    try:
        df = pd.read_excel(caminho)
        
        # Verificar colunas essenciais
        colunas_necessarias = ['Data', 'Produto', 'Preço FOB ($/t)', 'CFR ($/t)']
        for col in colunas_necessarias:
            if col not in df.columns:
                st.error(f"Coluna obrigatória não encontrada: {col}")
                
        # Converter coluna Data para datetime
        if 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'])
            
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

def formatar_moeda(valor):
    return f"R${valor:,.2f}"

# ---------------------------------------
# Carregamento de Dados
# ---------------------------------------
df = carregar_dados()

# Verificar se os dados foram carregados corretamente
if df.empty:
    st.stop()

# ---------------------------------------
# Barra Lateral (Filtros)
# ---------------------------------------
with st.sidebar:
    st.image("https://www.yara.com/corporate/images/yara-logo.svg", width=150)
    st.title("Filtros")
    
    # Filtro de produtos
    produtos_disponiveis = df['Produto'].unique() if 'Produto' in df.columns else []
    produtos = st.multiselect(
        "Produtos:",
        options=produtos_disponiveis,
        default=produtos_disponiveis
    )
    
    # Filtro de datas
    if 'Data' in df.columns:
        data_min = df['Data'].min().date()
        data_max = df['Data'].max().date()
        data_inicio, data_fim = st.slider(
            "Período:",
            min_value=data_min,
            max_value=data_max,
            value=(data_min, data_max))
    else:
        data_inicio, data_fim = None, None
    
    # Filtro de clientes
    clientes_disponiveis = df['Cliente'].unique() if 'Cliente' in df.columns else []
    clientes = st.multiselect(
        "Clientes:",
        options=clientes_disponiveis,
        default=clientes_disponiveis
    )
    
    st.divider()
    st.caption("Atualizado em: " + datetime.now().strftime("%d/%m/%Y %H:%M"))

# Aplicar filtros
try:
    df_filtrado = df.copy()
    
    if produtos:
        df_filtrado = df_filtrado[df_filtrado['Produto'].isin(produtos)]
    
    if 'Data' in df_filtrado.columns and data_inicio and data_fim:
        df_filtrado = df_filtrado[
            (df_filtrado['Data'].dt.date >= data_inicio) &
            (df_filtrado['Data'].dt.date <= data_fim)
        ]
    
    if clientes:
        df_filtrado = df_filtrado[df_filtrado['Cliente'].isin(clientes)]
        
except Exception as e:
    st.error(f"Erro ao aplicar filtros: {str(e)}")
    df_filtrado = df.copy()

# ---------------------------------------
# Página Principal
# ---------------------------------------
st.title("📊 Painel de Pricing e Inteligência de Mercado")
st.markdown("Análise em tempo real dos preços, volume de vendas e fatores de mercado.")

# ---------------------------------------
# Seção 1: KPIs Principais
# ---------------------------------------
st.header("Indicadores-Chave")

if not df_filtrado.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Preço Médio FOB
    if 'Preço FOB ($/t)' in df_filtrado.columns:
        preco_fob = df_filtrado['Preço FOB ($/t)'].mean()
        col1.metric("Preço Médio FOB", formatar_moeda(preco_fob))
    
    # KPI 2: Volume Total
    if 'Quantidade comercializada' in df_filtrado.columns:
        volume_total = df_filtrado['Quantidade comercializada'].sum()
        col2.metric("Volume Total", f"{volume_total:,.0f} t")
    
    # KPI 3: Margem CFR
    if 'CFR ($/t)' in df_filtrado.columns and 'Preço FOB ($/t)' in df_filtrado.columns:
        margem_cfr = ((df_filtrado['CFR ($/t)'] - df_filtrado['Preço FOB ($/t)']).mean() / 
                      df_filtrado['Preço FOB ($/t)'].mean()) * 100
        col3.metric("Margem CFR", f"{margem_cfr:.1f}%")
    
    # KPI 4: Exposição Cambial
    if 'Câmbio (R$/US$)' in df_filtrado.columns:
        cambio_medio = df_filtrado['Câmbio (R$/US$)'].mean()
        col4.metric("Câmbio Médio", f"R${cambio_medio:.2f}")

# ---------------------------------------
# Seção 2: Análise Temporal (Com Médias Diárias)
# ---------------------------------------
st.header("Tendências de Mercado")

if not df_filtrado.empty and 'Data' in df_filtrado.columns:
    tab1, tab2 = st.tabs(["Preços", "Commodities"])
    
    with tab1:
        if 'Preço FOB ($/t)' in df_filtrado.columns and 'CFR ($/t)' in df_filtrado.columns:
            # Calcular médias diárias
            df_medias = df_filtrado.groupby(df_filtrado['Data'].dt.date).agg({
                'Preço FOB ($/t)': 'mean',
                'CFR ($/t)': 'mean'
            }).reset_index()
            df_medias['Data'] = pd.to_datetime(df_medias['Data'])
            
            fig = go.Figure()
            
            # Adicionar FOB (média diária)
            fig.add_trace(go.Scatter(
                x=df_medias['Data'],
                y=df_medias['Preço FOB ($/t)'],
                name='Preço FOB (Média Diária)',
                mode='lines',
                line=dict(width=2.5, color='#1f77b4')
            ))
            
            # Adicionar CFR (média diária)
            fig.add_trace(go.Scatter(
                x=df_medias['Data'],
                y=df_medias['CFR ($/t)'],
                name='CFR (Média Diária)',
                mode='lines',
                line=dict(width=2.5, color='#ff7f0e', dash='dash')
            ))
            
            # Adicionar linha de tendência para FOB
            try:
                z_fob = np.polyfit(df_medias['Data'].astype(np.int64) // 10**9, 
                                  df_medias['Preço FOB ($/t)'], 1)
                p_fob = np.poly1d(z_fob)
                fig.add_trace(go.Scatter(
                    x=df_medias['Data'],
                    y=p_fob(df_medias['Data'].astype(np.int64) // 10**9),
                    name='Tendência FOB',
                    mode='lines',
                    line=dict(width=2, color='#1f77b4', dash='dot')
                ))
            except:
                pass
            
            fig.update_layout(
                title="Evolução de Preços FOB e CFR (Médias Diárias)",
                xaxis_title="Data",
                yaxis_title="Preço (US$/t)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Calcular médias diárias para commodities
        df_commodities = df_filtrado.groupby(df_filtrado['Data'].dt.date).agg({
            'FuturoMilho': 'mean',
            'FuturoSoja': 'mean',
            'CotacaoPetroleo': 'mean'
        }).reset_index()
        df_commodities['Data'] = pd.to_datetime(df_commodities['Data'])
        
        fig = go.Figure()
        
        # Commodities com médias diárias
        if 'FuturoMilho' in df_commodities.columns:
            fig.add_trace(go.Scatter(
                x=df_commodities['Data'],
                y=df_commodities['FuturoMilho'],
                name="Futuro Milho (Média Diária)",
                line=dict(color='green', width=2)
            ))
        
        if 'FuturoSoja' in df_commodities.columns:
            fig.add_trace(go.Scatter(
                x=df_commodities['Data'],
                y=df_commodities['FuturoSoja'],
                name="Futuro Soja (Média Diária)",
                line=dict(color='brown', width=2)
            ))
        
        if 'CotacaoPetroleo' in df_commodities.columns:
            fig.add_trace(go.Scatter(
                x=df_commodities['Data'],
                y=df_commodities['CotacaoPetroleo'],
                name="Petróleo (Média Diária)",
                line=dict(color='black', width=2, dash='dot')
            ))
        
        fig.update_layout(
            title="Commodities e Fatores Externos (Médias Diárias)",
            xaxis_title="Data",
            yaxis_title="Valor",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Configurar eixos secundários
        fig.update_layout(
            yaxis=dict(title="Milho/Soja (US$/bushel)", side="left"),
            yaxis2=dict(
                title="Petróleo (US$/barril)",
                overlaying="y",
                side="right",
                showgrid=False
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# Seção 3: Análise por Produto
# ---------------------------------------
st.header("Análise por Produto")

if not df_filtrado.empty and 'Produto' in df_filtrado.columns:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Métricas por Produto")
        stats_data = []
        
        if 'Preço FOB ($/t)' in df_filtrado.columns:
            stats_data.append('Preço FOB ($/t)')
        if 'CFR ($/t)' in df_filtrado.columns:
            stats_data.append('CFR ($/t)')
        if 'Quantidade comercializada' in df_filtrado.columns:
            stats_data.append('Quantidade comercializada')
        
        if stats_data:
            stats = df_filtrado.groupby('Produto')[stats_data].agg(['mean', 'std', 'min', 'max'])
            st.dataframe(stats.style.format("{:.2f}"))
    
    with col2:
        if 'Preço FOB ($/t)' in df_filtrado.columns:
            st.subheader("Distribuição de Preços")
            fig = px.box(
                df_filtrado,
                x='Produto',
                y='Preço FOB ($/t)',
                color='Produto',
                points="all",
                hover_data=['Data']
            )
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# Seção 4: Correlações de Mercado
# ---------------------------------------
st.header("Relações de Mercado")

if not df_filtrado.empty:
    # Selecionar colunas numéricas para correlação
    colunas_numericas = []
    for col in ['Preço FOB ($/t)', 'CFR ($/t)', 'Câmbio (R$/US$)', 
               'CotacaoPetroleo', 'FuturoMilho', 'FuturoSoja']:
        if col in df_filtrado.columns:
            colunas_numericas.append(col)
    
    if len(colunas_numericas) > 1:
        st.subheader("Correlações entre Variáveis")
        corr_matrix = df_filtrado[colunas_numericas].corr()
        fig = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale='RdBu',
            zmin=-1,
            zmax=1
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Dispersão Preço vs Commodities
    if 'Preço FOB ($/t)' in df_filtrado.columns and len(colunas_numericas) > 1:
        st.subheader("Relação entre Preço FOB e Commodities")
        col_x, col_y = st.columns(2)
        
        with col_x:
            opcoes_x = [c for c in colunas_numericas if c != 'Preço FOB ($/t)']
            var_x = st.selectbox(
                "Variável X:",
                options=opcoes_x,
                index=0
            )
        
        with col_y:
            var_y = st.selectbox(
                "Variável Y:",
                options=['Preço FOB ($/t)', 'CFR ($/t)'],
                index=0
            )
        
        fig = px.scatter(
            df_filtrado,
            x=var_x,
            y=var_y,
            color='Produto' if 'Produto' in df_filtrado.columns else None,
            trendline='ols',
            hover_data=['Data']
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# Seção 5: Análise de Clientes
# ---------------------------------------
st.header("Desempenho por Cliente")

if not df_filtrado.empty and 'Cliente' in df_filtrado.columns:
    if 'Quantidade comercializada' in df_filtrado.columns:
        st.subheader("Principais Clientes por Volume")
        top_clientes = df_filtrado.groupby('Cliente')['Quantidade comercializada'].sum().nlargest(5)
        fig = px.bar(
            top_clientes,
            x=top_clientes.index,
            y=top_clientes.values,
            labels={'y': 'Volume (t)', 'index': 'Cliente'},
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# Seção 6: Simulador de Precificação
# ---------------------------------------
st.header("Simulador de Cenários")
st.markdown("Estime o impacto de variações de mercado no preço final do produto.")

col1, col2, col3 = st.columns(3)

with col1:
    cambio = st.slider("Câmbio (R$/US$)", 4.0, 7.0, 5.2, 0.1)

with col2:
    petroleo = st.slider("Preço do Petróleo (US$/barril)", 60.0, 150.0, 85.0, 1.0)

with col3:
    futuro_soja = st.slider("Futuro da Soja (US$/bushel)", 10.0, 20.0, 14.5, 0.1)

# Modelo preditivo simplificado (exemplo)
preco_base = 450
coef_cambio = 20
coef_petroleo = 0.8
coef_soja = 2.5

preco_estimado = preco_base + coef_cambio * (cambio - 5.0) + coef_petroleo * (petroleo - 80) + coef_soja * (futuro_soja - 14.0)
st.subheader(f"Preço FOB Estimado: :blue[{formatar_moeda(preco_estimado)}]")

# ---------------------------------------
# Seção 7: Monitoramento de Alertas
# ---------------------------------------
st.header("Monitoramento de Alertas")

if not df_filtrado.empty and 'Preço FOB ($/t)' in df_filtrado.columns and 'Data' in df_filtrado.columns:
    try:
        # Ordenar por data para garantir a última entrada
        df_ordenado = df_filtrado.sort_values('Data')
        
        if len(df_ordenado) > 30:
            preco_atual = df_ordenado['Preço FOB ($/t)'].iloc[-1]
            media_30d = df_ordenado['Preço FOB ($/t)'].iloc[-30:].mean()
            desvio_30d = df_ordenado['Preço FOB ($/t)'].iloc[-30:].std()
            
            if preco_atual > media_30d + 2 * desvio_30d:
                st.error("🚨 ALERTA: Preço FOB atual está acima de 2 desvios padrão da média móvel de 30 dias!")
            elif preco_atual < media_30d - 2 * desvio_30d:
                st.warning("⚠️ Atenção: Preço FOB atual está abaixo de 2 desvios padrão da média móvel de 30 dias")
            else:
                st.success("✅ Preço FOB dentro da faixa normal de variação")
    
    except Exception as e:
        st.warning(f"Não foi possível verificar alertas: {str(e)}")

# ---------------------------------------
# Rodapé
# ---------------------------------------
st.divider()
st.caption("Desenvolvido pela Equipe de Pricing - Yara Industrial Solutions | Dados atualizados diariamente")