# app/services/llm_service.py
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
import time
from config import Config
from logger_config import get_logger, log_success, log_error, log_warning, log_info

class LLMService:
    """Enhanced LLM Service with strict document-only responses"""
    
    def __init__(self, vector_store):
        self.logger = get_logger("llm_service")
        self.vector_store = vector_store
        self.llm = None
        self.memory = None
        self.chain = None
        self.conversation_history = []
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM with proper error handling"""
        try:
            log_info(self.logger, "Initializing LLM service")
            start_time = time.time()
            
            # Initialize the LLM with strict parameters
            self.llm = ChatGroq(
                temperature=0.1,  # Lower temperature for more factual responses
                model_name="llama-3.3-70b-versatile",
                groq_api_key=Config.GROQ_API_KEY,
                max_tokens=1024  # Reduced for more focused responses
            )
            
            # Initialize memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )
            
            # Create custom prompt template for document-only responses
            custom_prompt = PromptTemplate(
                input_variables=["context", "question", "chat_history"],
                template="""You are an AI assistant that answers questions STRICTLY based on the provided document content.

IMPORTANT RULES:
1. Answer ONLY based on the context provided below
2. If the information is not in the context, say "This information is not available in the uploaded documents"
3. Always respond in English only
4. Do not make assumptions or add information not in the documents
5. Be direct and factual

Context from uploaded documents:
{context}

Previous conversation:
{chat_history}

Question: {question}

Answer based strictly on the document context above (English only):"""
            )
            
            # Initialize the conversation chain with custom prompt
            self.chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vector_store.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 6}  # Get more documents for better context
                ),
                memory=self.memory,
                return_source_documents=True,
                combine_docs_chain_kwargs={"prompt": custom_prompt},
                verbose=False
            )
            
            init_time = time.time() - start_time
            log_success(self.logger, f"LLM service initialized successfully in {init_time:.2f}s")
            
        except Exception as e:
            log_error(self.logger, f"Failed to initialize LLM service: {str(e)}")
            raise
    
    def get_response(self, query, include_sources=True):
        """
        Get response from the LLM with context from vector store ONLY
        
        Args:
            query (str): User query
            include_sources (bool): Whether to include source documents
        
        Returns:
            dict: Response with answer and optional sources
        """
        try:
            log_info(self.logger, f"Processing query: '{query[:100]}...'")
            start_time = time.time()
            
            # First check if we have any documents
            collection_info = self.vector_store.get_collection_info()
            if collection_info.get("document_count", 0) == 0:
                return {
                    "answer": "No documents have been uploaded yet. Please upload documents first to get answers about their content.",
                    "response_time": 0,
                    "query": query,
                    "sources": []
                }
            
            # Get relevant documents first to validate we have content
            relevant_docs = self.vector_store.similarity_search(query, k=6)
            
            if not relevant_docs:
                return {
                    "answer": "This information is not available in the uploaded documents. The question may not be related to the uploaded content.",
                    "response_time": 0,
                    "query": query,
                    "sources": []
                }
            
            # Create strict context-only prompt
            context = "\n\n".join([
                f"Document {i+1}:\n{doc.page_content}" 
                for i, doc in enumerate(relevant_docs)
            ])
            
            # Enhanced prompt to ensure document-only responses
            strict_prompt = f"""Based ONLY on the following document content, answer the question in English.

STRICT RULES:
- Use ONLY information from the documents below
- If the answer is not in the documents, say "This information is not available in the uploaded documents"
- Respond in English only
- Be factual and direct
- Do not add external knowledge

DOCUMENT CONTENT:
{context}

QUESTION: {query}

ANSWER (based strictly on the documents above, in English):"""
            
            # Get response using direct LLM call for better control
            messages = [HumanMessage(content=strict_prompt)]
            response = self.llm(messages)
            
            response_time = time.time() - start_time
            answer = response.content.strip()
            
            # Validate that the response seems document-based
            if self._is_generic_response(answer):
                answer = "This information is not available in the uploaded documents. Please ensure your question relates to the uploaded content."
            
            # Log response details
            log_success(self.logger, f"Generated response in {response_time:.2f}s")
            log_info(self.logger, f"Response length: {len(answer)} characters")
            log_info(self.logger, f"Sources used: {len(relevant_docs)} documents")
            
            # Store conversation in history
            self._add_to_history(query, answer)
            
            # Prepare response
            result = {
                "answer": answer,
                "response_time": response_time,
                "query": query
            }
            
            if include_sources and relevant_docs:
                result["sources"] = self._format_sources(relevant_docs)
            else:
                result["sources"] = []
            
            return result
            
        except Exception as e:
            log_error(self.logger, f"Error getting LLM response: {str(e)}")
            return {
                "answer": "I encountered an error processing your request. Please try again.",
                "error": str(e),
                "response_time": 0,
                "query": query,
                "sources": []
            }
    
    def _is_generic_response(self, response):
        """Check if response seems too generic (not document-based)"""
        generic_phrases = [
            "i don't know",
            "i'm not sure",
            "i apologize",
            "i can't help",
            "i don't have access",
            "based on my knowledge",
            "in general",
            "typically",
            "usually"
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in generic_phrases)
    
    def get_document_summary(self):
        """Get a summary of uploaded documents"""
        try:
            collection_info = self.vector_store.get_collection_info()
            
            if collection_info.get("document_count", 0) == 0:
                return {
                    "summary": "No documents uploaded",
                    "document_count": 0
                }
            
            # Get a sample of documents to create summary
            sample_docs = self.vector_store.similarity_search("summary overview content", k=3)
            
            if not sample_docs:
                return {
                    "summary": "Documents uploaded but content not accessible",
                    "document_count": collection_info.get("document_count", 0)
                }
            
            # Create summary prompt
            context = "\n\n".join([doc.page_content[:300] for doc in sample_docs])
            
            prompt = f"""Based on the following document excerpts, provide a brief summary of what these documents contain. Respond in English only.

Document excerpts:
{context}

Brief summary of document content:"""
            
            messages = [HumanMessage(content=prompt)]
            response = self.llm(messages)
            
            return {
                "summary": response.content.strip(),
                "document_count": collection_info.get("document_count", 0)
            }
            
        except Exception as e:
            log_error(self.logger, f"Error getting document summary: {str(e)}")
            return {
                "summary": "Error generating summary",
                "document_count": 0
            }
    
    def _format_sources(self, source_documents):
        """Format source documents for response"""
        sources = []
        for i, doc in enumerate(source_documents):
            # Get first 200 characters as preview
            content_preview = doc.page_content[:200]
            if len(doc.page_content) > 200:
                content_preview += "..."
            
            source = {
                "id": i + 1,
                "content": content_preview,
                "metadata": doc.metadata,
                "full_length": len(doc.page_content)
            }
            sources.append(source)
        return sources
    
    def _add_to_history(self, query, answer):
        """Add conversation to history"""
        conversation = {
            "timestamp": time.time(),
            "query": query,
            "answer": answer
        }
        self.conversation_history.append(conversation)
        
        # Keep only last 20 conversations
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_conversation_history(self, limit=10):
        """Get recent conversation history"""
        return self.conversation_history[-limit:]
    
    def clear_memory(self):
        """Clear conversation memory"""
        try:
            self.memory.clear()
            self.conversation_history = []
            log_info(self.logger, "Conversation memory cleared")
            return True
        except Exception as e:
            log_error(self.logger, f"Failed to clear memory: {str(e)}")
            return False
    
    def validate_document_response(self, query, answer):
        """Validate that response is based on documents"""
        # Check if we have documents
        collection_info = self.vector_store.get_collection_info()
        if collection_info.get("document_count", 0) == 0:
            return False
        
        # Check if answer indicates no information found
        no_info_phrases = [
            "not available in the uploaded documents",
            "information is not in the documents",
            "not found in the uploaded content"
        ]
        
        return not any(phrase in answer.lower() for phrase in no_info_phrases)
    
    def get_model_info(self):
        """Get information about the LLM model"""
        collection_info = self.vector_store.get_collection_info()
        
        return {
            "model_name": "llama-3.3-70b-versatile",
            "provider": "Groq",
            "temperature": 0.1,
            "max_tokens": 1024,
            "memory_type": "ConversationBufferMemory",
            "retriever_k": 6,
            "document_count": collection_info.get("document_count", 0),
            "response_language": "English only",
            "response_mode": "Document content only",
            "strict_mode": True
        }
    
    def health_check(self):
        """Perform a health check on the LLM service"""
        try:
            # Test with a simple query
            if not self.llm:
                return False
                
            test_messages = [HumanMessage(content="Respond with 'OK' in English")]
            response = self.llm(test_messages)
            
            if response and response.content:
                log_success(self.logger, "LLM service health check passed")
                return True
            else:
                log_error(self.logger, "LLM service health check failed: No response")
                return False
                
        except Exception as e:
            log_error(self.logger, f"LLM service health check failed: {str(e)}")
            return False
    
    def get_available_documents_info(self):
        """Get information about available documents for queries"""
        try:
            collection_info = self.vector_store.get_collection_info()
            
            if collection_info.get("document_count", 0) == 0:
                return {
                    "has_documents": False,
                    "message": "No documents uploaded. Please upload documents to enable Q&A functionality.",
                    "document_count": 0
                }
            
            # Get sample content to show what's available
            sample_docs = self.vector_store.similarity_search("content overview", k=2)
            
            return {
                "has_documents": True,
                "message": "Documents are available for questions",
                "document_count": collection_info.get("document_count", 0),
                "sample_content": [doc.page_content[:100] + "..." for doc in sample_docs[:2]]
            }
            
        except Exception as e:
            log_error(self.logger, f"Error getting document info: {str(e)}")
            return {
                "has_documents": False,
                "message": "Error accessing documents",
                "document_count": 0
            }