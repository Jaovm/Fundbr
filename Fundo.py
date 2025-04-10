import streamlit as st
import yfinance as yf
import pandas as pd

# ===================== PARAMETROS GLOBAIS =====================
TAXA_DESCONTO = 0.10
CRESCIMENTO = 0.05
YIELD_DESEJADO = 0.06
MULTIPLOS_SETORIAIS = {
    'finance': 8,
    'tech': 20,
    'utilities': 12,
    'default': 15
}

# ===================== FUNCOES DE VALUATION =====================
def metodo_graham(lpa, crescimento):
    return lpa * (8.5 + 2 * crescimento * 100)

def metodo_bazin(dividendos_ano, yield_desejado=YIELD_DESEJADO):
    return dividendos_ano / yield_desejado

def metodo_ddm(dividendos_ano, crescimento, taxa_desconto=TAXA_DESCONTO):
    if taxa_desconto <= crescimento:
        return None
    return dividendos_ano / (taxa_desconto - crescimento)

def metodo_valor_patrimonial(valor_patrimonial):
    return valor_patrimonial

def metodo_multiplos(lpa, setor):
    multiplicador = MULTIPLOS_SETORIAIS.get(setor.lower(), MULTIPLOS_SETORIAIS['default'])
    return lpa * multiplicador

def metodo_dcf(fcf_acao, crescimento, anos=5, taxa_desconto=TAXA_DESCONTO):
    fcf_proj = [fcf_acao * ((1 + crescimento) ** i) for i in range(1, anos + 1)]
    valor_presente = sum([fcf / ((1 + taxa_desconto) ** i) for i, fcf in enumerate(fcf_proj, 1)])
    valor_terminal = fcf_proj[-1] * (1 + crescimento) / (taxa_desconto - crescimento)
    return valor_presente + valor_terminal / ((1 + taxa_desconto) ** anos)

def sugestao_metodo(setor):
    setor = setor.lower()
    if 'finance' in setor:
        return ['Valor Patrimonial', 'Múltiplos']
    elif 'utilities' in setor:
        return ['Bazin', 'DDM']
    elif 'tech' in setor:
        return ['DCF', 'Graham']
    elif 'consumer' in setor or 'varejo' in setor:
        return ['Múltiplos', 'Graham']
    else:
        return ['Graham', 'Bazin']

def get_comparaveis_setor(setor, exclude_ticker):
    tickers = ['ITUB4.SA', 'BBDC4.SA', 'PETR4.SA', 'VALE3.SA', 'WEGE3.SA', 'EGIE3.SA', 'VIVT3.SA']
    dados = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info
            if info.get('sector', '').lower() == setor.lower() and t != exclude_ticker:
                dados.append({
                    'Ticker': t,
                    'Setor': info.get('sector', ''),
                    'LPA': info.get('trailingEps', 0),
                    'Preço': info.get('currentPrice', 0),
                    'P/L': info.get('currentPrice', 0) / info.get('trailingEps', 1)
                })
        except:
            pass
    return pd.DataFrame(dados)

# ===================== PREÇO TETO / PRECIFICAÇÃO =====================
def get_fundamentals(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    pe_ratio = info.get('trailingPE', None)
    pb_ratio = info.get('priceToBook', None)
    eps = info.get('epsTrailingTwelveMonths', None)
    eps_growth = info.get('earningsQuarterlyGrowth', None)

    if eps_growth is not None:
        eps_growth *= 100

    market_cap = info.get('marketCap', None)
    current_price = info.get('currentPrice', None)
    dividend_yield = info.get('dividendYield', None)
    target_mean_price = info.get('targetMeanPrice', None)
    sector = info.get('sector', None)

    return pe_ratio, pb_ratio, eps, eps_growth, market_cap, current_price, dividend_yield, target_mean_price, sector

def calculate_fair_price(sector, pe_ratio, pb_ratio, eps, roe):
    if sector == "Financial Services" and pb_ratio and roe:
        return pb_ratio * roe * 10
    elif pe_ratio and eps:
        return pe_ratio * eps
    return None

# ===================== INTERFACE =====================
st.title("Valuation Automático de Ações")
ticker_input = st.text_input("Digite o ticker da ação (ex: WEGE3.SA):")

if ticker_input:
    ticker = yf.Ticker(ticker_input)
    info = ticker.info

    setor = info.get('sector', 'Desconhecido')
    preco = info.get('currentPrice', 0)
    lpa = info.get('trailingEps', 0)
    dividendos = info.get('dividendRate', 0)
    dy = info.get('dividendYield', 0) or 0
    patrimonio = info.get('bookValue', 0)
    acoes = info.get('sharesOutstanding', 1)
    fcf_total = info.get('freeCashflow', 0) or 0
    fcf_acao = fcf_total / acoes if acoes > 0 else 0

    st.subheader("Resultado do Valuation")
    st.write("Setor:", setor)
    st.write("Preço atual:", f"R$ {preco:.2f}")

    resultados = {
        'Graham': metodo_graham(lpa, CRESCIMENTO),
        'Bazin': metodo_bazin(dividendos),
        'DDM': metodo_ddm(dividendos, CRESCIMENTO),
        'Valor Patrimonial': metodo_valor_patrimonial(patrimonio),
        'Múltiplos (P/L Setorial)': metodo_multiplos(lpa, setor),
        'DCF': metodo_dcf(fcf_acao, CRESCIMENTO)
    }

    for nome, valor in resultados.items():
        if valor:
            st.metric(label=nome, value=f"R$ {valor:.2f}", delta=f"{((valor - preco)/preco)*100:.2f}%")

    st.write("\n**Métodos sugeridos para o setor:**", ", ".join(sugestao_metodo(setor)))

    st.subheader("Análise de Múltiplos: Comparáveis do Setor")
    comparaveis_df = get_comparaveis_setor(setor, ticker_input)
    if not comparaveis_df.empty:
        st.dataframe(comparaveis_df)
    else:
        st.write("Sem comparáveis encontrados ou setor não identificado.")

    st.subheader("Preço Teto / Precificação Alternativa")
    pe_ratio, pb_ratio, eps, eps_growth, market_cap, current_price, dividend_yield, target_mean_price, sector_fair = get_fundamentals(ticker_input)
    fair_price = calculate_fair_price(sector_fair, pe_ratio, pb_ratio, eps, pe_ratio)

    st.write(f"Setor: {sector_fair if sector_fair else 'Não disponível'}")
    st.write(f"Preço Justo Estimado: {fair_price if fair_price else 'Não disponível'}")
    st.write(f"Preço Atual: {current_price}")
    st.write(f"P/E Ratio: {pe_ratio}")
    st.write(f"P/B Ratio: {pb_ratio}")
    st.write(f"EPS: {eps}")
    st.write(f"Crescimento EPS: {eps_growth}%")
    st.write(f"Market Cap: {market_cap}")
    st.write(f"Dividend Yield: {dividend_yield}")
    st.write(f"Preço Alvo Médio (analistas): {target_mean_price}")

