#!/usr/bin/env python3
"""
Simple test script to verify FREE HuggingFace embeddings work correctly
Run this to test your embedding setup: python test_embeddings.py
"""

def test_embeddings():
    """Test the exact embedding syntax used in the application"""
    
    print("🧪 Testing FREE HuggingFace Embeddings")
    print("=" * 50)
    
    try:
        # Import the exact same way as in the application
        from langchain.embeddings import HuggingFaceEmbeddings
        print("✅ Import successful")
        
        # Create embeddings using the exact syntax from vector_store.py
        print("📦 Creating embeddings with: all-MiniLM-L6-v2")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        print("✅ Embeddings created successfully")
        
        # Test with sample text
        print("🔍 Testing embedding generation...")
        test_texts = [
            "Hello world",
            "Machine learning is fascinating",
            "Python is a great programming language"
        ]
        
        # Test document embeddings
        doc_embeddings = embeddings.embed_documents(test_texts)
        print(f"✅ Document embeddings: {len(doc_embeddings)} docs, {len(doc_embeddings[0])} dimensions")
        
        # Test query embedding
        query_embedding = embeddings.embed_query("What is programming?")
        print(f"✅ Query embedding: {len(query_embedding)} dimensions")
        
        # Test vector store compatibility
        print("🗄️ Testing vector store compatibility...")
        from langchain.vectorstores import Chroma
        
        vector_store = Chroma(
            persist_directory="test_vector_db",
            embedding_function=embeddings
        )
        print("✅ Vector store created successfully")
        
        # Success summary
        print("\n🎉 SUCCESS! Everything works perfectly!")
        print("=" * 50)
        print("💰 Cost: $0 (FREE)")
        print("🔑 API Key: Not needed")
        print("🏠 Processing: Local")
        print("📊 Dimensions: 384")
        print("⚡ Speed: Fast")
        print("🎯 Quality: Good")
        print("🔒 Privacy: Full")
        
        # Clean up test files
        import os
        import shutil
        if os.path.exists("test_vector_db"):
            shutil.rmtree("test_vector_db")
            print("🧹 Cleaned up test files")
            
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Try: pip install sentence-transformers transformers")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def compare_with_openai():
    """Show comparison with OpenAI (what you DON'T need anymore)"""
    
    print("\n📊 Comparison with OpenAI")
    print("=" * 50)
    
    print("🤗 HuggingFace (Current - RECOMMENDED):")
    print("   Syntax: embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')")
    print("   Cost: $0 (FREE)")
    print("   API Key: Not needed")
    print("   Privacy: Full (local)")
    print("   Setup: pip install + run")
    print("   Quality: Good")
    
    print("\n🔑 OpenAI (What you DON'T need):")
    print("   Syntax: embeddings = OpenAIEmbeddings(openai_api_key='sk-...')")
    print("   Cost: $0.0001 per 1K tokens")
    print("   API Key: Required")
    print("   Privacy: Data sent to OpenAI")
    print("   Setup: API key + billing")
    print("   Quality: Excellent")
    
    print("\n🎯 Why HuggingFace is better for most users:")
    print("   ✅ Zero cost forever")
    print("   ✅ No API key management")
    print("   ✅ Works offline")
    print("   ✅ Complete privacy")
    print("   ✅ Good enough quality")
    print("   ✅ No rate limits")

def main():
    """Main test function"""
    print("🎯 FREE HuggingFace Embeddings Test")
    print("🔧 Testing the exact setup from your RAG application")
    print("📁 File: app/models/vector_store.py")
    print("")
    
    success = test_embeddings()
    
    compare_with_openai()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Your embedding setup is working perfectly!")
        print("🚀 Ready to run: python app/main.py")
    else:
        print("❌ Please fix the errors above before proceeding")
        
    print("\n💡 Next steps:")
    print("1. Make sure this test passes")
    print("2. Fill in your .env file with Groq API key")
    print("3. Add AWS credentials")
    print("4. Run: python app/main.py")

if __name__ == "__main__":
    main()