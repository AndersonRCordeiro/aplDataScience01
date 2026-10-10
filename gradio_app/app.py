import gradio as gr
import pandas as pd
import os
from datetime import datetime

ARQUIVO_CSV = "pacientes.csv"
COLUNAS = [
    "timestamp", "nome", "idade", "telefone", "convenio",
    "carteirinha", "prioridade", "motivo",
    "responsavel_nome", "responsavel_telefone",
]


def ler_ultimos():
    """Lê os últimos 5 registros do CSV, se existir."""
    if os.path.exists(ARQUIVO_CSV) and os.path.getsize(ARQUIVO_CSV) > 0:
        return pd.read_csv(ARQUIVO_CSV).tail(5)
    return pd.DataFrame(columns=COLUNAS)


def valor_padrao_form():
    """Valores padrão para limpar o formulário após um cadastro com sucesso."""
    return (
        "",                                  # nome
        None,                                # idade
        "",                                  # telefone
        "Particular",                        # convenio
        gr.update(value="", visible=False),  # carteirinha
        1,                                   # prioridade
        "",                                  # motivo
        gr.update(value="", visible=False),  # responsavel_nome
        gr.update(value="", visible=False),  # responsavel_telefone
    )


def atualizar_responsavel(idade):
    """Mostra os campos de responsável se a idade for menor que 18."""
    menor = idade is not None and float(idade) < 18
    return gr.update(visible=menor), gr.update(visible=menor)


def atualizar_carteirinha(convenio):
    """Mostra o campo de carteirinha se o convênio não for 'Particular'."""
    return gr.update(visible=convenio != "Particular")


def cadastrar_paciente(nome, idade, telefone, convenio, carteirinha,
                       prioridade, motivo, responsavel_nome, responsavel_telefone):
    """Valida, grava no CSV e limpa o formulário."""

    def erro(msg):
        """Retorna mensagem de erro sem limpar o formulário."""
        return (
            msg, ler_ultimos(),
            nome, idade, telefone, convenio, carteirinha,
            prioridade, motivo, responsavel_nome, responsavel_telefone,
        )

    if not nome or not str(nome).strip():
        return erro("Informe o nome do paciente.")

    idade_int = int(idade) if idade is not None else 0
    menor = idade_int < 18
    precisa_carteirinha = convenio != "Particular"

    if menor and (not responsavel_nome or not str(responsavel_nome).strip()):
        return erro("Paciente menor de 18 anos: informe o nome do responsável.")

    if menor and (not responsavel_telefone or not str(responsavel_telefone).strip()):
        return erro("Paciente menor de 18 anos: informe o telefone do responsável.")

    if precisa_carteirinha and (not carteirinha or not str(carteirinha).strip()):
        return erro(f"Convênio '{convenio}': informe o número da carteirinha.")

    linha = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nome": str(nome).strip(),
        "idade": idade_int,
        "telefone": str(telefone).strip() if telefone else "",
        "convenio": convenio,
        "carteirinha": (
            str(carteirinha).strip()
            if precisa_carteirinha and carteirinha else ""
        ),
        "prioridade": int(prioridade) if prioridade is not None else 1,
        "motivo": str(motivo).strip(),
        "responsavel_nome": (
            str(responsavel_nome).strip() if menor and responsavel_nome else ""
        ),
        "responsavel_telefone": (
            str(responsavel_telefone).strip() if menor and responsavel_telefone else ""
        ),
    }

    novo = pd.DataFrame([linha], columns=COLUNAS)

    if os.path.exists(ARQUIVO_CSV) and os.path.getsize(ARQUIVO_CSV) > 0:
        novo.to_csv(ARQUIVO_CSV, mode="a", header=False, index=False)
    else:
        novo.to_csv(ARQUIVO_CSV, mode="w", header=True, index=False)

    return ("Paciente cadastrado com sucesso!", ler_ultimos()) + valor_padrao_form()


with gr.Blocks(title="Cadastro de Pacientes") as demo:
    gr.Markdown("# Cadastro de Pacientes")
    gr.Markdown("Preencha os dados e clique em **Cadastrar**.")

    nome = gr.Textbox(label="Nome do paciente")
    idade = gr.Number(label="Idade", precision=0)
    telefone = gr.Textbox(label="Telefone do paciente")

    # Campos que só aparecem para menores de 18 anos
    responsavel_nome = gr.Textbox(
        label="Nome do responsável (menor de 18 anos)", visible=False
    )
    responsavel_telefone = gr.Textbox(
        label="Telefone do responsável (menor de 18 anos)", visible=False
    )

    convenio = gr.Dropdown(
        choices=["Particular", "Unimed", "Bradesco Saúde", "SulAmérica", "Outro"],
        label="Convênio",
        value="Particular",
    )
    # Campo que só aparece quando o convênio não é Particular
    carteirinha = gr.Textbox(
        label="Número da carteirinha do plano", visible=False
    )

    prioridade = gr.Slider(
        minimum=1, maximum=5, step=1,
        label="Prioridade do atendimento", value=1,
    )
    motivo = gr.Textbox(label="Motivo da consulta / observações", lines=3)

    botao = gr.Button("Cadastrar", variant="primary")
    saida_msg = gr.Textbox(label="Status", interactive=False)
    tabela = gr.Dataframe(label="Últimos pacientes cadastrados", interactive=False)

    # Mostra/esconde campos conforme idade e convênio
    idade.change(
        fn=atualizar_responsavel,
        inputs=idade,
        outputs=[responsavel_nome, responsavel_telefone],
    )
    convenio.change(
        fn=atualizar_carteirinha,
        inputs=convenio,
        outputs=carteirinha,
    )

    botao.click(
        fn=cadastrar_paciente,
        inputs=[nome, idade, telefone, convenio, carteirinha,
                prioridade, motivo, responsavel_nome, responsavel_telefone],
        outputs=[saida_msg, tabela,
                 nome, idade, telefone, convenio, carteirinha,
                 prioridade, motivo,
                 responsavel_nome, responsavel_telefone],
    )

    demo.load(fn=ler_ultimos, outputs=tabela)


if __name__ == "__main__":
    demo.launch()