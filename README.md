# Burbello Tools

Este repositório apresenta códigos feitos em Python de scripts com o intuito de otimizar alguns processos dentro do Escritório Burbello.

## 📋 Sobre

Aplicativo em [Streamlit](https://streamlit.io/) com ferramentas internas para agilizar tarefas rotineiras do escritório, reunidas em uma única interface web.

## 🛠️ Ferramentas disponíveis

### 🏢 Consultor de CNPJ
Consulta em lote a Razão Social de múltiplos CNPJs a partir da API pública [ReceitaWS](https://receitaws.com.br/), com:
- Entrada de vários CNPJs de uma vez (separados por vírgula)
- Tratamento automático de limite de requisições (rate limit)
- Exportação dos resultados em CSV (separado por `;`, compatível com Excel BR)

### 📄 Extrator de Folha de Pagamento
Extrai automaticamente informações de PDFs de folha de pagamento, como:
- Código e nome da empresa
- Quantidade de funcionários
- Total líquido
- FGTS (mensal, 13º e consignado)
- INSS, IRRF, contribuição sindical e total DCTFWeb

Os dados extraídos ficam salvos localmente (`dados_folhas.json`) e podem ser exportados em um único CSV consolidado.

## 🚀 Como rodar localmente

```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>
pip install -r requirements.txt
streamlit run app_burbello.py
```

O app abre automaticamente no navegador em `http://localhost:8501`.

## ☁️ Deploy no Streamlit Cloud

1. Suba o repositório para o GitHub, garantindo que `app_burbello.py` e `requirements.txt` estejam na raiz (ou no mesmo diretório configurado no deploy).
2. Em [share.streamlit.io](https://share.streamlit.io/), aponte para o repositório e o arquivo `app_burbello.py`.
3. Qualquer novo `push` no repositório atualiza o app automaticamente. Se as dependências mudarem, pode ser necessário reiniciar o app manualmente ("Manage app" → "Reboot app").

## 📦 Dependências

Listadas em [`requirements.txt`](./requirements.txt):
- `streamlit`
- `requests`
- `pdfplumber`

## 📁 Estrutura

```
.
├── app_burbello.py     # App principal (Consultor de CNPJ + Extrator de Folha)
├── requirements.txt    # Dependências do projeto
├── logo-site.png        # Logo exibida no topo do app (opcional)
└── dados_folhas.json    # Gerado automaticamente com os dados extraídos das folhas
```

## ⚠️ Observações

- O `dados_folhas.json` é salvo localmente no ambiente onde o app roda. No Streamlit Cloud, esse arquivo não é persistido entre reinicializações do servidor — para um histórico compartilhado e permanente entre a equipe, é recomendável migrar para um banco de dados (SQLite, Google Sheets, etc).
- A consulta de CNPJ depende da disponibilidade da API pública ReceitaWS e está sujeita a limites de requisições.
