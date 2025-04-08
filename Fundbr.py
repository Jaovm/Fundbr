import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Título
titulo = "Análise Fundamentalista para Buy and Hold"
st.set_page_config(page_title=titulo, layout="wide")
st.title(titulo)

# Input do usuário
ticker = st.text_input("Digite o ticker da ação (ex: WEGE3.SA):", "WEGE3.SA")

# Função para buscar médias do setor via API da Financial Modeling Prep
def buscar_medias_setor(setor_nome):
    try:
        api_key = "7a2Rn70FJUAnnDH0EV4YmHIsrGMCPo95"
        url = f"https://financialmodelingprep.com/api/v4/sector-performance?apikey={api_key}"
        response = requests.get(url)
        data = response.json()
        for setor in data:
            if setor_nome.lower() in setor['sector'].lower():
                return {
                    "ROE": setor.get("roe", 0),
                    "Dividend Yield": setor.get("dividendYield", 0),
                    "Margem Líquida": setor.get("netProfitMargin", 0),
                    "Dívida/Patrimônio": setor.get("debtToEquity", 0),
                    "P/L": setor.get("peRatio", 0)
                }
    except:
        return None

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
            "Technology": ["TOTS3.SA", "LINX3.SA"],
            "Utilities": ["TAEE11.SA", "ENGI11.SA"],
            "Financial Services": ["ITUB4.SA", "BBAS3.SA"],
            "Consumer Cyclical": ["MGLU3.SA", "VIIA3.SA"],
            "Industrials": ["WEGE3.SA", "EMBR3.SA"],
            "Healthcare": ["FLRY3.SA", "HAPV3.SA"]
        }

        if setor in sugestoes:
            for s in sugestoes[setor]:
                st.markdown(f"- [{s}](https://www.google.com/finance/quote/{s})")
        else:
            st.markdown("Setor não encontrado na base de sugestões.")

        # Gráfico de crescimento histórico
        st.subheader("Histórico de Preço - Últimos 5 anos")
        hist = acao.history(period="5y")
        st.line_chart(hist["Close"])

        # Scorecard simplificado
        st.subheader("Score Buy and Hold")
        score = 0

        if info.get("returnOnEquity", 0) > 0.10:
            score += 1
        if info.get("dividendYield", 0) > 0.05:
            score += 1
        if info.get("debtToEquity", 0) < 1:
            score += 1
        if info.get("netMargins", 0) > 0.1:
            score += 1
        if info.get("totalRevenue", 0) > 0:
            score += 1
        if info.get("netIncomeToCommon", 0) > 0:
            score += 1

        st.markdown(f"**Pontuação:** {score}/6 critérios atendidos")

        # Comparativo com setor via API
        st.subheader("Comparação com Média do Setor")
        media_setor = buscar_medias_setor(setor)

        if media_setor:
            dados = {
                "Indicador": ["ROE", "Dividend Yield", "Margem Líquida", "Dívida/Patrimônio", "P/L"],
                "Empresa": [
                    info.get("returnOnEquity", 0),
                    info.get("dividendYield", 0),
                    info.get("netMargins", 0),
                    info.get("debtToEquity", 0),
                    info.get("trailingPE", 0)
                ],
                "Média Setor": [
                    media_setor["ROE"],
                    media_setor["Dividend Yield"],
                    media_setor["Margem Líquida"],
                    media_setor["Dívida/Patrimônio"],
                    media_setor["P/L"]
                ]
            }
            df_comp = pd.DataFrame(dados)
            st.dataframe(df_comp)
        else:
            st.warning("Não foi possível obter as médias do setor.")

    except Exception as e:
        st.error("Erro ao buscar dados da ação. Verifique o ticker e tente novamente.")

