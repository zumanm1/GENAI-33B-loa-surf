import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.chat_models import ChatOllama
from langchain.chains import RetrievalQA
from langchain.agents import AgentType, initialize_agent, Tool
import requests

VECTOR_STORE_PATH = 'vector_store'
if not os.path.exists(VECTOR_STORE_PATH):
    os.makedirs(VECTOR_STORE_PATH)

VECTOR_STORE_INDEX = os.path.join(VECTOR_STORE_PATH, 'faiss_index')

def get_text_from_documents(file_paths):
    """Load text from a list of documents (PDFs, TXTs)."""
    documents = []
    for file_path in file_paths:
        if file_path.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file_path.lower().endswith('.txt') or file_path.lower().endswith('.md'):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
    return documents

def get_text_chunks(documents):
    """Split documents into chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def get_vector_store(text_chunks):
    """Create or update the FAISS vector store."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    if os.path.exists(VECTOR_STORE_INDEX):
        # Load existing vector store and add new documents
        vector_store = FAISS.load_local(VECTOR_STORE_INDEX, embeddings, allow_dangerous_deserialization=True)
        vector_store.add_documents(text_chunks)
    else:
        # Create a new vector store
        vector_store = FAISS.from_documents(documents=text_chunks, embedding=embeddings)
        
    vector_store.save_local(VECTOR_STORE_INDEX)
    print(f"Vector store updated and saved at {VECTOR_STORE_INDEX}")

def handle_rag_query(query):
    """Handle a user query using the RAG pipeline."""
    if not os.path.exists(VECTOR_STORE_INDEX):
        return "Vector store not found. Please upload documents first."

    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.load_local(VECTOR_STORE_INDEX, embeddings, allow_dangerous_deserialization=True)
        
        # Initialize the local LLM
        # IMPORTANT: Make sure you have Ollama running with the specified model pulled.
        # e.g., run `ollama run llama2` in your terminal.
        llm = ChatOllama(model="llama2")

        # Create the RetrievalQA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )

        response = qa_chain.invoke(query)
        return response.get('result', 'No answer could be generated.')

    except Exception as e:
        print(f"An error occurred during RAG query processing: {e}")
        return "An error occurred while processing your request. Please ensure Ollama is running and the model is available."


def get_device_config(hostname: str) -> str:
    """Tool for the AI agent. Fetches the running configuration for a specific device by its hostname."""
    try:
        # This tool requires an authenticated session, which we don't have here.
        # This is a known limitation we will address later by passing the session.
        # For now, we will mock the response for demonstration purposes.
        mock_configs = {
            "core-router-01": "interface GigabitEthernet0/1\n ip address 192.168.1.1 255.255.255.0\n no shutdown",
            "access-switch-01": "interface Vlan10\n ip address 10.10.10.1 255.255.255.0\n name USERS",
            "dist-switch-01": "router ospf 1\n network 10.0.0.0 0.255.255.255 area 0"
        }
        config = mock_configs.get(hostname, f"No configuration found for device '{hostname}'.")
        return f"The configuration for {hostname} is:\n\n{config}"
    except Exception as e:
        return f"An error occurred while fetching config for {hostname}: {e}"

def get_list_of_devices():
    """Tool for the AI agent. Fetches the list of network devices from the backend API."""
    try:
        response = requests.get("http://127.0.0.1:5050/api/devices")
        response.raise_for_status() # Raise an exception for bad status codes
        devices = response.json()
        # Format the output for the LLM
        return f"Here are the devices I can interact with: {', '.join([d['hostname'] for d in devices])}"
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "I was unable to fetch the list of devices from the backend."


def handle_agent_query(query):
    """Handle a user query using the AI Agent."""
    try:
        llm = ChatOllama(model="llama2")
        tools = [
            Tool(
                name="GetListOfDevices",
                func=get_list_of_devices,
                description="Use this tool to get the hostnames of all available network devices. It takes no arguments."
            ),
            Tool(
                name="GetDeviceConfig",
                func=get_device_config,
                description="Use this tool to get the running configuration for a specific network device. It requires a single argument: the hostname of the device."
            )
        ]

        # Initialize the agent
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True # Set to True for debugging to see the agent's thoughts
        )

        response = agent.invoke({"input": query})
        return response.get('output', 'The agent did not return a response.')

    except Exception as e:
        print(f"An error occurred during Agent query processing: {e}")
        return "An error occurred while processing your agent request. Please ensure Ollama is running."

def process_and_store_documents(file_paths):
    """Main function to process uploaded files and update the vector store."""
    full_file_paths = [os.path.join('uploads', f) for f in file_paths]
    documents = get_text_from_documents(full_file_paths)
    if not documents:
        print("No documents were loaded. Check file paths and types.")
        return
    
    text_chunks = get_text_chunks(documents)
    get_vector_store(text_chunks)
