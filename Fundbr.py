import streamlit as st
import yfinance as yf

# Dicionário de filosofias recomendadas por setor
setor_filosofia = {
    'Energy': ['Deep Value', 'Dividend Investing'],
    'Technology': ['Growth Investing', 'Quality Investing'],
    'Financial Services': ['Value Investing', 'Dividend Investing'],
    'Utilities': ['Dividend Investing', 'Value Investing'],
    'Healthcare': ['Quality Investing', 'Growth Investing'],
    'Consumer Defensive': ['Quality Investing', 'Value Investing'],
    'Industrials': ['GARP', 'Value Investing'],
    'Consumer Cyclical': ['GARP', 'Growth Investing'],
    'Real Estate': ['Deep Value', 'Dividend Investing']
}

# Funções de avaliação das filosofias
def avaliar_value(d):
    if d['pe_ratio'] < 15 and d['pb_ratio'] < 1.5:
        return True, 'P/L < 15 e P/VP < 1.5 atendidos.'
    return False, 'Não atende critérios clássicos de valor (P/L ou P/VP altos).'

def avaliar_garp(d):
    if d['peg_ratio'] and d['peg_ratio'] < 1:
        return True, f'PEG < 1 ({d["peg_ratio"]:.2f}).'
    return False, 'PEG acima de 1 (crescimento vs preço não equilibrado).'

def avaliar_quality(d):
    if d['roe'] and d['roe'] > 20 and d['profit_margin'] and d['profit_margin'] > 0.15:
        return True, 'ROE > 20% e Margem líquida > 15%.'
    return False, 'Empresa não apresenta alta qualidade (ROE ou margem abaixo do ideal).'

def avaliar_deep_value(d):
    if d['pe_ratio'] < 6 and d['pb_ratio'] < 1:
        return True, 'Múltiplos muito baixos (P/L < 6 e P/VP < 1).'
    return False, 'Não parece descontada o suficiente para Deep Value.'

# Coleta de dados com yfinance
def get_dados_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            'setor': info.get('sector', 'Desconhecido'),
            'pe_ratio': info.get('trailingPE', None),
            'pb_ratio': info.get('priceToBook', None),
            'peg_ratio': info.get('pegRatio', None),
            'roe': info.get('returnOnEquity', None),
            'profit_margin': info.get('profitMargins', None),
        }
    except Exception as e:
        return None

# Streamlit UI
st.title('Análise de Filosofias de Valuation')
ticker = st.text_input('Digite o ticker (ex: PETR4.SA, AAPL)', 'PETR4.SA')

if st.button('Analisar'):
    dados = get_dados_yahoo(ticker)

    if dados:
        setor = dados['setor']
        st.subheader(f"Setor: {setor}")
        recomendadas = setor_filosofia.get(setor, ['Value Investing'])
        st.markdown(f"**Filosofia(s) recomendada(s) para o setor:** {', '.join(recomendadas)}")

        # Avaliação das filosofias
        st.subheader('Avaliação por Filosofia')
        avaliacoes = {
            'Value Investing': avaliar_value(dados),
            'GARP': avaliar_garp(dados),
            'Quality Investing': avaliar_quality(dados),
            'Deep Value': avaliar_deep_value(dados),
        }

        for nome, (aprovado, comentario) in avaliacoes.items():
            status = '✔️ Atende' if aprovado else '❌ Não atende'
            destaque = '⭐' if nome in recomendadas else ''
            st.markdown(f"**{destaque} {nome}**: {status} - {comentario}")

        st.info("Filosofias com estrela são recomendadas para o setor do ativo analisado.")
    else:
        st.error('Erro ao buscar dados. Verifique o ticker.')

