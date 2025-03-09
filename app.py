import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_groq import ChatGroq
from htmlTemplates import css, bot_template, user_template


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            # text += "".join(page.extract_text().split("  "))
            text += page.extract_text()
    return text

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size= 1000, 
                                              chunk_overlap= 250,
                                              length_function=len,
                                              separators= "\n"
                                            #   is_separator_regex=False,
                                            )
    return splitter.split_text(text)

def get_vector_store(chunks):
    embedding_model= GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    vector_store = FAISS.from_texts(texts=chunks, embedding=embedding_model)
    return vector_store

def get_conversation(retriever):
    llm= ChatGroq(model="llama-3.2-11b-vision-preview")
    memory= ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever,
        memory=memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with Multiple PDFs", page_icon=":shark:", layout="wide")
    
    st.markdown(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with Multiple PDFs :books:")
    
    user_question=st.text_input("Enter your question here about your document")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your Documents :books:")
        pdf_docs=st.file_uploader("Upload your PDFs", type=["pdf"], accept_multiple_files=True)
        if st.button("Submit"):
            with st.spinner("Processing your documents..."):

                ## get the raw text from pdfs  
                raw_text = get_pdf_text(pdf_docs)
                # st.write(raw_text)

                ## get the text chunks
                chunks= get_text_chunks(raw_text)
                st.write(chunks)

                ## get vectorstore
                vector_store = get_vector_store(chunks)

                ## create retriever object
                retriever= vector_store.as_retriever()

                ## Conversation chains
                st.session_state.conversation = get_conversation(retriever)

                ## session state
                


   





if __name__ == "__main__":
    main()