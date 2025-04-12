import streamlit as st
import yfinance as yf

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

def calculate_fair_price(pe_ratio, pb_ratio, eps, roe, setor, fcf_acao):
    # Cálculo do preço justo por múltiplos (P/L ou P/B)
    if setor == "Financial Services" and pb_ratio and roe:
        # Para setor financeiro, usamos o P/B multiplicado pelo ROE
        return pb_ratio * roe * 10
    elif pe_ratio and eps:
        # Para outros setores, usamos P/L * EPS
        return pe_ratio * eps
    elif fcf_acao:
        # Para empresas em crescimento, o DCF pode ser a melhor opção
        return metodo_dcf(fcf_acao, CRESCIMENTO)
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

    # Calcular os resultados usando diferentes métodos
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

    # Cálculo do Preço Justo
    pe_ratio, pb_ratio, eps, eps_growth, market_cap, current_price, dividend_yield, target_mean_price, sector_fair = get_fundamentals(ticker_input)
    fair_price = calculate_fair_price(pe_ratio, pb_ratio, eps, eps_growth, setor, fcf_acao)

    st.write("\n**Preço Justo Estimado (Resultado Final):**", f"R$ {fair_price:.2f}" if fair_price else 'Não disponível')

    # Exibição das métricas
    for nome, valor in resultados.items():
        if valor:
            st.metric(label=nome, value=f"R$ {valor:.2f}", delta=f"{((valor - preco)/preco)*100:.2f}%")

    st.write("\n**Métodos sugeridos para o setor:**", ", ".join(sugestao_metodo(setor)))

    # Cálculo do Upside/Downside com base no preço alvo médio
    target_mean_price = target_mean_price or 0
    upside_downside = ((target_mean_price - preco) / preco) * 100 if target_mean_price else None

    if upside_downside is not None:
        if upside_downside > 0:
            st.write(f"\n**Upside (Potencial de valorização):** {upside_downside:.2f}%")
        else:
            st.write(f"\n**Downside (Risco de desvalorização):** {abs(upside_downside):.2f}%")
    else:
        st.write("\n**Preço alvo médio não disponível.**")
