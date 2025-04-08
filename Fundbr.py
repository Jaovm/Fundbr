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
            roe = info.get('returnOnEquity', 0)
            dy = info.get('dividendYield', 0)
            margem = info.get('netMargins', 0)
            st.metric("ROE", f"{roe*100:.2f}%")
            st.metric("Dividend Yield", f"{dy*100:.2f}%")
            st.metric("Margem líquida", f"{margem*100:.2f}%")

        with col2:
            div_patrim = info.get('debtToEquity', 0)
            lucro = info.get('netIncomeToCommon', 0)
            receita = info.get('totalRevenue', 0)
            st.metric("Dívida/Patrimônio", f"{div_patrim:.2f}")
            st.metric("Lucro líquido (12m)", f"R$ {lucro/1e6:.2f} mi")
            st.metric("Receita (12m)", f"R$ {receita/1e6:.2f} mi")

        with col3:
            liquidez = info.get('averageDailyVolume3Month', 0)
            pl = info.get('trailingPE', 0)
            st.metric("Liquidez média diária", f"R$ {liquidez:,}")
            st.metric("Número de funcionários", f"{info.get('fullTimeEmployees', 'N/A')}")
            st.metric("Preço/Lucro (P/L)", f"{pl:.2f}")

        st.subheader("Visão futura da empresa")
        analise = info.get("longBusinessSummary", "Resumo futuro não disponível.")
        st.markdown(f"{analise}")

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

        st.subheader("Histórico de Preço - Últimos 5 anos")
        hist = acao.history(period="5y")
        st.line_chart(hist["Close"])

        st.subheader("Score Buy and Hold e Análise SWOT")
        score = 0
        criterios = []

        if roe > 0.10:
            score += 1
            criterios.append("✔ ROE acima de 10% (força)")
        else:
            criterios.append("✖ ROE abaixo de 10% (fraqueza)")

        if dy > 0.05:
            score += 1
            criterios.append("✔ Dividend Yield acima de 5% (força)")
        else:
            criterios.append("✖ Dividend Yield abaixo de 5% (atenção)")

        if div_patrim < 1:
            score += 1
            criterios.append("✔ Dívida menor que patrimônio (força)")
        else:
            criterios.append("✖ Dívida maior que patrimônio (atenção)")

        if margem > 0.1:
            score += 1
            criterios.append("✔ Margem líquida acima de 10% (força)")
        else:
            criterios.append("✖ Margem líquida abaixo de 10% (atenção)")

        if receita > 0:
            score += 1
            criterios.append("✔ Receita positiva nos últimos 12 meses")
        else:
            criterios.append("✖ Receita negativa")

        if lucro > 0:
            score += 1
            criterios.append("✔ Lucro positivo nos últimos 12 meses")
        else:
            criterios.append("✖ Lucro negativo")

        st.markdown(f"**Pontuação total:** {score}/6 critérios atendidos")
        st.markdown("### Comentários sobre critérios:")
        for c in criterios:
            st.markdown(f"- {c}")

        media_setor = buscar_medias_setor(setor)
        st.subheader("Comparação com Média do Setor")
        if media_setor:
            dados = {
                "Indicador": ["ROE", "Dividend Yield", "Margem Líquida", "Dívida/Patrimônio", "P/L"],
                "Empresa": [roe, dy, margem, div_patrim, pl],
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

            st.subheader("Análise comparativa com o setor")
            comentarios = []
            if roe > media_setor["ROE"]:
                comentarios.append("ROE acima da média do setor (vantagem competitiva)")
            else:
                comentarios.append("ROE abaixo da média do setor (ponto de atenção)")
            if dy > media_setor["Dividend Yield"]:
                comentarios.append("Dividend Yield superior à média do setor")
            if margem > media_setor["Margem Líquida"]:
                comentarios.append("Margem líquida superior ao setor (eficiência)")
            if div_patrim < media_setor["Dívida/Patrimônio"]:
                comentarios.append("Empresa menos endividada que a média do setor")
            if pl < media_setor["P/L"]:
                comentarios.append("Valuation (P/L) abaixo do setor (potencial de valorização)")

            st.markdown("### Observações comparativas:")
            for c in comentarios:
                st.markdown(f"- {c}")

        else:
            st.warning("Não foi possível obter as médias do setor.")

    except Exception as e:
        st.error("Erro ao buscar dados da ação. Verifique o ticker e tente novamente.")

