import streamlit as st
import math

# Configuração da página
st.set_page_config(page_title="Calculadora Pix ou Parcela", page_icon="💰", layout="centered")

# Lógica de proteção por senha
def check_password():
    """Retorna `True` se o usuário digitou a senha correta."""
    def password_entered():
        # Verifica a senha digitada contra a senha salva nos secrets do Streamlit
        # Se não houver secret configurado, usa "1234" como padrão
        senha_correta = st.secrets.get("senha_app", "1234")
        if st.session_state["password"] == senha_correta:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Limpa a senha por segurança
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primeira execução, pede a senha
        st.text_input("Digite a senha para acessar a calculadora", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Senha incorreta, pede de novo
        st.text_input("Digite a senha para acessar a calculadora", type="password", on_change=password_entered, key="password")
        st.error("😕 Senha incorreta.")
        return False
    return True

# Funções matemáticas
def calcular_taxa_mensal_cdi(cdi_anual):
    return ((1 + cdi_anual / 100) ** (1 / 12)) - 1

def simular_parcelado(valor_total, parcelas, taxa_mensal):
    valor_parcela = valor_total / parcelas
    saldo = valor_total
    for _ in range(parcelas):
        saldo += saldo * taxa_mensal
        saldo -= valor_parcela
    return max(0, saldo)

def simular_a_vista(desconto, parcelas, taxa_mensal):
    saldo = desconto
    for _ in range(parcelas):
        saldo += saldo * taxa_mensal
    return saldo

# App Principal
if check_password():
    st.title("💰 Calculadora Pix ou Parcela")
    st.write("Descubra qual opção deixa mais dinheiro no seu bolso no final do período.")

    with st.form("calculadora_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Dados da Compra")
            valor_total = st.number_input("Valor total a prazo (R$)", min_value=0.01, value=833.20, step=10.0)
            parcelas = st.number_input("Número de parcelas", min_value=1, max_value=36, value=10, step=1)
            valor_pix = st.number_input("Valor final pagando no Pix (R$)", min_value=0.01, value=795.90, step=10.0)
            desconto_pix = valor_total - valor_pix
            st.info(f"Desconto calculado: R$ {desconto_pix:.2f}")

        with col2:
            st.subheader("Dados de Investimento")
            cdi_anual = st.number_input("CDI Anual Atual (%)", min_value=0.01, value=10.50, step=0.1)
            percentual_cdb = st.number_input("Rendimento do CDB (% do CDI)", min_value=1.0, value=140.0, step=5.0)
            rendimento_bolsa = st.number_input("Expectativa na Bolsa (% a.m.)", min_value=0.01, value=1.00, step=0.1)

        submit_button = st.form_submit_button("Simular Cenários")

    if submit_button:
        # Cálculos de taxas
        cdi_mensal = calcular_taxa_mensal_cdi(cdi_anual)
        taxa_cdb_bruta_mensal = cdi_mensal * (percentual_cdb / 100)
        imposto_de_renda = 0.225
        taxa_cdb_liquida_mensal = taxa_cdb_bruta_mensal * (1 - imposto_de_renda)
        taxa_bolsa_mensal = rendimento_bolsa / 100
        
        # Simulações
        saldo_parcelado_cdb = simular_parcelado(valor_total, parcelas, taxa_cdb_liquida_mensal)
        saldo_parcelado_bolsa = simular_parcelado(valor_total, parcelas, taxa_bolsa_mensal)
        saldo_vista_cdb = simular_a_vista(desconto_pix, parcelas, taxa_cdb_liquida_mensal)
        saldo_vista_bolsa = simular_a_vista(desconto_pix, parcelas, taxa_bolsa_mensal)
        
        resultados = {
            "Pix + Investir Desconto no CDB": saldo_vista_cdb,
            "Pix + Investir Desconto na Bolsa": saldo_vista_bolsa,
            "Parcelado + Investir Total no CDB": saldo_parcelado_cdb,
            "Parcelado + Investir Total na Bolsa": saldo_parcelado_bolsa
        }
        
        resultados_ordenados = sorted(resultados.items(), key=lambda item: item[1], reverse=True)
        
        st.divider()
        st.header(f"🏆 Melhor Opção: {resultados_ordenados[0][0]}")
        st.success(f"Saldo final livre após {parcelas} meses: **R$ {resultados_ordenados[0][1]:.2f}**")
        
        st.subheader("Ranking dos Cenários")
        for i, (nome, saldo) in enumerate(resultados_ordenados):
            if i == 0:
                st.metric(label=f"{i+1}º - {nome}", value=f"R$ {saldo:.2f}", delta="Vencedor")
            else:
                diferenca = saldo - resultados_ordenados[0][1]
                st.metric(label=f"{i+1}º - {nome}", value=f"R$ {saldo:.2f}", delta=f"R$ {diferenca:.2f}", delta_color="inverse")

        st.caption(f"*Nota: O cálculo do CDB já desconta 22,5% de IR sobre os rendimentos mensais.*")