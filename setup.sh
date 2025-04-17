#!/bin/bash

# Atualizando e instalando dependências
echo "Atualizando e instalando dependências..."

# Atualizar o pip
python3 -m pip install --upgrade pip

# Instalar as bibliotecas necessárias
pip install -r requirements.txt

# Baixar corpora do TextBlob (necessário para análise de sentimento)
python3 -m textblob.download_corpora

echo "Dependências instaladas com sucesso!"
