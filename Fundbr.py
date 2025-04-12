import streamlit as st
import yfinance as yf
import pandas as pd

# ===================== UTILITÁRIOS DE AJUSTE DINÂMICO =====================
WACC_POR_SETOR = {
    'financial services': 0.11,
    'technology': 0.12,
    'utilities': 0.08,
    'basic materials': 0.10,
    'consumer defensive': 0.09,
    'energy': 0.11,
    'industrials': 0.10,
    'default': 0.10
}

YIELD_SETORIAL = {
    'financial services': 0.07,
    'technology': 0.02,
    'utilities': 0.05,
    'default': 0.04
}

PL_SETORIAL = {
    'financial services': 8,
    'technology': 20,
    'utilities': 12,
    'default': 15
}

def ajustar_taxa_desconto(setor):
    return WACC_POR_SETOR.get(setor.lower(), WACC_POR_SETOR['default'])

def ajustar_yield(setor):
    return YIELD_SETORIAL.get(setor.lower(), YIELD_SETORIAL['default'])

def ajustar_multiplo(setor):
    return PL_SETORIAL.get(setor.lower(), PL_SETORIAL['default'])

# ===================== MÉTODOS DE VALUATION =====================
def dcf_duas_fases(fcf, crescimento_inicial, crescimento_perpetuo, anos, wacc):
    fcf_proj = [fcf * ((1 + crescimento_inicial) ** i) for i in range(1, anos + 1)]
    valor_presente = sum([fcf / ((1 + wacc) ** i) for i, fcf in enumerate(fcf_proj, 1)])
    fcf_final = fcf_proj[-1] * (1 + crescimento_perpetuo)
    valor_terminal = fcf_final / (wacc - crescimento_perpetuo)
    return valor_presente + valor_terminal / ((1 + wacc) ** anos)

def metodo_multiplo_eps(eps, setor):
    return eps * ajustar_multiplo(setor)

def metodo_bazin(dividendos_ano, setor):
    return dividendos_ano / ajustar_yield(setor)

# ===================== COLETA DE DADOS =====================
def get_dados(ticker):
    info = yf.Ticker(ticker).info
    setor = info.get('sector', 'default')
    preco = info.get('currentPrice', 0)
    lpa = info.get('trailingEps', 0)
    dividendos = info.get('dividendRate', 0)
    dy = info.get('dividendYield') or 0
    patrimonio = info.get('bookValue', 0)
    acoes = info.get('sharesOutstanding', 1)
    fcf_total = info.get('freeCashflow', 0) or 0
    fcf_acao = fcf_total / acoes if acoes > 0 else 0
    crescimento = info.get('earningsQuarterlyGrowth') or 0.05
    target_price = info.get('targetMeanPrice')
    return {
        'setor': setor,
        'preco': preco,
        'lpa': lpa,
        'dividendos': dividendos,
        'dy': dy,
        'patrimonio': patrimonio,
        'fcf_acao': fcf_acao,
        'crescimento': crescimento,
        'target_price': target_price
    }

# ===================== INTERFACE STREAMLIT =====================
st.title("Valuation Profissional de Ações")

ticker = st.text_input("Ticker da ação (ex: WEGE3.SA):")
if ticker:
    dados = get_dados(ticker)
    setor = dados['setor']
    taxa_desconto = ajustar_taxa_desconto(setor)
    crescimento = dados['crescimento']
    crescimento_perp = crescimento / 2

    resultados = {
        'DCF (2 fases)': dcf_duas_fases(dados['fcf_acao'], crescimento, crescimento_perp, 5, taxa_desconto),
        'Múltiplos (P/L Setorial)': metodo_multiplo_eps(dados['lpa'], setor),
        'Bazin': metodo_bazin(dados['dividendos'], setor),
        'Patrimônio por Ação': dados['patrimonio'],
    }

    st.subheader("Resultados do Valuation:")
    for metodo, preco_justo in resultados.items():
        if preco_justo:
            st.metric(metodo, f"R$ {preco_justo:.2f}")

    if dados['target_price']:
        st.write(f"**Preço Alvo Médio (Analistas)**: R$ {dados['target_price']:.2f}")
