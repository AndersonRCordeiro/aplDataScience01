"""
TechFix Informatica - Painel administrativo (Streamlit).

Fornece CRUD completo sobre clientes e ordens de servico, filtros de
consulta, indicadores e exportacao CSV. Consome o banco Supabase.
"""

from __future__ import annotations

import os
import re

import pandas as pd
import streamlit as st
from supabase import Client, create_client

from pathlib import Path
from dotenv import load_dotenv

# Carrega o .env da raiz do projeto, independentemente do diretorio
# em que o comando 'streamlit run' foi disparado.
load_dotenv(Path(__file__).resolve().parent / ".env")

# ---------------------------------------------------------------------------
# Configuracao de pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TechFix - Painel Administrativo",
    layout="wide",
)

STATUS_VALIDOS = [
    "Aberto",
    "Em análise",
    "Aguardando peça",
    "Concluído",
    "Entregue",
]
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


# ---------------------------------------------------------------------------
# Conexao com o Supabase
# ---------------------------------------------------------------------------
def _obter_credenciais() -> tuple[str | None, str | None]:
    """Le credenciais de variaveis de ambiente ou de secrets.toml."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if url and key:
        return url, key
    try:
        return st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
    except Exception:  # noqa: BLE001
        print("Credenciais do Supabase nao encontradas em variaveis de ambiente ou secrets.toml.")
        return None, None


@st.cache_resource
def obter_cliente() -> Client:
    url, key = _obter_credenciais()
    if not url or not key:
        st.error(
            "Credenciais do Supabase nao configuradas. "
            "Defina SUPABASE_URL e SUPABASE_KEY em .env ou secrets.toml."
        )
        st.stop()
    return create_client(url, key)


supabase = obter_cliente()


# ---------------------------------------------------------------------------
# Camada de dados
# ---------------------------------------------------------------------------
def carregar_ordens() -> pd.DataFrame:
    """Retorna DataFrame com todas as OS e dados do cliente associado."""
    try:
        resposta = (
            supabase.table("ordens_servico")
            .select(
                "id, modelo_computador, problema_relatado, status, "
                "data_abertura, data_atualizacao, cliente_id, "
                "clientes(id, nome, email, endereco, celular_whatsapp)"
            )
            .order("id", desc=True)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erro ao consultar o banco de dados: {exc}")
        return pd.DataFrame()

    registros: list[dict] = []
    for item in resposta.data:
        cliente = item.get("clientes") or {}
        registros.append(
            {
                "OS": item["id"],
                "Cliente": cliente.get("nome"),
                "E-mail": cliente.get("email"),
                "Celular": cliente.get("celular_whatsapp"),
                "Endereco": cliente.get("endereco"),
                "Equipamento": item["modelo_computador"],
                "Problema": item["problema_relatado"],
                "Status": item["status"],
                "Abertura": item["data_abertura"],
                "Atualizacao": item["data_atualizacao"],
                "cliente_id": cliente.get("id") or item["cliente_id"],
            }
        )
    return pd.DataFrame(registros)


def aplicar_filtros(
    df: pd.DataFrame,
    nome: str,
    email: str,
    status: str,
) -> pd.DataFrame:
    """Aplica filtros de nome, e-mail e status sobre o DataFrame."""
    resultado = df.copy()
    if nome:
        resultado = resultado[
            resultado["Cliente"].str.contains(nome, case=False, na=False)
        ]
    if email:
        resultado = resultado[
            resultado["E-mail"].str.contains(email, case=False, na=False)
        ]
    if status != "Todos":
        resultado = resultado[resultado["Status"] == status]
    return resultado


# ---------------------------------------------------------------------------
# Cabecalho e barra lateral
# ---------------------------------------------------------------------------
st.title("TechFix Informatica - Painel Administrativo")

df_completo = carregar_ordens()

with st.sidebar:
    st.header("Filtros")
    filtro_nome = st.text_input("Nome do cliente")
    filtro_email = st.text_input("E-mail")
    filtro_status = st.selectbox("Status", ["Todos"] + STATUS_VALIDOS)
    st.caption(
        "Os filtros aplicam-se a aba Consultar e ao CSV exportado."
    )

df_filtrado = aplicar_filtros(df_completo, filtro_nome, filtro_email, filtro_status)

aba_consultar, aba_cadastrar, aba_editar, aba_indicadores = st.tabs(
    ["Consultar", "Cadastrar", "Editar e Excluir", "Indicadores"]
)


# ---------------------------------------------------------------------------
# Aba 1 - Consultar
# ---------------------------------------------------------------------------
with aba_consultar:
    st.subheader("Ordens de Servico")

    if df_filtrado.empty:
        st.info("Nenhuma ordem de servico encontrada com os filtros atuais.")
    else:
        st.dataframe(
            df_filtrado.drop(columns=["cliente_id"]),
            use_container_width=True,
            hide_index=True,
        )
        csv = (
            df_filtrado.drop(columns=["cliente_id"])
            .to_csv(index=False)
            .encode("utf-8")
        )
        st.download_button(
            label="Exportar dados filtrados em CSV",
            data=csv,
            file_name="ordens_servico.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------------------------
# Aba 2 - Cadastrar
# ---------------------------------------------------------------------------
with aba_cadastrar:
    st.subheader("Cadastrar nova Ordem de Servico")

    modo = st.radio(
        "Tipo de cliente",
        ["Existente", "Novo"],
        horizontal=True,
    )
    cliente_id: int | None = None

    if modo == "Existente":
        try:
            clientes = (
                supabase.table("clientes")
                .select("id, nome, email")
                .execute()
                .data
            )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Erro ao carregar clientes: {exc}")
            clientes = []

        if not clientes:
            st.warning(
                "Nenhum cliente cadastrado. Selecione a opcao 'Novo'."
            )
        else:
            mapa = {f"{c['nome']} - {c['email']}": c["id"] for c in clientes}
            escolha = st.selectbox("Cliente", list(mapa.keys()))
            cliente_id = mapa[escolha]
    else:
        novo_nome = st.text_input("Nome do cliente *")
        novo_endereco = st.text_input("Endereco *")
        novo_email = st.text_input("E-mail *")
        novo_celular = st.text_input("Celular / WhatsApp *")

    modelo = st.text_input("Modelo do computador *")
    problema = st.text_area("Problema relatado *")
    status_inicial = st.selectbox("Status inicial", STATUS_VALIDOS, index=0)

    if st.button("Cadastrar Ordem de Servico", type="primary"):
        try:
            if modo == "Novo":
                email_limpo = (novo_email or "").strip().lower()
                celular_limpo = re.sub(r"\D", "", novo_celular or "")
                if not all(
                    [novo_nome, novo_endereco, email_limpo, celular_limpo]
                ):
                    st.error("Preencha todos os dados do novo cliente.")
                    st.stop()
                if not EMAIL_PATTERN.match(email_limpo):
                    st.error("E-mail invalido.")
                    st.stop()

                existente = (
                    supabase.table("clientes")
                    .select("id")
                    .eq("email", email_limpo)
                    .execute()
                )
                if existente.data:
                    cliente_id = int(existente.data[0]["id"])
                else:
                    criado = (
                        supabase.table("clientes")
                        .insert(
                            {
                                "nome": novo_nome.strip(),
                                "endereco": novo_endereco.strip(),
                                "email": email_limpo,
                                "celular_whatsapp": celular_limpo,
                            }
                        )
                        .execute()
                    )
                    cliente_id = int(criado.data[0]["id"])

            if not cliente_id:
                st.error("Selecione ou crie um cliente antes de continuar.")
                st.stop()
            if not modelo.strip() or not problema.strip():
                st.error("Informe o equipamento e o problema relatado.")
                st.stop()

            supabase.table("ordens_servico").insert(
                {
                    "cliente_id": cliente_id,
                    "modelo_computador": modelo.strip(),
                    "problema_relatado": problema.strip(),
                    "status": status_inicial,
                }
            ).execute()

            st.success("Ordem de Servico cadastrada com sucesso.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha ao cadastrar a ordem de servico: {exc}")


# ---------------------------------------------------------------------------
# Aba 3 - Editar e Excluir
# ---------------------------------------------------------------------------
with aba_editar:
    st.subheader("Editar ou excluir registros")

    if df_completo.empty:
        st.info("Nenhuma ordem de servico cadastrada.")
    else:
        os_id = st.selectbox(
            "Selecione a Ordem de Servico",
            df_completo["OS"].tolist(),
            key="select_os",
        )
        registro = df_completo[df_completo["OS"] == os_id].iloc[0]

        st.markdown(
            f"**Cliente:** {registro['Cliente']} ({registro['E-mail']})  \n"
            f"**Equipamento:** {registro['Equipamento']}  \n"
            f"**Problema:** {registro['Problema']}"
        )

        # ----- Atualizacao de status -----
        st.markdown("#### Status da Ordem de Servico")
        idx_atual = (
            STATUS_VALIDOS.index(registro["Status"])
            if registro["Status"] in STATUS_VALIDOS
            else 0
        )
        novo_status = st.selectbox(
            "Novo status", STATUS_VALIDOS, index=idx_atual
        )
        if st.button("Atualizar status"):
            try:
                supabase.table("ordens_servico").update(
                    {"status": novo_status}
                ).eq("id", int(os_id)).execute()
                st.success("Status atualizado com sucesso.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Erro ao atualizar status: {exc}")

        st.divider()

        # ----- Edicao dos dados do cliente -----
        st.markdown("#### Dados do cliente")
        with st.form("form_editar_cliente"):
            edit_endereco = st.text_input(
                "Endereco", value=registro["Endereco"] or ""
            )
            edit_email = st.text_input(
                "E-mail", value=registro["E-mail"] or ""
            )
            edit_celular = st.text_input(
                "Celular", value=registro["Celular"] or ""
            )
            salvar = st.form_submit_button("Salvar dados do cliente")

        if salvar:
            email_limpo = edit_email.strip().lower()
            if not EMAIL_PATTERN.match(email_limpo):
                st.error("E-mail invalido.")
            else:
                try:
                    supabase.table("clientes").update(
                        {
                            "endereco": edit_endereco.strip(),
                            "email": email_limpo,
                            "celular_whatsapp": re.sub(
                                r"\D", "", edit_celular
                            ),
                        }
                    ).eq("id", int(registro["cliente_id"])).execute()
                    st.success("Dados do cliente atualizados.")
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Erro ao atualizar cliente: {exc}")

        st.divider()

        # ----- Exclusao de OS -----
        st.markdown("#### Excluir Ordem de Servico")
        confirmar_os = st.checkbox(
            "Confirmo a exclusao desta Ordem de Servico",
            key="confirmar_os",
        )
        if st.button("Excluir Ordem de Servico", disabled=not confirmar_os):
            try:
                supabase.table("ordens_servico").delete().eq(
                    "id", int(os_id)
                ).execute()
                st.success("Ordem de Servico excluida.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Erro ao excluir Ordem de Servico: {exc}")

        # ----- Exclusao de cliente (cascata) -----
        st.markdown(
            "#### Excluir Cliente (remove tambem todas as suas OS)"
        )
        confirmar_cliente = st.checkbox(
            "Confirmo a exclusao do cliente e de todas as suas Ordens de Servico",
            key="confirmar_cliente",
        )
        if st.button(
            "Excluir Cliente", disabled=not confirmar_cliente
        ):
            try:
                supabase.table("clientes").delete().eq(
                    "id", int(registro["cliente_id"])
                ).execute()
                st.success(
                    "Cliente excluido. Ordens de Servico removidas em cascata."
                )
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Erro ao excluir cliente: {exc}")


# ---------------------------------------------------------------------------
# Aba 4 - Indicadores
# ---------------------------------------------------------------------------
with aba_indicadores:
    st.subheader("Indicadores")

    if df_completo.empty:
        st.info("Sem dados para exibir.")
    else:
        contagem = (
            df_completo["Status"]
            .value_counts()
            .reindex(STATUS_VALIDOS, fill_value=0)
        )
        st.metric("Total de Ordens de Servico", int(len(df_completo)))

        colunas = st.columns(len(STATUS_VALIDOS))
        for indice, status in enumerate(STATUS_VALIDOS):
            colunas[indice].metric(status, int(contagem[status]))

        st.bar_chart(contagem)
