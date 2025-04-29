# Interface do Chatbot da BD, feita com [Streamlit](https://streamlit.io/)

## Instruções
A interface do chatbot pode ser executada localmente utilizando o Docker ou o Python.

### Docker
Instale o Docker seguindo as [instruções de instalação](https://docs.docker.com/engine/install/), de acordo com a distribuição linux que você usa. Em seguida, a partir da raiz deste repositório, execute os comandos:
```
docker build -t <nome-da-tag>:latest .
docker run <nome-da-tag>:latest
```
> [!TIP]
> Você pode adicionar a flag `--rm` ao comando `docker run` para remover o container após a sua execução.
### Python

Crie um ambiente virtual e ative-o:
```
python3 -m venv <caminho-para-o-venv>
. <caminho-para-o-venv>/bin/activate
```
Em seguida, a partir da raíz deste repositório, instale o pacote:
```
pip install --upgrade pip
pip install .
```
E execute-o utilizando o streamlit:
```
streamlit run frontend/main.py
```
> [!TIP]
> - Você pode adicionar a flag `-e` para instalar o pacote no modo editável durante o desenvolvimento.
> - Você pode criar o ambiente virtual e fazer a instalação do pacote utilizando ferramentas como o [uv](https://docs.astral.sh/uv/) ou o [poetry](https://python-poetry.org/docs/).
