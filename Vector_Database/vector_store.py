import logging
import os
import uuid
from typing import Dict, List, Optional, Union, Any, Tuple
import numpy as np
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from datetime import datetime
from pydantic import BaseModel, Field

# Set up logging
logging.basicConfig(
    filename='vector_database.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Document(BaseModel):
    """
    Represents a document to be stored in the vector database.
    """
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = None
    embedding: Optional[List[float]] = None

class VectorStore:
    """
    Main class for interacting with the Chroma vector database.
    Provides methods for storing, retrieving, and searching text documents.
    """
    
    def __init__(
        self, 
        collection_name: str = "narrative_data",
        persist_directory: Optional[str] = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database to
            embedding_model: Name of the sentence transformer model to use for embeddings
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Create persist directory if it doesn't exist
        if persist_directory and not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
        
        # Initialize the client
        self._initialize_client(persist_directory)
        
        # Initialize the embedding function
        self._initialize_embedding_function(embedding_model)
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        logging.info(f"Initialized vector store with collection: {collection_name}")
    
    def _initialize_client(self, persist_directory: Optional[str]) -> None:
        """
        Initialize the Chroma client.
        
        Args:
            persist_directory: Directory to persist the database to
        """
        if persist_directory:
            # Persistent client
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        else:
            # In-memory client
            self.client = chromadb.Client(
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
    
    def _initialize_embedding_function(self, model_name: str) -> None:
        """
        Initialize the embedding function.
        
        Args:
            model_name: Name of the model to use
        """
        # Use sentence transformers embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents to add
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Generate IDs for documents that don't have them
        for doc in documents:
            if not doc.id:
                doc.id = str(uuid.uuid4())
        
        try:
            # Extract document fields for Chroma
            ids = [doc.id for doc in documents]
            texts = [doc.text for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            
            # Add documents to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            
            logging.info(f"Added {len(documents)} documents to collection {self.collection_name}")
            return ids
        
        except Exception as e:
            logging.error(f"Error adding documents: {e}")
            raise
    
    def add_document(self, document: Document) -> str:
        """
        Add a single document to the vector store.
        
        Args:
            document: Document to add
            
        Returns:
            Document ID
        """
        return self.add_documents([document])[0]
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Document if found, None otherwise
        """
        try:
            result = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not result or not result["ids"]:
                return None
            
            return Document(
                id=result["ids"][0],
                text=result["documents"][0],
                metadata=result["metadatas"][0] if result["metadatas"] else {},
                embedding=result["embeddings"][0] if result["embeddings"] else None
            )
        
        except Exception as e:
            logging.error(f"Error getting document {document_id}: {e}")
            return None
    
    def get_documents(self, document_ids: List[str]) -> List[Document]:
        """
        Get multiple documents by IDs.
        
        Args:
            document_ids: List of document IDs to get
            
        Returns:
            List of documents found
        """
        if not document_ids:
            return []
        
        try:
            result = self.collection.get(
                ids=document_ids,
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not result or not result["ids"]:
                return []
            
            documents = []
            for i, doc_id in enumerate(result["ids"]):
                documents.append(Document(
                    id=doc_id,
                    text=result["documents"][i],
                    metadata=result["metadatas"][i] if result["metadatas"] else {},
                    embedding=result["embeddings"][i] if result["embeddings"] else None
                ))
            
            return documents
        
        except Exception as e:
            logging.error(f"Error getting documents {document_ids}: {e}")
            return []
    
    def search(
        self, 
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search the vector store for similar documents.
        
        Args:
            query: Query string
            n_results: Number of results to return
            filter_metadata: Metadata filter to apply
            
        Returns:
            List of similar documents
        """
        try:
            # Perform the query
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Convert results to documents
            documents = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    doc = Document(
                        id=doc_id,
                        text=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    )
                    documents.append(doc)
            
            logging.info(f"Found {len(documents)} documents for query: '{query}'")
            return documents
        
        except Exception as e:
            logging.error(f"Error searching for query '{query}': {e}")
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[document_id])
            logging.info(f"Deleted document {document_id}")
            return True
        
        except Exception as e:
            logging.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete multiple documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not document_ids:
            return True
        
        try:
            self.collection.delete(ids=document_ids)
            logging.info(f"Deleted {len(document_ids)} documents")
            return True
        
        except Exception as e:
            logging.error(f"Error deleting documents {document_ids}: {e}")
            return False
    
    def update_document(self, document: Document) -> bool:
        """
        Update a document in the vector store.
        
        Args:
            document: Document to update
            
        Returns:
            True if successful, False otherwise
        """
        if not document.id:
            logging.error("Cannot update document without ID")
            return False
        
        try:
            # Delete the existing document
            self.delete_document(document.id)
            
            # Add the updated document
            self.add_document(document)
            
            logging.info(f"Updated document {document.id}")
            return True
        
        except Exception as e:
            logging.error(f"Error updating document {document.id}: {e}")
            return False
    
    def search_by_metadata(
        self, 
        metadata_filter: Dict[str, Any],
        limit: int = 100
    ) -> List[Document]:
        """
        Search documents by metadata.
        
        Args:
            metadata_filter: Metadata filter to apply
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        try:
            results = self.collection.get(
                where=metadata_filter,
                limit=limit,
                include=["documents", "metadatas", "embeddings"]
            )
            
            if not results or not results["ids"]:
                return []
            
            documents = []
            for i, doc_id in enumerate(results["ids"]):
                documents.append(Document(
                    id=doc_id,
                    text=results["documents"][i],
                    metadata=results["metadatas"][i] if results["metadatas"] else {},
                    embedding=results["embeddings"][i] if results["embeddings"] else None
                ))
            
            logging.info(f"Found {len(documents)} documents with metadata filter: {metadata_filter}")
            return documents
        
        except Exception as e:
            logging.error(f"Error searching by metadata {metadata_filter}: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary of collection statistics
        """
        try:
            # Get all IDs
            result = self.collection.get(include=[])
            count = len(result["ids"]) if result and "ids" in result else 0
            
            # Get unique metadata values (limited sample for performance)
            sample_limit = min(1000, count)
            sample = self.collection.get(limit=sample_limit, include=["metadatas"])
            
            metadata_keys = set()
            metadata_counts = {}
            
            if sample and sample["metadatas"]:
                for metadata in sample["metadatas"]:
                    for key, value in metadata.items():
                        metadata_keys.add(key)
                        
                        if key not in metadata_counts:
                            metadata_counts[key] = {}
                        
                        value_str = str(value)
                        if value_str not in metadata_counts[key]:
                            metadata_counts[key][value_str] = 0
                        
                        metadata_counts[key][value_str] += 1
            
            # Format metadata stats
            metadata_stats = {}
            for key in metadata_keys:
                values = metadata_counts.get(key, {})
                top_values = sorted(values.items(), key=lambda x: x[1], reverse=True)[:10]
                metadata_stats[key] = {
                    "unique_values": len(values),
                    "top_values": dict(top_values)
                }
            
            return {
                "count": count,
                "collection_name": self.collection_name,
                "metadata_keys": list(metadata_keys),
                "metadata_stats": metadata_stats
            }
        
        except Exception as e:
            logging.error(f"Error getting collection stats: {e}")
            return {
                "error": str(e),
                "count": 0,
                "collection_name": self.collection_name
            }
    
    def reset_collection(self) -> bool:
        """
        Reset (delete all documents in) the collection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.reset()
            
            # Recreate the collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            
            logging.info(f"Reset collection {self.collection_name}")
            return True
        
        except Exception as e:
            logging.error(f"Error resetting collection: {e}")
            return False
    
    def __len__(self) -> int:
        """
        Get the number of documents in the collection.
        
        Returns:
            Number of documents
        """
        try:
            result = self.collection.get(include=[])
            return len(result["ids"]) if result and "ids" in result else 0
        
        except Exception:
            return 0