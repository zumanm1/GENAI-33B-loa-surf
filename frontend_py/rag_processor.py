import os
import json
import requests
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain import hub
import logging
from logging.handlers import RotatingFileHandler

# --- Setup Logging --- #
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file = os.path.join(log_directory, "rag_processor.log")

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a rotating file handler
handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=3) # 1MB per file, 3 backups
handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add the handler to the logger, but avoid adding it multiple times
if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    logger.addHandler(handler)

# --- Default Configuration --- #
DEFAULT_CONFIG = {
    "ollama_model": "llama2",
    "embedding_model": "all-MiniLM-L6-v2",
    "ai_agent_type": "Default RAG Agent",
    "vector_store_path": "chroma_db_store"
}

# --- Configuration Loader --- #
def get_ai_config():
    """Fetches AI configuration from the backend API."""
    try:
        response = requests.get("http://127.0.0.1:5050/api/ai/config", timeout=3)
        if response.status_code == 200:
            logger.info("Successfully fetched AI config from backend.")
            return response.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not fetch AI config from backend: {e}. Using default config.")
    return DEFAULT_CONFIG

@tool
def get_router_config(device_name: str) -> str:
    """Fetches the running configuration for a specific router."""
    mock_configs = {
        "Router1": "hostname Router1\ninterface eth0/0\nip address 192.168.1.1 255.255.255.0",
        "Router2": "hostname Router2\ninterface eth0/1\nip address 10.0.0.1 255.255.255.0"
    }
    return mock_configs.get(device_name, f"Configuration for {device_name} not found.")

class RAGProcessor:
    def __init__(self, docs_path="uploads"):
        self.docs_path = docs_path
        self.vector_store = None
        self.config = get_ai_config()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.prompt_template = """Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Context: {context}
        Question: {question}
        Helpful Answer:"""
        self.PROMPT = PromptTemplate(
            template=self.prompt_template, input_variables=["context", "question"]
        )

    def _get_llm(self):
        """Initializes the LLM with the model from the config."""
        model_name = self.config.get("ollama_model", DEFAULT_CONFIG["ollama_model"])
        logger.info(f"Initializing Ollama with model: {model_name}")
        return ChatOllama(model=model_name)

    def _get_embeddings(self):
        """Initializes the embeddings with the model from the config."""
        # Note: OllamaEmbeddings doesn't use a separate embedding model name in the same way.
        # The model used for embeddings is tied to the Ollama instance model.
        # If you were using something like HuggingFaceEmbeddings, you'd use self.config.get('embedding_model').
        model_name = self.config.get("ollama_model", DEFAULT_CONFIG["ollama_model"])
        logger.info(f"Initializing OllamaEmbeddings for model: {model_name}")
        return OllamaEmbeddings(model=model_name)

    def process_documents(self):
        if not os.path.exists(self.docs_path) or not os.listdir(self.docs_path):
            logger.warning("Uploads directory is empty or does not exist. Skipping document processing.")
            return False
        try:
            loader = DirectoryLoader(self.docs_path, glob="**/*.txt")
            documents = loader.load()
            if not documents:
                logger.warning("No documents found to process.")
                return False
            
            texts = self.text_splitter.split_documents(documents)
            embeddings = self._get_embeddings()
            self.vector_store = Chroma.from_documents(texts, embeddings)
            logger.info("Documents processed and vector store created successfully.")
            return True
        except Exception as e:
            logger.error(f"Error processing documents: {e}")
            return "An error occurred while processing your request. Please ensure Ollama is running and the model is available."

    def query(self, question: str):
        if self.vector_store is None:
            logger.warning("Vector store not initialized. Processing documents first.")
            processed = self.process_documents()
            if not processed:
                return "Vector store is not available. Please upload documents first."

        try:
            llm = self._get_llm()
            qa_chain = RetrievalQA.from_chain_type(
                llm,
                retriever=self.vector_store.as_retriever(),
                chain_type_kwargs={"prompt": self.PROMPT}
            )
            result = qa_chain({"query": question})
            return result["result"]
        except Exception as e:
            logger.error(f"Error during query: {e}")
            return "An error occurred. Ensure Ollama is running and documents have been uploaded."

    def agent_chat(self, question: str):
        try:
            llm = self._get_llm()
            tools = [get_router_config]
            prompt = hub.pull("hwchase17/openai-functions-agent")
            
            agent = create_tool_calling_agent(llm, tools, prompt)
            agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            
            response = agent_executor.invoke({"input": question})
            return response.get("output", "No output from agent.")
        except Exception as e:
            logger.error(f"Error in agent_chat: {e}")
            return "An error occurred while processing your agent request. Please ensure Ollama is running."

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
