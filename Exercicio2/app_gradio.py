"""
TechFix Informatica - Interface de atendimento (Gradio).

Cadastra cliente (reaproveita quando o e-mail ja existe) e abre uma
Ordem de Servico com status inicial 'Aberto' no banco Supabase.
"""

from __future__ import annotations

import os
import re

import gradio as gr
from dotenv import load_dotenv
from supabase import Client, create_client

# ---------------------------------------------------------------------------
# Configuracao e credenciais
# ---------------------------------------------------------------------------
load_dotenv()

SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Variaveis SUPABASE_URL e SUPABASE_KEY nao configuradas. "
        "Crie um arquivo .env a partir de .env.example."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
CELULAR_PATTERN = re.compile(r"^[0-9]{10,13}$")

STATUS_INICIAL = "Aberto"


# ---------------------------------------------------------------------------
# Regras de negocio
# ---------------------------------------------------------------------------
def _validar_entrada(
    nome: str,
    endereco: str,
    email: str,
    celular: str,
    modelo: str,
    problema: str,
) -> str | None:
    """Retorna mensagem de erro, ou None se a entrada for valida."""
    if not all([nome, endereco, email, celular, modelo, problema]):
        return "Preencha todos os campos obrigatorios."
    if not EMAIL_PATTERN.match(email):
        return "E-mail invalido. Exemplo: cliente@exemplo.com."
    if not CELULAR_PATTERN.match(celular):
        return "Celular invalido. Informe de 10 a 13 digitos, apenas numeros."
    return None


def _obter_ou_criar_cliente(
    nome: str,
    endereco: str,
    email: str,
    celular: str,
) -> int:
    """Retorna o id do cliente existente (por e-mail) ou cria um novo."""
    existente = (
        supabase.table("clientes").select("id").eq("email", email).execute()
    )
    if existente.data:
        return int(existente.data[0]["id"])

    novo = (
        supabase.table("clientes")
        .insert(
            {
                "nome": nome,
                "endereco": endereco,
                "email": email,
                "celular_whatsapp": celular,
            }
        )
        .execute()
    )
    return int(novo.data[0]["id"])


def cadastrar(
    nome: str,
    endereco: str,
    email: str,
    celular: str,
    modelo: str,
    problema: str,
) -> str:
    """Valida, persiste cliente e ordem de servico e devolve mensagem."""
    nome = (nome or "").strip()
    endereco = (endereco or "").strip()
    email = (email or "").strip().lower()
    celular = re.sub(r"\D", "", celular or "")
    modelo = (modelo or "").strip()
    problema = (problema or "").strip()

    erro = _validar_entrada(nome, endereco, email, celular, modelo, problema)
    if erro:
        return erro

    try:
        cliente_id = _obter_ou_criar_cliente(nome, endereco, email, celular)

        resposta = (
            supabase.table("ordens_servico")
            .insert(
                {
                    "cliente_id": cliente_id,
                    "modelo_computador": modelo,
                    "problema_relatado": problema,
                    "status": STATUS_INICIAL,
                }
            )
            .execute()
        )
        print("URL carregada:", repr(SUPABASE_URL))
        ordem_id = resposta.data[0]["id"]
        return (
            f"Cadastro realizado com sucesso. "
            f"Ordem de Servico numero {ordem_id} criada."
        )
    except Exception as exc:  # noqa: BLE001 - mensagem amigavel ao usuario
        return f"Falha ao gravar no banco de dados: {exc}"


def limpar() -> tuple[str, str, str, str, str, str, str]:
    """Limpa todos os campos do formulario."""
    return "", "", "", "", "", "", ""


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def construir_interface() -> gr.Blocks:
    with gr.Blocks(title="TechFix - Atendimento") as demo:
        gr.Markdown(
            "# TechFix Informatica\n"
            "### Cadastro de Ordem de Servico\n"
            "Preencha os dados do cliente e do equipamento. "
            "Campos marcados com asterisco sao obrigatorios."
        )

        with gr.Row():
            with gr.Column():
                nome = gr.Textbox(
                    label="Nome do cliente *",
                    placeholder="Ex.: Joao Silva",
                )
                endereco = gr.Textbox(
                    label="Endereco *",
                    placeholder="Rua, numero, bairro, cidade",
                )
                email = gr.Textbox(
                    label="E-mail *",
                    placeholder="cliente@exemplo.com",
                )
                celular = gr.Textbox(
                    label="Celular / WhatsApp *",
                    placeholder="Somente numeros. Ex.: 11987654321",
                )
            with gr.Column():
                modelo = gr.Textbox(
                    label="Modelo do computador *",
                    placeholder="Ex.: Dell Inspiron 15 3000",
                )
                problema = gr.Textbox(
                    label="Problema apresentado *",
                    lines=6,
                    placeholder="Descreva o defeito relatado pelo cliente.",
                )

        with gr.Row():
            botao_cadastrar = gr.Button("Cadastrar", variant="primary")
            botao_limpar = gr.Button("Limpar")

        mensagem = gr.Markdown()

        botao_cadastrar.click(
            fn=cadastrar,
            inputs=[nome, endereco, email, celular, modelo, problema],
            outputs=mensagem,
        )
        botao_limpar.click(
            fn=limpar,
            inputs=None,
            outputs=[nome, endereco, email, celular, modelo, problema, mensagem],
        )

    return demo


if __name__ == "__main__":
    app = construir_interface()
    # share=True gera link publico temporario para teste em dispositivos moveis.
    app.launch(share=True)
