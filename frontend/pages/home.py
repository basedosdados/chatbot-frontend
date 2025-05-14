import streamlit as st


# Page config, Title and welcome message
st.set_page_config(
    page_title="Chatbot BD",
    page_icon="https://api.dicebear.com/9.x/initials/svg?seed=BD&radius=20&backgroundColor=34a853&fontFamily=sans-serif&fontWeight=800",
)

st.title("Chatbot BD")
st.caption("Para consultas em bases de dados utilizando linguagem natural")

st.write("\n")

st.subheader("Bem Vindo(a)! :wave:")
st.write(f"Bem vindo(a) ao chatbot da BD! Ele vai te ajudar a conversar com seus dados! Basta entrar na página de chat no menu à esquerda e começar a conversa. Faça perguntas sobre os dados disponíveis <br/> e o chatbot dará o seu melhor para respondê-las!", unsafe_allow_html=True)

st.write("\n")

# Available models
st.subheader("Modelo :brain:")
st.write("O modelo por trás do chatbot é o Gemini, do Google.")

st.write("\n")

# Available features
st.subheader("Funcionalidades :memo:")
st.write("""
         - **Botão de Reset (:blue[:material/refresh:]):** clique no botão de reset para reiniciar a conversa com o chatbot, limpando a sua memória e o histórico de conversa, sem precisar sair da aplicação.
         - **Botão de Download (:blue[:material/download:]):** clique no botão de download para exportar a **conversa** para um arquivo CSV. Apenas a **conversa** é exportada, e não os dados/tabelas disponíveis.
         - **Botão de Gráfico (:blue[:material/bar_chart:]):** clique no botão de gráfico para exibir ou ocultar o gráfico gerado pelo chatbot. Ele pode gerar gráficos de barras verticais e horizontais, linhas, setores e de dispersão.
         - **Botão de Código (:blue[:material/code:]):** clique no botão de código para exibir ou ocultar como o chatbot está fazendo as consultas nas bases de dados. O chatbot faz consultas em bases de dados armazenadas na nuvem usando linguagem SQL.
         - **Botões de Feedback (:blue[:material/thumb_up:] ou :blue[:material/thumb_down:]):** clique nos botões de feedback para enviar feedbacks sobre as respostas recebidas, com comentários opcionais. É necessário clicar no botão de envio (:material/send:) para que o feedback seja enviado.""")

st.write("\n")

# Prompting guide
st.subheader("Guia de Prompt :clipboard:")
st.write("A forma como você conversa com o chatbot pode influenciar na qualidade das respostas! Por isso, abaixo estão listadas algumas dicas para te ajudar a elaborar suas perguntas. Elas podem ser úteis caso as respostas fornecidas estejam incorretas ou não sejam boas o suficiente!")
st.write("""
         1. Tente fazer uma pergunta por vez. Caso sua pergunta seja muito complexa, ou talvez seja um conjunto de várias perguntas, tente separá-la em perguntas menores e mais simples.
         2. Tente utilizar termos como "**por**" ou "**total**" quando precisar de informações agregadas segundo alguma variável. Por exemplo, se quiser saber a porcentagem de estudantes leitores **por** raça ou o **total** de matrículas em um ano específico.
         3. Caso saiba os nomes das colunas das tabelas, tente mencioná-los nas suas perguntas. Por exemplo, se você sabe que uma tabela possui a coluna "**município**", tente usar a palavra **município** ao invés de "cidade". Isso não significa que você não possa usar palavras parecidas, mas usar os nomes das colunas ajuda o chatbot.
         4. Caso o chatbot não esteja encontrando uma resposta para a sua pergunta e você saiba em qual tabela estão os dados necessários para respondê-la, você pode tentar pedir explicitamente ao chatbot para procurar nessa tabela específica.""")

st.write("\n")

# Important information
st.subheader(":gray[:material/info:] Importante")
st.write("""
         - Quando enviar uma pergunta ao chatbot, espere até que uma resposta seja fornecida antes de trocar de página ou clicar em qualquer botão dentro da aplicação. Você pode alternar entre as abas do seu navegador normalmente.
         - Após sair da aplicação ou fechá-la, o histórico de conversa e a memória do chatbot serão deletados.""")
