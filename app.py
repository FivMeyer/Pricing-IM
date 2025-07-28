import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import plotly.express as px
from pathlib import Path

# --- Data Loading & Preprocessing -------------------------------------------
@st.cache_data
def load_data():
    base_path = Path("_data")
    # Leitura das bases
    df_case = pd.read_excel(base_path / "BaseDados.xlsx")  # fileciteturn1file12
    df_case["Data"] = pd.to_datetime(df_case["Data"])  # fileciteturn1file12
    df_case["Data"] = df_case["Data"].dt.strftime("%d-%m-%Y")  # fileciteturn1file12

    df_petroleo = pd.read_csv(base_path / "cotacao_petroleo_2025.csv")  # fileciteturn1file12
    df_soja_milho = pd.read_csv(base_path / "fechamentos_soja_milho_2025.csv")  # fileciteturn1file12

    # Cálculos iniciais
    pivot = (
        df_case
        .pivot_table(index="Data", values="Câmbio (R$/US$)", aggfunc='mean')
        .rename(columns={"Câmbio (R$/US$)": "CambioMedioDia"})  # fileciteturn1file0
    )
    df_case = df_case.merge(pivot, on="Data", how="left")  # fileciteturn1file0
    df_case["ValorTransacaoFOB (R$)"] = (
        df_case["Quantidade (t)"] * df_case["Preço FOB ($/t)"] * df_case["CambioMedioDia"]
    )  # fileciteturn1file0
    df_case["ValorTransacaoCFR (R$)"] = df_case["Quantidade (t)"] * df_case["CFR ($/t)"] * df_case["CambioMedioDia"]  

    return df_case

# --- Metrics Computation ---------------------------------------------------
def compute_metrics(df, produto):
    df_prod = df[df['Produto'] == produto].copy()
    # Elasticidade Preço x Volume
    df_valid = df_prod[(df_prod['Quantidade (t)'] > 0) & (df_prod['Preço FOB ($/t)'] > 0)]
    x = sm.add_constant(np.log(df_valid['Preço FOB ($/t)']))
    y = np.log(df_valid['Quantidade (t)'])
    model = sm.OLS(y, x).fit()
    elasticidade = model.params['Preço FOB ($/t)']  

    # Pass-through Cambial
    df_pt = df_prod.dropna(subset=['Preço FOB ($/t)', 'Câmbio (R$/US$)'])
    X = sm.add_constant(df_pt['Câmbio (R$/US$)'])
    y_pt = df_pt['Preço FOB ($/t)']
    pt_model = sm.OLS(y_pt, X).fit()
    pass_through = pt_model.params['Câmbio (R$/US$)']

    # Preço médio
    preco_medio = df_prod['Preço FOB ($/t)'].mean()

    return {
        'elasticidade': elasticidade,
        'pass_through': pass_through,
        'preco_medio': preco_medio
    }

# --- Streamlit Layout ------------------------------------------------------
def main():
    st.title("Dashboard de Pricing - Yara Case")
    df = load_data()

    produtos = df['Produto'].unique()
    produto = st.sidebar.selectbox("Selecione o produto", produtos)

    # Cálculo de métricas
    metrics = compute_metrics(df, produto)
    st.header(f"Indicadores para {produto}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Elasticidade Preço x Volume", f"{metrics['elasticidade']:.2f}")
    col2.metric("Pass-through Cambial", f"{metrics['pass_through']:.2f}")
    col3.metric("Preço Médio (R$/t)", f"{metrics['preco_medio']:.2f}")

    # Gráfico de Ticket Médio por Cliente
    st.subheader("Ticket Médio por Cliente")
    df_group = (
        df[df['Produto']==produto]
        .groupby('Cliente')
        .agg(ticket=('ValorTransacaoFOB (R$)', 'mean'))
        .reset_index()
    )
    fig1 = px.bar(df_group, x='Cliente', y='ticket', title='R$ por Cliente')
    st.plotly_chart(fig1)

    # Sazonalidade Semanal
    st.subheader("Sazonalidade Semanal: Volume por Dia da Semana")
    df['Data'] = pd.to_datetime(df['Data'], format='%d-%m-%Y')
    df['Dia_Semana'] = df['Data'].dt.day_name()
    saz = (
        df[df['Produto']==produto]
        .groupby('Dia_Semana')['Quantidade (t)']
        .sum()
        .reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])
        .reset_index()
        .rename(columns={'Quantidade (t)': 'Volume'})
    )
    fig2 = px.line(saz, x='Dia_Semana', y='Volume', markers=True)
    st.plotly_chart(fig2)

    # Tabela completa
    st.subheader("Dados Transacionais")
    st.dataframe(df[df['Produto']==produto])

if __name__ == "__main__":
    main()
