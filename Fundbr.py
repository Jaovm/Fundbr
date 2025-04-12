import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ===================== PARAMETROS GLOBAIS =====================
TAXA_DESCONTO = 0.10
CRESCIMENTO = 5  # Crescimento em %
YIELD_DESEJADO = 0.06
MULTIPLOS_SETORIAIS = {
    'finance': 8,
    'tech': 20,
    'utilities': 12,
    'default': 15
}

# ===================== FUNCOES DE VALUATION =====================
def metodo_graham(lpa, crescimento):
    return lpa * (8.5 + 2 * crescimento)

def metodo_bazin(dividendos_ano, yield_desejado=YIELD_DESEJADO):
    return dividendos_ano / yield_desejado if dividendos_ano else None

def metodo_ddm(dividendos_ano, crescimento, taxa_desconto=TAXA_DESCONTO):
    g = crescimento / 100
    if taxa_desconto <= g or not dividendos_ano:
        return None
    return dividendos_ano / (taxa_desconto - g)

def metodo_valor_patrimonial(valor_patrimonial):
    return valor_patrimonial if valor_patrimonial else None

def metodo_multiplos(lpa, setor):
    if not lpa:
        return None
    multiplicador = MULTIPLOS_SETORIAIS.get(setor.lower(), MULTIPLOS_SETORIAIS['default'])
    return lpa * multiplicador

def metodo_dcf(fcf_acao, crescimento, anos=5, taxa_desconto=TAXA_DESCONTO):
    if not fcf_acao:
        return None
    g = crescimento / 100
    fcf_proj = [fcf_acao * ((1 + g) ** i) for i in range(1, anos + 1)]
    valor_presente = sum([fcf / ((1 + taxa_desconto) ** i) for i, fcf in enumerate(fcf_proj, 1)])
    valor_terminal = fcf_proj[-1] * (1 + g) / (taxa_desconto - g)
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
                eps = info.get('trailingEps') or 0
                preco = info.get('currentPrice') or 0
                pl = preco / eps if eps else None
                dados.append({
                    'Ticker': t,
                    'Setor': info.get('sector', ''),
                    'LPA': eps,
                    'Preço': preco,
                    'P/L': pl
                })
        except:
            pass
    return pd.DataFrame(dados)

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
    preco = info.get('currentPrice') or 0
    lpa = info.get('trailingEps') or 0
    dividendos = info.get('dividendRate') or 0
    dy = info.get('dividendYield') or 0
    patrimonio = info.get('bookValue') or 0
    acoes = info.get('sharesOutstanding') or 1
    fcf_total = info.get('freeCashflow') or 0
    fcf_acao = fcf_total / acoes if acoes > 0 else 0

    st.subheader("Resultado do Valuation")
    st.write("Setor:", setor)
    st.write("Preço atual:", f"R$ {preco:.2f}")

    resultados = {}

    if lpa:
        resultados['Graham'] = metodo_graham(lpa, CRESCIMENTO)
        resultados['Múltiplos (P/L Setorial)'] = metodo_multiplos(lpa, setor)

    if dividendos:
        resultados['Bazin'] = metodo_bazin(dividendos)
        resultados['DDM'] = metodo_ddm(dividendos, CRESCIMENTO)

    if patrimonio:
        resultados['Valor Patrimonial'] = metodo_valor_patrimonial(patrimonio)

    if fcf_acao:
        resultados['DCF'] = metodo_dcf(fcf_acao, CRESCIMENTO)

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
    st.write(f"Preço Alvo Médio (analistas - fonte: Yahoo Finance): {target_mean_price}")

    # Gráfico de comparação
    st.subheader("Comparação de Preços")
    labels = ['Preço Atual', 'Preço Justo Estimado', 'Preço Alvo Médio']
    values = [preco, fair_price or 0, target_mean_price or 0]

    fig, ax = plt.subplots()
    ax.bar(labels, values, color=['blue', 'green', 'orange'])
    ax.set_ylabel('Valor (R$)')
    ax.set_title('Comparação de Preços de Ação')
    st.pyplot(fig)
