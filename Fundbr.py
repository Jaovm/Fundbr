import streamlit as st
import yfinance as yf
import pandas as pd

# Título
titulo = "Análise Fundamentalista para Buy and Hold"
st.set_page_config(page_title=titulo, layout="wide")
st.title(titulo)

# Input do usuário
ticker = st.text_input("Digite o ticker da ação (ex: WEGE3.SA):", "WEGE3.SA")

if ticker:
    acao = yf.Ticker(ticker)

    try:
        info = acao.info
        setor = info.get("sector", "Setor não disponível")
        st.subheader(f"Resumo da empresa: {info.get('longName', 'N/A')}")
        st.markdown(f"**Setor:** {setor}")
        st.markdown(f"**País:** {info.get('country', 'N/A')}")
        st.markdown(f"**Descrição:** {info.get('longBusinessSummary', 'N/A')}")

        st.subheader("Indicadores Financeiros")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("ROE", f"{info.get('returnOnEquity', 0)*100:.2f}%")
            st.metric("Dividend Yield", f"{info.get('dividendYield', 0)*100:.2f}%")
            st.metric("Margem líquida", f"{info.get('netMargins', 0)*100:.2f}%")

        with col2:
            st.metric("Dívida/Patrimônio", f"{info.get('debtToEquity', 0):.2f}")
            st.metric("Lucro líquido (12m)", f"R$ {info.get('netIncomeToCommon', 0)/1e6:.2f} mi")
            st.metric("Receita (12m)", f"R$ {info.get('totalRevenue', 0)/1e6:.2f} mi")

        with col3:
            st.metric("Liquidez média diária", f"R$ {info.get('averageDailyVolume3Month', 0):,}")
            st.metric("Número de funcionários", f"{info.get('fullTimeEmployees', 'N/A')}")
            st.metric("Preço/Lucro (P/L)", f"{info.get('trailingPE', 0):.2f}")

        # Visão futura (de forma resumida)
        st.subheader("Visão futura da empresa")
        analise = info.get("longBusinessSummary", "Resumo futuro não disponível.")
        st.markdown(f"{analise}")

        # Sugestões do mesmo setor
        st.subheader("Outras empresas do mesmo setor (sugestões)")
        sugestoes = {
            "Tecnologia": ["TOTS3.SA", "LINX3.SA"],
            "Energia": ["TAEE11.SA", "ENGI11.SA"],
            "Financeiro": ["ITUB4.SA", "BBAS3.SA"],
            "Consumo Cíclico": ["MGLU3.SA", "VIIA3.SA"],
            "Indústria": ["WEGE3.SA", "EMBR3.SA"],
            "Saúde": ["FLRY3.SA", "HAPV3.SA"]
        }

        if setor in sugestoes:
            for s in sugestoes[setor]:
                st.markdown(f"- [{s}](https://www.google.com/finance/quote/{s})")
        else:
            st.markdown("Setor não encontrado na base de sugestões.")

    except Exception as e:
        st.error("Erro ao buscar dados da ação. Verifique o ticker e tente novamente.")
