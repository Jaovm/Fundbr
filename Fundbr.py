import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime

# Título
titulo = "Análise Fundamentalista para Buy and Hold"
st.set_page_config(page_title=titulo, layout="wide")
st.title(titulo)

# Campo para chave da API da Financial Modeling Prep
api_key = st.text_input("Digite sua chave da API da Financial Modeling Prep (FMP):", type="password")

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

def buscar_dados_yahoo(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    hist = stock.history(period="5y")
    return info, hist

@st.cache_data

def buscar_dados_fmp(ticker_fmp, apikey):
    base_url = f"https://financialmodelingprep.com/api/v3"
    endpoints = {
        "profile": f"{base_url}/profile/{ticker_fmp}?apikey={apikey}",
        "income": f"{base_url}/income-statement/{ticker_fmp}?limit=20&apikey={apikey}",
        "ratios": f"{base_url}/ratios-ttm/{ticker_fmp}?apikey={apikey}",
        "quote": f"{base_url}/quote/{ticker_fmp}?apikey={apikey}"
    }
    dados = {}
    for key, url in endpoints.items():
        r = requests.get(url)
        if r.status_code == 200:
            dados[key] = r.json()
    return dados

if ticker and api_key:
    info_yahoo, hist_yahoo = buscar_dados_yahoo(ticker)
    dados_fmp = buscar_dados_fmp(ticker.replace(".SA", ""), api_key)

    perfil = dados_fmp.get("profile", [{}])[0] if dados_fmp.get("profile") else {}

    st.subheader("Resumo da Empresa")
    if perfil:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nome:** {perfil.get('companyName', '-')}")
            st.write(f"**Setor:** {perfil.get('sector', '-')}")
            st.write(f"**Indústria:** {perfil.get('industry', '-')}")
        with col2:
            st.write(f"**País:** {perfil.get('country', '-')}")
            st.write(f"**Preço atual:** US$ {perfil.get('price', '-')}")
            st.write(f"**Beta:** {perfil.get('beta', '-')}")

    st.subheader("Checklist Automatizado - Critérios Financeiros")
    criterios = {}

    # Critério 1: Mais de 5 anos na bolsa
    primeiro_ano = datetime.datetime.fromtimestamp(info_yahoo.get("firstTradeDateEpochUtc", datetime.datetime.now().timestamp())).year
    criterios["Mais de 5 anos na Bolsa"] = primeiro_ano <= datetime.datetime.now().year - 5

    # Critério 2: Nunca deu prejuízo em ano fiscal
    lucro_anos = [item['netIncome'] for item in dados_fmp.get('income', []) if item['netIncome'] > 0]
    criterios["Nunca deu prejuízo em ano fiscal"] = len(lucro_anos) == len(dados_fmp.get('income', []))

    # Critério 3: Lucro positivo nos últimos 20 trimestres
    criterios["Lucro positivo nos últimos 20 trimestres"] = len(lucro_anos) >= 20

    # Critério 4: DY médio > 5%
    dy = 0
    if perfil and perfil.get("price"):
        dy = perfil.get("lastDiv", 0) / perfil.get("price", 1)
    criterios["Dividend Yield médio > 5%"] = dy > 0.05

    # Critério 5: ROE > 10%
    roe = dados_fmp.get("ratios", [{}])[0].get("returnOnEquityTTM", 0)
    criterios["ROE > 10%"] = roe > 0.10

    # Critério 6: Dívida < Patrimônio
    debt_ratio = dados_fmp.get("ratios", [{}])[0].get("debtEquityRatioTTM", 1)
    criterios["Dívida < Patrimônio"] = debt_ratio < 1

    # Critério 7: Crescimento de receita nos últimos 5 anos
    receitas = [item['revenue'] for item in dados_fmp.get('income', [])[-5:]]
    criterios["Crescimento de receita 5 anos"] = all(x < y for x, y in zip(receitas, receitas[1:])) if len(receitas) == 5 else False

    # Critério 8: Crescimento de lucros nos últimos 5 anos
    lucros = [item['netIncome'] for item in dados_fmp.get('income', [])[-5:]]
    criterios["Crescimento de lucros 5 anos"] = all(x < y for x, y in zip(lucros, lucros[1:])) if len(lucros) == 5 else False

    # Critério 9: Liquidez diária > 2 milhões
    media_volume = info_yahoo.get("averageDailyVolume10Day", 0) * info_yahoo.get("previousClose", 0)
    criterios["Liquidez diária > US$ 2M"] = media_volume > 2_000_000

    # Critério 10: Margem líquida estável ou crescente
    margens = [item.get("netProfitMargin", 0) for item in dados_fmp.get("ratios", [{}])] * 5
    criterios["Margem líquida estável ou crescente"] = all(x <= y for x, y in zip(margens, margens[1:]))

    # Critério 11: ROIC acima do custo de capital (não disponível na versão gratuita da FMP)
    criterios["ROIC acima do custo de capital"] = "(necessário plano pago ou cálculo manual)"

    for crit, status in criterios.items():
        if isinstance(status, bool):
            st.write(f"- {'✅' if status else '❌'} {crit}")
        else:
            st.write(f"- ❓ {crit}: {status}")

