# extrator_comentarios_apps
📁 Estrutura de diretórios

meu_app_comentarios/
│
├── extract_unified_web.py                  # Seu aplicativo Streamlit principal
├── requirements.txt        # Todas as dependências do projeto
├── setup.sh                # Script para configurar dependências (Linux/Mac)
└── Procfile                # (Opcional) Necessário para Heroku, ignorado no Streamlit Cloud

✅ requirements.txt
Completo, com todas as dependências corretas

✅ setup.sh
Para rodar localmente ou configurar manualmente


🚀 Como usar (local ou cloud)
👉 Localmente:

chmod +x setup.sh
./setup.sh
streamlit run app.py

👉 No Streamlit Cloud:

    Crie um repositório no GitHub com esses arquivos.

    Vá para o Streamlit Cloud e clique em “New app”.

    Selecione seu repositório e app.py.

    Pronto!