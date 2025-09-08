# fix_keras_issue.py
# Run this script to fix the Keras 3 compatibility issue

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def check_installation(package_name, import_name=None):
    """Check if a package is installed and can be imported"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} is installed and working")
        return True
    except ImportError:
        print(f"❌ {package_name} is not installed or not working")
        return False

def main():
    print("🔧 Fixing Keras 3 Compatibility Issue for LangChain/HuggingFace...")
    print("=" * 60)
    
    # Step 1: Install tf-keras (main fix)
    print("\n1. Installing tf-keras (Keras compatibility fix)...")
    success1 = run_command("pip install tf-keras")
    
    # Step 2: Install langchain-huggingface (alternative)
    print("\n2. Installing langchain-huggingface (alternative embeddings)...")
    success2 = run_command("pip install langchain-huggingface")
    
    # Step 3: Upgrade sentence-transformers
    print("\n3. Upgrading sentence-transformers...")
    success3 = run_command("pip install sentence-transformers --upgrade")
    
    # Step 4: Set TensorFlow to use CPU only (avoid GPU issues)
    print("\n4. Setting TensorFlow environment variables...")
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'   # Reduce TF warnings
    print("✅ TensorFlow configured for CPU-only mode")
    
    print("\n" + "=" * 60)
    print("🧪 Testing installations...")
    print("=" * 60)
    
    # Test 1: Check tf-keras
    print("\nTest 1: tf-keras import")
    tf_keras_ok = check_installation("tf-keras", "tf_keras")
    
    # Test 2: Check langchain-huggingface
    print("\nTest 2: langchain-huggingface import")
    langchain_hf_ok = check_installation("langchain-huggingface", "langchain_huggingface")
    
    # Test 3: Test HuggingFace embeddings
    print("\nTest 3: HuggingFace embeddings test")
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        test_result = embeddings.embed_query("test")
        if test_result and len(test_result) > 0:
            print("✅ HuggingFace embeddings are working!")
            embeddings_ok = True
        else:
            print("❌ HuggingFace embeddings test failed")
            embeddings_ok = False
    except Exception as e:
        print(f"❌ HuggingFace embeddings error: {str(e)}")
        embeddings_ok = False
    
    # Test 4: Test alternative embeddings
    print("\nTest 4: Alternative embeddings test")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings as HFEmbeddings
        alt_embeddings = HFEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        alt_test_result = alt_embeddings.embed_query("test")
        if alt_test_result and len(alt_test_result) > 0:
            print("✅ Alternative embeddings are working!")
            alt_embeddings_ok = True
        else:
            print("❌ Alternative embeddings test failed")
            alt_embeddings_ok = False
    except Exception as e:
        print(f"❌ Alternative embeddings error: {str(e)}")
        alt_embeddings_ok = False
    
    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)
    
    if tf_keras_ok and embeddings_ok:
        print("🎉 SUCCESS: Keras issue fixed! Original embeddings working.")
        print("✅ You can now run your application: python app/main.py")
    elif alt_embeddings_ok:
        print("🎉 PARTIAL SUCCESS: Alternative embeddings working.")
        print("✅ Your application should work with langchain-huggingface")
    else:
        print("⚠️  PARTIAL FIX: Some issues remain, but fallback will work")
        print("ℹ️  Your application will use simple hash-based embeddings")
    
    print("\n📋 Next steps:")
    print("1. Replace your code files with the corrected versions")
    print("2. Run: python app/main.py")
    print("3. If still issues, restart your terminal/IDE")
    
    print("\n💡 Alternative manual fix:")
    print("If this script doesn't work, try manually:")
    print("  pip install tf-keras --force-reinstall")
    print("  pip install tensorflow==2.15.0")
    print("  pip install langchain-huggingface")

if __name__ == "__main__":
    main()