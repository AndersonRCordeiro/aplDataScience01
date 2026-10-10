import streamlit as st
import pandas as pd
import os
from datetime import datetime

ARQUIVO_CSV = "pacientes.csv"
COLUNAS = [
    "timestamp", "nome", "idade", "telefone", "convenio",
    "carteirinha", "prioridade", "motivo",
    "responsavel_nome", "responsavel_telefone",
]

st.set_page_config(page_title="Cadastro de Pacientes", layout="centered")
st.title("Cadastro de Pacientes")


def append_csv(linha):
    """Tenta gravar a linha no CSV local. No Streamlit Cloud o arquivo é efêmero."""
    try:
        novo = pd.DataFrame([linha], columns=COLUNAS)
        if os.path.exists(ARQUIVO_CSV) and os.path.getsize(ARQUIVO_CSV) > 0:
            novo.to_csv(ARQUIVO_CSV, mode="a", header=False, index=False)
        else:
            novo.to_csv(ARQUIVO_CSV, mode="w", header=True, index=False)
        return True
    except Exception as e:
        st.warning(f"Não foi possível gravar o CSV local: {e}")
        return False


# ---------- Inicialização do session_state ----------
if "pacientes" not in st.session_state:
    st.session_state.pacientes = pd.DataFrame(columns=COLUNAS)

if "reset_flag" not in st.session_state:
    st.session_state.reset_flag = False

if "mensagem_sucesso" not in st.session_state:
    st.session_state.mensagem_sucesso = None

# IMPORTANTE: este bloco precisa rodar ANTES dos widgets serem criados.
# Como estamos no topo do script e os widgets são criados abaixo,
# podemos redefinir os valores com segurança.
if st.session_state.reset_flag:
    st.session_state.idade_input = 0
    st.session_state.convenio_input = "Particular"
    st.session_state.reset_flag = False


# ---------- Campos fora do form (disparam rerun) ----------
st.subheader("Dados principais")

idade = st.number_input(
    "Idade", min_value=0, max_value=120, step=1, value=0,
    key="idade_input",
)

convenio = st.selectbox(
    "Convênio",
    ["Particular", "Unimed", "Bradesco Saúde", "SulAmérica", "Outro"],
    key="convenio_input",
)

menor = idade < 18
precisa_carteirinha = convenio != "Particular"


# ---------- Demais campos dentro do form ----------
with st.form("cadastro", clear_on_submit=True):
    nome = st.text_input("Nome do paciente")
    telefone = st.text_input("Telefone do paciente")

    if menor:
        st.info("Paciente menor de 18 anos: informe os dados do responsável.")
        responsavel_nome = st.text_input("Nome do responsável")
        responsavel_telefone = st.text_input("Telefone do responsável")
    else:
        responsavel_nome = ""
        responsavel_telefone = ""

    if precisa_carteirinha:
        st.info(f"Convênio “{convenio}”: informe o número da carteirinha.")
        carteirinha = st.text_input("Número da carteirinha do plano")
    else:
        carteirinha = ""

    prioridade = st.slider("Prioridade do atendimento", 1, 5, value=1)
    motivo = st.text_area("Motivo da consulta / observações")

    enviado = st.form_submit_button("Cadastrar")


# ---------- Processamento ----------
if enviado:
    erros = []
    if not nome.strip():
        erros.append("Informe o nome do paciente.")
    if menor and not responsavel_nome.strip():
        erros.append("Informe o nome do responsável.")
    if menor and not responsavel_telefone.strip():
        erros.append("Informe o telefone do responsável.")
    if precisa_carteirinha and not carteirinha.strip():
        erros.append("Informe o número da carteirinha do plano.")

    if erros:
        for e in erros:
            st.error(e)
    else:
        nova_linha = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nome": nome.strip(),
            "idade": int(idade),
            "telefone": telefone.strip(),
            "convenio": convenio,
            "carteirinha": carteirinha.strip() if precisa_carteirinha else "",
            "prioridade": int(prioridade),
            "motivo": motivo.strip(),
            "responsavel_nome": responsavel_nome.strip() if menor else "",
            "responsavel_telefone": responsavel_telefone.strip() if menor else "",
        }

        st.session_state.pacientes = pd.concat(
            [
                st.session_state.pacientes,
                pd.DataFrame([nova_linha], columns=COLUNAS),
            ],
            ignore_index=True,
        )
        append_csv(nova_linha)

        # Sinaliza o reset para o próximo rerun
        st.session_state.reset_flag = True
        st.session_state.mensagem_sucesso = "Paciente cadastrado!"
        st.rerun()


# ---------- Feedback e tabela ----------
if st.session_state.mensagem_sucesso:
    st.success(st.session_state.mensagem_sucesso)
    st.session_state.mensagem_sucesso = None

st.subheader("Últimos pacientes cadastrados")
st.dataframe(st.session_state.pacientes.tail(5), use_container_width=True)

csv = st.session_state.pacientes.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Baixar CSV",
    data=csv,
    file_name="pacientes.csv",
    mime="text/csv",
)