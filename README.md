# Interface do Chatbot da BD, feita com [Streamlit](https://streamlit.io/)

## Instruções
Copie o arquivo `.env.example` e ajuste os valores:
```bash
cp .env.example .env
```
Em seguida, execute a aplicação localmente utilizando o Docker ou o Python. 

### Docker
Instale o Docker seguindo as [instruções de instalação](https://docs.docker.com/engine/install/), de acordo com a distribuição linux que você usa. Em seguida, a partir da raiz do repositório, construa a imagem:
```bash
docker build -t nome-da-tag:latest .
```
E execute o container:
```bash
docker run --env-file .env -p 8501:8501 nome-da-tag:latest
```
A aplicação estará disponível em `http://localhost:8501`

> [!TIP]
> Você pode adicionar a flag `--rm` ao comando `docker run` para remover o container após a sua execução.
### Python

Instale o [Poetry](https://python-poetry.org/docs/). Em seguida, a partir da raíz do repositório, instale o pacote: 
```bash
poetry install
```

E execute a aplicação utilizando o streamlit:
```bash
streamlit run frontend/main.py
```
