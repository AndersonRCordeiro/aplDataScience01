import gradio as gr
import pandas as pd
import os
from datetime import datetime

ARQUIVO_CSV = "pacientes.csv"
COLUNAS = ["timestamp", "nome", "idade", "convenio", "prioridade", "motivo"]


def ler_ultimos():
    """Lê os últimos 5 registros do CSV, se existir."""
    if os.path.exists(ARQUIVO_CSV) and os.path.getsize(ARQUIVO_CSV) > 0:
        return pd.read_csv(ARQUIVO_CSV).tail(5)
    return pd.DataFrame(columns=COLUNAS)


def cadastrar_paciente(nome, idade, convenio, prioridade, motivo):
    """Grava uma nova linha no CSV e retorna mensagem + tabela atualizada."""
    if not nome or not str(nome).strip():
        return "Informe o nome do paciente.", ler_ultimos()

    linha = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": str(nome).strip(),
        "idade": int(idade) if idade is not None else 0,
        "convenio": convenio,
        "prioridade": int(prioridade) if prioridade is not None else 1,
        "motivo": str(motivo).strip(),
    }

    novo = pd.DataFrame([linha], columns=COLUNAS)

    if os.path.exists(ARQUIVO_CSV) and os.path.getsize(ARQUIVO_CSV) > 0:
        novo.to_csv(ARQUIVO_CSV, mode="a", header=False, index=False)
    else:
        novo.to_csv(ARQUIVO_CSV, mode="w", header=True, index=False)

    return "Paciente cadastrado com sucesso!", ler_ultimos()


with gr.Blocks(title="Cadastro de Pacientes") as demo:
    gr.Markdown("# Cadastro de Pacientes")
    gr.Markdown("Preencha os dados e clique em **Cadastrar**.")

    nome = gr.Textbox(label="Nome do paciente")
    idade = gr.Number(label="Idade", precision=0)
    convenio = gr.Dropdown(
        choices=["Particular", "Unimed", "Bradesco Saúde", "SulAmérica", "Outro"],
        label="Convênio",
        value="Particular",
    )
    prioridade = gr.Slider(
        minimum=1,
        maximum=5,
        step=1,
        label="Prioridade do atendimento",
        value=1,
    )
    motivo = gr.Textbox(label="Motivo da consulta / observações", lines=3)

    botao = gr.Button("Cadastrar", variant="primary")
    saida_msg = gr.Textbox(label="Status", interactive=False)
    tabela = gr.Dataframe(label="Últimos pacientes cadastrados", interactive=False)

    botao.click(
        fn=cadastrar_paciente,
        inputs=[nome, idade, convenio, prioridade, motivo],
        outputs=[saida_msg, tabela],
    ).then(
        fn=lambda: ("", None, "Particular", 1, ""),
        outputs=[nome, idade, convenio, prioridade, motivo],
    )

    demo.load(fn=ler_ultimos, outputs=tabela)


if __name__ == "__main__":
    demo.launch()