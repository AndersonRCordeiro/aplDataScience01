import streamlit as st
import pandas as pd
import os
from datetime import datetime

ARQUIVO_CSV = "pacientes.csv"
COLUNAS = ["timestamp", "nome", "idade", "convenio", "prioridade", "motivo"]

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


if "pacientes" not in st.session_state:
    st.session_state.pacientes = pd.DataFrame(columns=COLUNAS)

with st.form("cadastro", clear_on_submit=True):
    nome = st.text_input("Nome do paciente")
    idade = st.number_input("Idade", min_value=0, max_value=120, step=1)
    convenio = st.selectbox(
        "Convênio",
        ["Particular", "Unimed", "Bradesco Saúde", "SulAmérica", "Outro"],
    )
    prioridade = st.slider("Prioridade do atendimento", 1, 5, value=1)
    motivo = st.text_area("Motivo da consulta / observações")
    enviado = st.form_submit_button("Cadastrar")

if enviado:
    if not nome.strip():
        st.error("Informe o nome do paciente.")
    else:
        nova_linha = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nome": nome.strip(),
            "idade": int(idade),
            "convenio": convenio,
            "prioridade": int(prioridade),
            "motivo": motivo.strip(),
        }

        st.session_state.pacientes = pd.concat(
            [
                st.session_state.pacientes,
                pd.DataFrame([nova_linha], columns=COLUNAS),
            ],
            ignore_index=True,
        )

        append_csv(nova_linha)
        st.success("Paciente cadastrado!")

st.subheader("Últimos pacientes cadastrados")
st.dataframe(st.session_state.pacientes.tail(5), use_container_width=True)

csv = st.session_state.pacientes.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Baixar CSV",
    data=csv,
    file_name="pacientes.csv",
    mime="text/csv",
)