import streamlit as st


TABLES = {
    "Avaliação de Fluência Leitora da PARC": {
        "description": "Variáveis principais: Ano, Momento Avaliação, Sigla UF, Nome Município, Rede, Localização, Sexo, Raça/Cor, Perfil, Detalhamento Perfil",
        "link": "https://coda.io/d/_doJyOPr-NIX/Tabelas_suRf37t1#br-fundacao-lemann-alfabetizacao-avaliacao-fluencia-parc-aluno_tu-lkwy3"
    },
    "Ideb dos Municípios": {
        "description": "Variáveis principais: Ano, Município, Sigla UF, Anos Escolares, Taxa Aprovação, Indicador Rendimento, Nota SAEB Matemática, Nota SAEB Língua Portuguesa, Nota SAEB Média Padronizada, Ideb, Programa",
        "link": "https://coda.io/d/_doJyOPr-NIX/Tabelas_suRf37t1#ideb-municipio-programas-fl_tu6xUAan"
    },
    "Ideb das UFs": {
        "description": "Variáveis principais: Ano, Sigla UF, Anos Escolares, Taxa Aprovação, Indicador Rendimento, Nota SAEB Matemática, Nota SAEB Língua Portuguesa, Nota SAEB Média Padronizada, Ideb, Programa",
        "link": "https://coda.io/d/_doJyOPr-NIX/Tabelas_suRf37t1#ideb-uf-programas-fl_tukZ-YYg"
    },
    "Egressos de Oportunidades de Desenvolvimento de Liderança": {
        "description": "Variáveis principais: Organização, Programa, Raça, Sexo, UF, Região, Setor, Cargo Padronizado, Instituição, Tema, PAF",
        "link": "https://coda.io/d/_doJyOPr-NIX/Tabelas_suRf37t1#br-fundacao-lemann-egressos_tuj-dKlq"
    },
    "Sinopse Estatística do Censo Escolar - Etapa de Ensino e Série": {
        "description": "Variáveis principais: Ano, Sigla UF, Município, Rede, Etapa de Ensino, Série, Quantidade de Matrículas",
        "link": "https://coda.io/d/_doJyOPr-NIX/Tabelas_suRf37t1#sinopse-estatistica-etapa-ensino-serie-programas-fl_tuSX-LEz"
    },
    "Sinopse Estatística do Censo Escolar - Etapa e Tempo Integral": {
        "description": "Variáveis principais: Ano, Sigla UF, Município, Rede, Etapa de Ensino, Tempo de Ensino, Quantidade de Matrículas",
        "link": "https://coda.io/d/_doJyOPr-NIX/Tabelas_suRf37t1#sinopse-estatistica-tempo-ensino-programas-fl_tuUTtjLa"
    }
}

N_TABLES_COLUMNS = 1

# Page config, Title and welcome message
st.set_page_config(
    page_title="Assistente BD & FL",
    page_icon="https://api.dicebear.com/9.x/initials/svg?seed=BD&radius=20&backgroundColor=34a853&fontFamily=sans-serif&fontWeight=800",
)

st.title("Assistente BD & FL")
st.caption("Para consultas em bases de dados utilizando linguagem natural")

st.write("\n")

st.subheader("Bem Vindo(a)! :wave:")
st.write(f"Bem vindo(a) ao assistente da BD & FL! Ele vai te ajudar a conversar com seus dados! Basta entrar na página de chat no menu à esquerda e começar a conversa. Faça perguntas sobre os dados disponíveis <br/> e o assistente dará o seu melhor para respondê-las!", unsafe_allow_html=True)

st.write("\n")

# Available models
st.subheader("Modelo :brain:")
st.write("O modelo por trás do assistente é o GPT-4o, da OpenAI.")

st.write("\n")

# Available tables
st.subheader("Tabelas :card_index_dividers:")
st.write("As tabelas disponíveis para consulta são as seguintes:")

columns = {
    col_num: col for col_num, col in enumerate(st.columns(N_TABLES_COLUMNS))
}

for i, (table_name, table_info) in enumerate(TABLES.items()):
    col = columns[i%N_TABLES_COLUMNS]
    description = table_info["description"]
    link = table_info["link"]
    with col.expander(f":blue[{table_name}]"):
        st.write(description)
        st.write(f"[Documentação]({link})")

st.write("\n")

# Available features
st.subheader("Funcionalidades :memo:")
st.write("""
         - **Botão de Reset (:blue[:material/refresh:]):** clique no botão de reset para reiniciar a conversa com o assistente, limpando a sua memória e o histórico de conversa, sem precisar sair da aplicação.
         - **Botão de Download (:blue[:material/download:]):** clique no botão de download para exportar a **conversa** para um arquivo CSV. Apenas a **conversa** é exportada, e não os dados/tabelas disponíveis.
         - **Botão de Gráfico (:blue[:material/bar_chart:]):** clique no botão de gráfico para exibir ou ocultar o gráfico gerado pelo assistente. Ele pode gerar gráficos de barras verticais e horizontais, linhas, setores e de dispersão.
         - **Botão de Código (:blue[:material/code:]):** clique no botão de código para exibir ou ocultar como o assistente está fazendo as consultas nas bases de dados. O assistente faz consultas em bases de dados armazenadas na nuvem usando linguagem SQL.
         - **Botões de Feedback (:blue[:material/thumb_up:] ou :blue[:material/thumb_down:]):** clique nos botões de feedback para enviar feedbacks sobre as respostas recebidas, com comentários opcionais. É necessário clicar no botão de envio (:material/send:) para que o feedback seja enviado.""")

st.write("\n")

# Prompting guide
st.subheader("Guia de Prompt :clipboard:")
st.write("A forma como você conversa com o assistente pode influenciar na qualidade das respostas! Por isso, abaixo estão listadas algumas dicas para te ajudar a elaborar suas perguntas. Elas podem ser úteis caso as respostas fornecidas estejam incorretas ou não sejam boas o suficiente!")
st.write("""
         1. Tente fazer uma pergunta por vez. Caso sua pergunta seja muito complexa, ou talvez seja um conjunto de várias perguntas, tente separá-la em perguntas menores e mais simples.
         2. Tente utilizar termos como "**por**" ou "**total**" quando precisar de informações agregadas segundo alguma variável. Por exemplo, se quiser saber a porcentagem de estudantes leitores **por** raça ou o **total** de matrículas em um ano específico.
         3. Caso saiba os nomes das colunas das tabelas, tente mencioná-los nas suas perguntas. Por exemplo, se você sabe que uma tabela possui a coluna "**município**", tente usar a palavra **município** ao invés de "cidade". Isso não significa que você não possa usar palavras parecidas, mas usar os nomes das colunas ajuda o assistente.
         4. Caso o assistente não esteja encontrando uma resposta para a sua pergunta e você saiba em qual tabela estão os dados necessários para respondê-la, você pode tentar pedir explicitamente ao assistente para procurar nessa tabela específica.""")

st.write("\n")

# Important information
st.subheader(":gray[:material/info:] Importante")
st.write("""
         - Quando enviar uma pergunta ao assistente, espere até que uma resposta seja fornecida antes de trocar de página ou clicar em qualquer botão dentro da aplicação. Você pode alternar entre as abas do seu navegador normalmente.
         - Após sair da aplicação ou fechá-la, o histórico de conversa e a memória do assistente serão deletados.""")
