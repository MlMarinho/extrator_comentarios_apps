#!/bin/bash

# Atualiza pacotes e instala dependências básicas
apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpython3-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1-mesa-glx \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Instala as bibliotecas Python listadas no requirements.txt
pip install --upgrade pip
pip install -r requirements.txt