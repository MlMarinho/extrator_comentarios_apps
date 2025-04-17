#!/bin/bash

echo "Atualizando pip e instalando dependências..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo "Baixando dados de análise de sentimento (TextBlob)..."
python3 -m textblob.download_corpora

echo "Setup completo!"