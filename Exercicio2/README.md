# TechFix Informática — Sistema de Ordens de Serviço

Integração de interface web (Gradio) + painel administrativo (Streamlit)
com banco de dados em nuvem (Supabase/PostgreSQL).

## Estrutura

```
.
├── sql/schema.sql          # DDL completo
├── app_gradio.py           # cadastro de OS (mobile)
├── app_streamlit.py        # painel CRUD
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── evidencias/
```

## 1. Configurar o banco

1. Crie um projeto em https://supabase.com
2. Abra **SQL Editor** e execute o conteúdo de `sql/schema.sql`
3. Em **Project Settings → API**, copie `Project URL` e `anon public key`

## 2. Configurar credenciais

```bash
cp .env.example .env
# edite .env com URL e KEY reais
```

> Para o Streamlit, opcionalmente crie `.streamlit/secrets.toml`:
> ```toml
> SUPABASE_URL = "https://xxxx.supabase.co"
> SUPABASE_KEY = "eyJhbGci..."
> ```

## 3. Instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Executar o app de atendimento (Gradio)

```bash
python app_gradio.py
# abre localmente e gera link público (share=True) para acessar no celular
```

## 5. Executar o painel administrativo (Streamlit)

```bash
streamlit run app_streamlit.py
```

## 6. Evidências a capturar (pasta `evidencias/`)

- (a) Tela do Gradio aberta no celular
- (b) Mensagem de cadastro realizado
- (c) Tabelas preenchidas no Table Editor do Supabase
- (d) Painel Streamlit com Consultar, Editar e Indicadores
