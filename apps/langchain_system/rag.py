"""
RAG (Retrieval-Augmented Generation) System for ConcordBroker
Manages document retrieval and knowledge base operations
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    JSONLoader,
    CSVLoader
)
# PDFLoader might need separate installation
try:
    from langchain_community.document_loaders import PyPDFLoader as PDFLoader
except ImportError:
    PDFLoader = None
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import Document

logger = logging.getLogger(__name__)

class PropertyRAGSystem:
    """
    RAG system specialized for property data and real estate documents
    """
    
    def __init__(self, llm, embeddings):
        self.llm = llm
        self.embeddings = embeddings
        
        # Text splitter configurations
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Vector stores for different document types
        self.vector_stores = {}
        self._initialize_vector_stores()
        
        # Document loaders
        self.loaders = {
            'txt': TextLoader,
            'json': JSONLoader,
            'csv': CSVLoader
        }
        if PDFLoader:
            self.loaders['pdf'] = PDFLoader
        
        # RAG chains
        self.chains = {}
    
    def _initialize_vector_stores(self):
        """Initialize vector stores for different document categories"""
        
        categories = [
            'property_listings',
            'tax_records',
            'legal_documents',
            'market_reports',
            'building_codes',
            'investment_guides'
        ]
        
        for category in categories:
            store_path = f"./vector_stores/{category}"
            Path(store_path).mkdir(parents=True, exist_ok=True)
            
            # Try to load existing store or create new one
            try:
                self.vector_stores[category] = FAISS.load_local(
                    store_path,
                    self.embeddings
                )
                logger.info(f"Loaded existing vector store: {category}")
            except:
                # Create new store with dummy document
                self.vector_stores[category] = FAISS.from_texts(
                    [f"Initial document for {category}"],
                    self.embeddings,
                    metadatas=[{"category": category, "created": str(datetime.now())}]
                )
                logger.info(f"Created new vector store: {category}")
    
    def load_documents(self, path: str, category: str = "general", 
                       file_pattern: str = "**/*") -> List[Document]:
        """
        Load documents from a directory
        
        Args:
            path: Directory path containing documents
            category: Category for the documents
            file_pattern: Glob pattern for file selection
        
        Returns:
            List of loaded documents
        """
        
        documents = []
        path_obj = Path(path)
        
        if not path_obj.exists():
            logger.warning(f"Path does not exist: {path}")
            return documents
        
        # Load different file types
        for file_path in path_obj.glob(file_pattern):
            if file_path.is_file():
                ext = file_path.suffix[1:].lower()
                
                if ext in self.loaders:
                    try:
                        loader_class = self.loaders[ext]
                        
                        if ext == 'json':
                            # Special handling for JSON
                            loader = loader_class(
                                str(file_path),
                                jq_schema='.',
                                text_content=False
                            )
                        else:
                            loader = loader_class(str(file_path))
                        
                        file_docs = loader.load()
                        
                        # Add metadata
                        for doc in file_docs:
                            doc.metadata.update({
                                "category": category,
                                "source_file": str(file_path),
                                "loaded_at": str(datetime.now())
                            })
                        
                        documents.extend(file_docs)
                        logger.info(f"Loaded {len(file_docs)} documents from {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
        
        return documents
    
    def add_documents(self, documents: List[Document], category: str = "general"):
        """
        Add documents to a vector store
        
        Args:
            documents: List of documents to add
            category: Category for storage
        """
        
        if not documents:
            logger.warning("No documents to add")
            return
        
        # Split documents
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"Split {len(documents)} documents into {len(split_docs)} chunks")
        
        # Add to appropriate vector store
        if category not in self.vector_stores:
            self.vector_stores[category] = FAISS.from_documents(
                split_docs,
                self.embeddings
            )
        else:
            self.vector_stores[category].add_documents(split_docs)
        
        # Save vector store
        store_path = f"./vector_stores/{category}"
        self.vector_stores[category].save_local(store_path)
        logger.info(f"Added {len(split_docs)} chunks to {category} vector store")
    
    def create_retrieval_chain(self, category: str = "general", 
                              chain_type: str = "stuff",
                              return_source_documents: bool = True) -> RetrievalQA:
        """
        Create a retrieval chain for Q&A
        
        Args:
            category: Document category to search
            chain_type: Type of chain (stuff, map_reduce, refine, map_rerank)
            return_source_documents: Whether to return source documents
        
        Returns:
            RetrievalQA chain
        """
        
        if category not in self.vector_stores:
            raise ValueError(f"Category '{category}' not found in vector stores")
        
        # Create retriever
        retriever = self.vector_stores[category].as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Create prompt template
        prompt_template = """You are a real estate expert assistant for ConcordBroker.
        Use the following context to answer the question. If you don't know the answer, 
        say you don't know. Be specific and provide actionable insights when possible.
        
        Context: {context}
        
        Question: {question}
        
        Answer:"""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create chain
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type=chain_type,
            retriever=retriever,
            return_source_documents=return_source_documents,
            chain_type_kwargs={"prompt": prompt}
        )
        
        # Store chain
        self.chains[f"{category}_qa"] = chain
        
        return chain
    
    def create_conversational_chain(self, category: str = "general") -> ConversationalRetrievalChain:
        """
        Create a conversational retrieval chain with memory
        
        Args:
            category: Document category to search
        
        Returns:
            ConversationalRetrievalChain
        """
        
        if category not in self.vector_stores:
            raise ValueError(f"Category '{category}' not found in vector stores")
        
        # Create retriever
        retriever = self.vector_stores[category].as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Create memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # Create chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True
        )
        
        # Store chain
        self.chains[f"{category}_conversational"] = chain
        
        return chain
    
    def query(self, question: str, category: str = "general", 
             use_conversational: bool = False) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: Question to answer
            category: Document category to search
            use_conversational: Whether to use conversational chain
        
        Returns:
            Answer with sources
        """
        
        # Get or create appropriate chain
        chain_key = f"{category}_{'conversational' if use_conversational else 'qa'}"
        
        if chain_key not in self.chains:
            if use_conversational:
                chain = self.create_conversational_chain(category)
            else:
                chain = self.create_retrieval_chain(category)
        else:
            chain = self.chains[chain_key]
        
        # Run query
        try:
            if use_conversational:
                result = chain({"question": question})
            else:
                result = chain({"query": question})
            
            # Format response
            response = {
                "question": question,
                "answer": result.get("result") or result.get("answer"),
                "sources": []
            }
            
            # Extract sources
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    response["sources"].append({
                        "content": doc.page_content[:500],  # Truncate for response
                        "metadata": doc.metadata
                    })
            
            return response
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            return {
                "question": question,
                "answer": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    def similarity_search(self, query: str, category: str = "general", 
                         k: int = 5) -> List[Document]:
        """
        Perform similarity search
        
        Args:
            query: Search query
            category: Document category to search
            k: Number of results to return
        
        Returns:
            List of similar documents
        """
        
        if category not in self.vector_stores:
            raise ValueError(f"Category '{category}' not found in vector stores")
        
        return self.vector_stores[category].similarity_search(query, k=k)
    
    def load_property_data(self, data_path: str):
        """
        Load property-specific data into the RAG system
        
        Args:
            data_path: Path to property data directory
        """
        
        # Load different types of property data
        data_types = {
            "listings": "property_listings",
            "tax_records": "tax_records",
            "permits": "legal_documents",
            "market_analysis": "market_reports"
        }
        
        for data_type, category in data_types.items():
            type_path = Path(data_path) / data_type
            if type_path.exists():
                documents = self.load_documents(str(type_path), category)
                if documents:
                    self.add_documents(documents, category)
                    logger.info(f"Loaded {len(documents)} {data_type} documents")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAG system"""
        
        stats = {
            "vector_stores": {},
            "chains": list(self.chains.keys()),
            "total_documents": 0
        }
        
        for category, store in self.vector_stores.items():
            # This is approximate - actual count may vary
            stats["vector_stores"][category] = {
                "status": "active",
                "last_updated": datetime.now().isoformat()
            }
        
        return stats