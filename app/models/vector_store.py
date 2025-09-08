# app/models/vector_store.py
import chromadb
from langchain_community.vectorstores import Chroma
import time
import os
from config import Config
from logger_config import get_logger, log_success, log_error, log_warning, log_info

class VectorStore:
    """Enhanced Vector Store with logging and error handling - Keras 3 Compatible"""
    
    def __init__(self, path):
        self.logger = get_logger("vector_store")
        self.path = path
        self.embeddings = None
        self.vector_store = None
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize the vector store with proper error handling"""
        try:
            log_info(self.logger, f"Initializing vector store at path: {self.path}")
            start_time = time.time()
            
            # Ensure directory exists
            os.makedirs(self.path, exist_ok=True)
            
            # Try multiple embedding approaches to handle Keras compatibility issues
            self.embeddings = self._initialize_embeddings()
            
            # Initialize vector store
            self.vector_store = Chroma(
                persist_directory=self.path,
                embedding_function=self.embeddings,
                collection_name="document_collection"
            )
            
            init_time = time.time() - start_time
            log_success(self.logger, f"Vector store initialized successfully in {init_time:.2f}s")
            
            # Log collection info
            try:
                collection_count = self.vector_store._collection.count()
                log_info(self.logger, f"Current collection size: {collection_count} documents")
            except Exception as count_error:
                log_warning(self.logger, f"Could not get collection count: {count_error}")
            
        except Exception as e:
            log_error(self.logger, f"Failed to initialize vector store: {str(e)}")
            raise
    
    def _initialize_embeddings(self):
        """Initialize embeddings with fallback options for Keras compatibility"""
        
        # Option 1: Try HuggingFace embeddings with tf-keras fix
        try:
            log_info(self.logger, "Attempting HuggingFace embeddings (Option 1)")
            
            # Try to import and fix tf-keras issue
            try:
                import tensorflow as tf
                # Set memory growth to avoid GPU issues
                physical_devices = tf.config.list_physical_devices('GPU')
                if physical_devices:
                    tf.config.experimental.set_memory_growth(physical_devices[0], True)
            except:
                pass  # Continue without GPU optimization
            
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={
                    'device': 'cpu',  # Force CPU to avoid GPU/CUDA issues
                    'trust_remote_code': False
                },
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 1  # Smaller batch size for stability
                }
            )
            
            # Test the embeddings
            test_text = "test embedding"
            test_result = embeddings.embed_query(test_text)
            
            if test_result and len(test_result) > 0:
                log_success(self.logger, "HuggingFace embeddings initialized successfully")
                return embeddings
            else:
                raise Exception("Embedding test failed")
                
        except Exception as e1:
            log_warning(self.logger, f"HuggingFace embeddings failed: {str(e1)}")
            
            # Option 2: Try alternative embeddings from langchain-huggingface
            try:
                log_info(self.logger, "Attempting langchain-huggingface embeddings (Option 2)")
                
                # Try importing from the new package
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings as HFEmbeddings
                    
                    embeddings = HFEmbeddings(
                        model_name="all-MiniLM-L6-v2",
                        model_kwargs={'device': 'cpu'},
                        encode_kwargs={'normalize_embeddings': True}
                    )
                    
                    # Test the embeddings
                    test_result = embeddings.embed_query("test embedding")
                    if test_result and len(test_result) > 0:
                        log_success(self.logger, "langchain-huggingface embeddings initialized successfully")
                        return embeddings
                    else:
                        raise Exception("Embedding test failed")
                        
                except ImportError:
                    log_warning(self.logger, "langchain-huggingface package not installed")
                    raise Exception("langchain-huggingface not available")
                    
            except Exception as e2:
                log_warning(self.logger, f"Alternative embeddings failed: {str(e2)}")
                
                # Option 3: Use OpenAI embeddings if available
                try:
                    log_info(self.logger, "Attempting OpenAI embeddings (Option 3)")
                    
                    if hasattr(Config, 'OPENAI_API_KEY') and Config.OPENAI_API_KEY:
                        from langchain_community.embeddings import OpenAIEmbeddings
                        
                        embeddings = OpenAIEmbeddings(
                            openai_api_key=Config.OPENAI_API_KEY,
                            model="text-embedding-ada-002"
                        )
                        
                        # Test the embeddings
                        test_result = embeddings.embed_query("test embedding")
                        if test_result and len(test_result) > 0:
                            log_success(self.logger, "OpenAI embeddings initialized successfully")
                            return embeddings
                        else:
                            raise Exception("OpenAI embedding test failed")
                    else:
                        raise Exception("OpenAI API key not available")
                        
                except Exception as e3:
                    log_warning(self.logger, f"OpenAI embeddings failed: {str(e3)}")
                    
                    # Option 4: Use a simple embedding fallback
                    log_warning(self.logger, "Using fallback embedding method")
                    return self._create_fallback_embeddings()
    
    def _create_fallback_embeddings(self):
        """Create a simple fallback embedding function"""
        log_info(self.logger, "Creating simple fallback embeddings")
        
        class SimpleFallbackEmbeddings:
            def embed_documents(self, texts):
                # Simple hash-based embeddings as last resort
                import hashlib
                embeddings = []
                for text in texts:
                    # Create a simple hash-based embedding
                    hash_obj = hashlib.md5(text.encode())
                    hex_dig = hash_obj.hexdigest()
                    # Convert to numerical embedding (384 dimensions to match all-MiniLM-L6-v2)
                    embedding = [int(hex_dig[i:i+2], 16) / 255.0 for i in range(0, min(len(hex_dig), 32), 2)]
                    # Pad to 384 dimensions
                    while len(embedding) < 384:
                        embedding.extend(embedding[:min(len(embedding), 384 - len(embedding))])
                    embeddings.append(embedding[:384])
                return embeddings
            
            def embed_query(self, text):
                return self.embed_documents([text])[0]
        
        log_warning(self.logger, "Using simple hash-based embeddings - limited functionality")
        return SimpleFallbackEmbeddings()
    
    def add_documents(self, documents):
        """Add documents to the vector store with logging"""
        try:
            if not documents:
                log_warning(self.logger, "No documents provided to add")
                return False
            
            log_info(self.logger, f"Adding {len(documents)} documents to vector store")
            start_time = time.time()
            
            # Add documents to vector store
            self.vector_store.add_documents(documents)
            
            # Persist the changes (for older versions of Chroma)
            try:
                self.vector_store.persist()
                log_info(self.logger, "Changes persisted to disk")
            except AttributeError:
                # Newer versions of Chroma auto-persist
                log_info(self.logger, "Auto-persistence enabled")
            
            add_time = time.time() - start_time
            log_success(self.logger, f"Successfully added {len(documents)} documents in {add_time:.2f}s")
            
            # Log updated collection size
            try:
                collection_count = self.vector_store._collection.count()
                log_info(self.logger, f"Updated collection size: {collection_count} documents")
            except Exception as count_error:
                log_warning(self.logger, f"Could not get updated collection count: {count_error}")
            
            return True
            
        except Exception as e:
            log_error(self.logger, f"Failed to add documents to vector store: {str(e)}")
            return False
    
    def similarity_search(self, query, k=4):
        """Perform similarity search with logging"""
        try:
            if not query or not query.strip():
                log_warning(self.logger, "Empty query provided")
                return []
                
            log_info(self.logger, f"Performing similarity search for query: '{query[:50]}...'")
            start_time = time.time()
            
            # Perform search
            results = self.vector_store.similarity_search(query, k=k)
            
            search_time = time.time() - start_time
            log_success(self.logger, f"Found {len(results)} results in {search_time:.2f}s")
            
            # Log result details (without sensitive content)
            for i, result in enumerate(results):
                if hasattr(result, 'page_content'):
                    content_preview = result.page_content[:100] + "..." if len(result.page_content) > 100 else result.page_content
                    self.logger.debug(f"[RESULT] Result {i+1}: {content_preview}")
                else:
                    self.logger.debug(f"[RESULT] Result {i+1}: {type(result)}")
            
            return results
            
        except Exception as e:
            log_error(self.logger, f"Similarity search failed: {str(e)}")
            return []
    
    def similarity_search_with_score(self, query, k=4):
        """Perform similarity search with scores"""
        try:
            if not query or not query.strip():
                log_warning(self.logger, "Empty query provided")
                return []
                
            log_info(self.logger, f"Performing similarity search with scores for: '{query[:50]}...'")
            start_time = time.time()
            
            # Perform search with scores
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            search_time = time.time() - start_time
            log_success(self.logger, f"Found {len(results)} scored results in {search_time:.2f}s")
            
            # Log scores
            for i, (doc, score) in enumerate(results):
                self.logger.debug(f"[SCORE] Result {i+1} score: {score:.4f}")
            
            return results
            
        except Exception as e:
            log_error(self.logger, f"Similarity search with scores failed: {str(e)}")
            return []
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            log_warning(self.logger, "Deleting entire vector store collection")
            
            # Try different methods depending on Chroma version
            try:
                self.vector_store.delete_collection()
            except AttributeError:
                # Alternative method for newer versions
                if hasattr(self.vector_store, '_collection'):
                    self.vector_store._collection.delete()
                else:
                    raise Exception("Unable to delete collection - method not available")
            
            log_success(self.logger, "Vector store collection deleted successfully")
            return True
            
        except Exception as e:
            log_error(self.logger, f"Failed to delete collection: {str(e)}")
            return False
    
    def get_collection_info(self):
        """Get information about the current collection"""
        try:
            collection_count = 0
            try:
                collection_count = self.vector_store._collection.count()
            except Exception as count_error:
                self.logger.debug(f"Could not get count: {count_error}")
            
            embedding_info = "Unknown"
            if hasattr(self.embeddings, 'model_name'):
                embedding_info = f"HuggingFace: {self.embeddings.model_name}"
            elif hasattr(self.embeddings, '__class__'):
                embedding_info = f"{self.embeddings.__class__.__name__}"
            
            return {
                "document_count": collection_count,
                "path": self.path,
                "embedding_model": embedding_info,
                "embedding_type": "Free Local Model",
                "embedding_dimensions": 384,  # Standard dimension
                "collection_name": "document_collection",
                "status": "active",
                "cost": "Free",
                "device": "CPU",
                "vector_store_type": "Chroma"
            }
        except Exception as e:
            log_error(self.logger, f"Failed to get collection info: {str(e)}")
            return {
                "document_count": 0,
                "path": self.path,
                "embedding_model": "Error",
                "embedding_type": "Free Local Model",
                "embedding_dimensions": 384,
                "collection_name": "document_collection",
                "status": "error",
                "cost": "Free",
                "device": "CPU",
                "vector_store_type": "Chroma",
                "error": str(e)
            }
    
    def health_check(self):
        """Perform a health check on the vector store"""
        try:
            log_info(self.logger, "Performing vector store health check")
            
            # Check if vector store is initialized
            if self.vector_store is None:
                log_error(self.logger, "Vector store not initialized")
                return False
            
            # Check if embeddings are working
            if self.embeddings is None:
                log_error(self.logger, "Embeddings not initialized") 
                return False
            
            # Try a simple embedding operation
            test_text = "health check test"
            test_embedding = self.embeddings.embed_query(test_text)
            
            if not test_embedding or len(test_embedding) == 0:
                log_error(self.logger, "Embedding generation failed")
                return False
            
            # Try a simple search operation (will work even with empty collection)
            test_results = self.similarity_search("test", k=1)
            
            log_success(self.logger, "Vector store health check passed")
            return True
            
        except Exception as e:
            log_error(self.logger, f"Vector store health check failed: {str(e)}")
            return False
    
    def clear_collection(self):
        """Clear all documents from the collection without deleting it"""
        try:
            log_warning(self.logger, "Clearing all documents from collection")
            
            # Get all document IDs and delete them
            if hasattr(self.vector_store, '_collection'):
                collection = self.vector_store._collection
                all_ids = collection.get()['ids']
                
                if all_ids:
                    collection.delete(ids=all_ids)
                    log_success(self.logger, f"Cleared {len(all_ids)} documents from collection")
                else:
                    log_info(self.logger, "Collection was already empty")
            else:
                log_warning(self.logger, "Cannot clear collection - method not available")
                return False
            
            return True
            
        except Exception as e:
            log_error(self.logger, f"Failed to clear collection: {str(e)}")
            return False
    
    def add_texts(self, texts, metadatas=None):
        """Add raw texts to the vector store"""
        try:
            if not texts:
                log_warning(self.logger, "No texts provided")
                return False
            
            log_info(self.logger, f"Adding {len(texts)} texts to vector store")
            start_time = time.time()
            
            # Add texts to vector store
            self.vector_store.add_texts(texts, metadatas=metadatas)
            
            add_time = time.time() - start_time
            log_success(self.logger, f"Successfully added {len(texts)} texts in {add_time:.2f}s")
            
            return True
            
        except Exception as e:
            log_error(self.logger, f"Failed to add texts: {str(e)}")
            return False