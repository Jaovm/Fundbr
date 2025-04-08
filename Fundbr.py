import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests

# Título
titulo = "Análise Fundamentalista para Buy and Hold"
st.set_page_config(page_title=titulo, layout="wide")
st.title(titulo)

# Checklist para ações Buy and Hold
with st.expander("Checklist para ações Buy and Hold"):
    st.markdown("""
    **Critérios Financeiros**

    1. Empresa com mais de 5 anos listada na Bolsa  
    2. Nunca apresentou prejuízo em ano fiscal  
    3. Lucro positivo nos últimos 20 trimestres (5 anos)  
    4. Dividend Yield médio acima de 5% ao ano nos últimos 5 anos  
    5. ROE (Retorno sobre o Patrimônio Líquido) acima de 10%  
    6. Dívida líquida menor que o patrimônio líquido  
    7. Crescimento de receita nos últimos 5 anos  
    8. Crescimento de lucros nos últimos 5 anos  
    9. Liquidez diária acima de US$ 2 milhões  
    10. Margem líquida estável ou crescente nos últimos 5 anos  
    11. ROIC acima do custo de capital  

    **Critérios Qualitativos**

    12. Presença de vantagens competitivas claras (moat)  
    13. Baixa dependência de subsídios ou incentivos fiscais  
    14. Setor com baixo risco regulatório ou disruptivo  
    15. Governança corporativa sólida e alinhamento com minoritários  
    16. Histórico de reinvestimento eficiente ou política de dividendos consistente  
    17. Capacidade comprovada de adaptação e inovação  
    18. Histórico de baixa diluição de ações  
    19. Participação relevante da diretoria/acionistas majoritários na empresa (skin in the game)  
    """)

# Input do usuário
ticker = st.text_input("Digite o ticker da ação (ex: WEGE3.SA):", "WEGE3.SA")

@st.cache_data

def buscar_dados(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5y")
        return info, hist
    except:
        return None, None

info, hist = buscar_dados(ticker)

if info:
    st.subheader("Resumo da Empresa")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Nome:** {info.get('longName', '-')}")
        st.write(f"**Setor:** {info.get('sector', '-')}")
        st.write(f"**Indústria:** {info.get('industry', '-')}")
        st.write(f"**País:** {info.get('country', '-')}")
    with col2:
        st.write(f"**Dividend Yield:** {round(info.get('dividendYield', 0)*100, 2)}%")
        st.write(f"**ROE:** {round(info.get('returnOnEquity', 0)*100, 2)}%")
        st.write(f"**Margem Líquida:** {round(info.get('netMargins', 0)*100, 2)}%")
        st.write(f"**Dívida/Patrimônio:** {round(info.get('debtToEquity', 0), 2)}")

    st.subheader("Checklist Automatizado - Critérios Financeiros")
    checklist = {
        "Mais de 5 anos na Bolsa": info.get("firstTradeDateEpochUtc", 0) < (pd.Timestamp.now().timestamp() - 5*365*24*60*60),
        "Nunca deu prejuízo (ano fiscal)": info.get("profitMargins", 0) > 0,
        "Dividend Yield médio > 5%": info.get("dividendYield", 0) > 0.05,
        "ROE > 10%": info.get("returnOnEquity", 0) > 0.10,
        "Dívida < Patrimônio": info.get("debtToEquity", 0) < 1,
        "Margem Líquida positiva": info.get("netMargins", 0) > 0,
        "Liquidez diária > US$ 2M": info.get("averageDailyVolume10Day", 0) * info.get("previousClose", 0) > 2_000_000
    }

    for criterio, status in checklist.items():
        st.write(f"- {'✅' if status else '❌'} {criterio}")
else:
    st.warning("Ticker inválido ou não encontrado.")

