#!/usr/bin/env python3
"""
Upgrade LangChain and related packages to latest versions
Includes compatibility checks and migration helpers
"""

import subprocess
import sys
import json
from typing import List, Dict, Tuple

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """Run command and return success status and output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def get_current_versions() -> Dict[str, str]:
    """Get current versions of LangChain packages"""
    packages = [
        "langchain",
        "langchain-core", 
        "langchain-community",
        "langchain-openai",
        "langgraph",
        "langsmith"
    ]
    
    versions = {}
    for package in packages:
        success, output = run_command(["pip", "show", package])
        if success and "Version:" in output:
            for line in output.split('\n'):
                if line.startswith("Version:"):
                    versions[package] = line.split(":")[1].strip()
                    break
        else:
            versions[package] = "Not installed"
    
    return versions

def upgrade_packages():
    """Upgrade LangChain packages to latest versions"""
    
    print("=" * 60)
    print("LANGCHAIN UPGRADE UTILITY")
    print("=" * 60)
    
    # Get current versions
    print("\nCurrent versions:")
    current = get_current_versions()
    for pkg, ver in current.items():
        print(f"  {pkg}: {ver}")
    
    # Packages to upgrade
    packages = [
        # Core packages
        "langchain>=0.3.27",
        "langchain-core>=0.3.75",
        "langchain-community>=0.3.0",
        
        # Provider packages
        "langchain-openai>=0.2.0",
        "langchain-anthropic>=0.3.0",
        
        # LangGraph and LangSmith
        "langgraph>=0.6.7",
        "langsmith>=0.2.0",
        
        # Additional optimizations
        "langchain-experimental>=0.3.0",
        "langchainhub>=0.2.0",
        
        # Performance dependencies
        "tiktoken>=0.8.0",
        "faiss-cpu>=1.8.0",
        "numpy<2.0.0",  # Compatibility constraint
    ]
    
    print("\n" + "=" * 60)
    print("UPGRADING PACKAGES")
    print("=" * 60)
    
    for package in packages:
        pkg_name = package.split(">=")[0]
        print(f"\nUpgrading {pkg_name}...")
        
        success, output = run_command([sys.executable, "-m", "pip", "install", "--upgrade", package])
        
        if success:
            print(f"[OK] {pkg_name} upgraded successfully")
        else:
            print(f"[WARNING] {pkg_name} upgrade failed: {output[:200]}")
    
    # Get new versions
    print("\n" + "=" * 60)
    print("NEW VERSIONS")
    print("=" * 60)
    new = get_current_versions()
    for pkg, ver in new.items():
        old_ver = current.get(pkg, "Not installed")
        if ver != old_ver:
            print(f"  {pkg}: {old_ver} -> {ver} [UPGRADED]")
        else:
            print(f"  {pkg}: {ver} (unchanged)")
    
    # Run compatibility check
    print("\n" + "=" * 60)
    print("COMPATIBILITY CHECK")
    print("=" * 60)
    
    try:
        # Test imports
        import langchain
        import langchain_core
        import langgraph
        from langchain_openai import ChatOpenAI
        from langgraph.graph import StateGraph
        
        print("[OK] All core imports successful")
        print(f"[OK] LangChain version: {langchain.__version__}")
        print(f"[OK] LangGraph version: {langgraph.__version__}")
        
        # Test basic functionality
        print("\nTesting basic functionality...")
        
        # Test LLM initialization
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
            print("[OK] LLM initialization successful")
        except Exception as e:
            print(f"[WARNING] LLM initialization failed (API key may be needed): {e}")
        
        # Test StateGraph
        graph = StateGraph(dict)
        print("[OK] StateGraph creation successful")
        
        print("\n[SUCCESS] Upgrade completed successfully!")
        
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print("\nPlease check your installation and try again.")
        return False
    
    # Provide migration tips
    print("\n" + "=" * 60)
    print("MIGRATION TIPS")
    print("=" * 60)
    print("""
1. **Breaking Changes to Check**:
   - Chain.run() is deprecated, use Chain.invoke()
   - LLMChain is deprecated, use RunnableSequence
   - Memory classes moved to langchain_community
   
2. **Performance Optimizations Available**:
   - Enable streaming: llm.stream() for real-time responses
   - Use batch operations: llm.batch() for multiple inputs
   - Implement caching: from langchain.cache import InMemoryCache
   
3. **New Features to Explore**:
   - Parallel tool execution in agents
   - Enhanced error handling with fallbacks
   - Improved token counting and management
   - Better async support throughout
   
4. **LangGraph Improvements**:
   - Use conditional edges for complex routing
   - Implement checkpointers for state persistence
   - Leverage subgraphs for modular workflows
   
5. **Testing Your Upgrade**:
   - Run your existing agents to ensure compatibility
   - Check API response times (should be faster)
   - Monitor memory usage (should be lower)
""")
    
    return True

def create_optimized_config():
    """Create optimized configuration for upgraded LangChain"""
    
    config = {
        "llm": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "streaming": True,
            "max_tokens": 4000,
            "request_timeout": 30,
            "max_retries": 3,
            "cache": True
        },
        "agents": {
            "max_iterations": 10,
            "early_stopping_method": "force",
            "handle_parsing_errors": True,
            "verbose": False,
            "return_intermediate_steps": False
        },
        "memory": {
            "type": "conversation_buffer_window",
            "k": 10,
            "return_messages": True
        },
        "embeddings": {
            "model": "text-embedding-3-small",
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "vectorstore": {
            "type": "faiss",
            "similarity_metric": "cosine",
            "k": 5
        },
        "cache": {
            "enabled": True,
            "type": "redis",
            "ttl": 3600
        },
        "tracing": {
            "langsmith": True,
            "verbose": False
        }
    }
    
    # Save configuration
    with open("langchain_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n[OK] Created optimized configuration in langchain_config.json")
    
    return config

if __name__ == "__main__":
    print("Starting LangChain upgrade process...")
    
    # Perform upgrade
    success = upgrade_packages()
    
    if success:
        # Create optimized config
        create_optimized_config()
        
        print("\n" + "=" * 60)
        print("UPGRADE COMPLETE")
        print("=" * 60)
        print("""
Next steps:
1. Restart your API server to use new versions
2. Test your existing agents for compatibility
3. Implement new performance features
4. Monitor improvements in speed and reliability
""")
    else:
        print("\n[ERROR] Upgrade failed. Please check the errors above.")
        sys.exit(1)