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


def get_device_config(hostname: str, api_session: requests.Session) -> str:
    """Tool for the AI agent. Fetches the running configuration for a specific device by its hostname."""
    try:
        response = api_session.get(f"http://127.0.0.1:5050/api/devices/{hostname}")
        if response.status_code == 404:
            return f"Device with hostname '{hostname}' not found."
        response.raise_for_status()
        config = response.json().get('config', 'No configuration available.')
        return f"The configuration for {hostname} is:\n\n{config}"
    except requests.RequestException as e:
        return f"An API error occurred while fetching config for {hostname}: {e}"

def get_list_of_devices(api_session: requests.Session) -> str:
    """Tool for the AI agent. Fetches the list of network devices from the backend API."""
    try:
        response = api_session.get("http://127.0.0.1:5050/api/devices")
        response.raise_for_status() # Raise an exception for bad status codes
        devices = response.json()
        # Format the output for the LLM
        return f"Here are the devices I can interact with: {', '.join([d['hostname'] for d in devices])}"
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return "I was unable to fetch the list of devices from the backend."


def propose_config_change(hostname: str, config_changes: str, api_session: requests.Session) -> str:
    """Tool for the Agentic RAG. Proposes a configuration change for a specific device."""
    try:
        payload = {
            'hostname': hostname,
            'proposed_config': config_changes,
            'description': 'Proposed by GENAI Networks Engineer'
        }
        response = api_session.post("http://127.0.0.1:5050/api/baseline/proposals", json=payload)
        response.raise_for_status()
        return f"Successfully proposed configuration changes for {hostname}. Awaiting human review."
    except requests.RequestException as e:
        return f"Failed to propose changes for {hostname}: {e}"

def handle_agentic_rag_query(query, api_session: requests.Session):
    """Handle a query using an agent that can both retrieve information and use tools."""
    try:
        llm = ChatOllama(model="llama2")
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_store = FAISS.load_local(VECTOR_STORE_INDEX, embeddings, allow_dangerous_deserialization=True)

        # Create a RAG tool
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever()
        )

        from functools import partial
        tools = [
            Tool(
                name="KnowledgeBaseSearch",
                func=rag_chain.invoke,
                description="Use this to answer questions based on uploaded documents. Input should be a user's question."
            ),
            Tool(
                name="GetListOfDevices",
                func=partial(get_list_of_devices, api_session=api_session),
                description="Use this to get the hostnames of all available network devices."
            ),
            Tool(
                name="GetDeviceConfig",
                func=partial(get_device_config, api_session=api_session),
                description="Use this to get the running configuration for a specific network device. Requires hostname."
            ),
            Tool(
                name="ProposeConfigChange",
                func=partial(propose_config_change, api_session=api_session),
                description="Use this to propose a new configuration for a device. Requires hostname and the new config snippet."
            )
        ]

        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

        response = agent.invoke({"input": query})
        return response.get('output', 'The agent did not return a response.')

    except Exception as e:
        print(f"An error occurred during Agentic RAG query processing: {e}")
        return "An error occurred. Ensure Ollama is running and documents have been uploaded."

def handle_agent_query(query, api_session: requests.Session):
    """Handle a user query using the AI Agent."""
    try:
        llm = ChatOllama(model="llama2")
        # Bind the authenticated session to the tool functions
        from functools import partial
        get_list_of_devices_with_session = partial(get_list_of_devices, api_session=api_session)
        get_device_config_with_session = partial(get_device_config, api_session=api_session)

        tools = [
            Tool(
                name="GetListOfDevices",
                func=get_list_of_devices_with_session,
                description="Use this tool to get the hostnames of all available network devices. It takes no arguments."
            ),
            Tool(
                name="GetDeviceConfig",
                func=get_device_config_with_session,
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
