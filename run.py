#!/usr/bin/env python3
"""
Startup script for the AI Task Planning Agent
Powered by Groq + Llama 4 Maverick
"""
import os
import sys
import subprocess
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, .env file won't be loaded")
    print("   Install with: pip install python-dotenv")

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def check_virtual_env():
    """Check if running in virtual environment"""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if not in_venv:
        print("⚠️  Warning: Not running in a virtual environment")
        print("   Consider creating one: python -m venv venv")
        print("   Then activate it before running this script")
        print()
    
    return True

def check_env_file():
    """Check if .env file exists and is readable"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found in current directory")
        print(f"   Current directory: {os.getcwd()}")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read().strip()
            if not content:
                print("❌ .env file is empty")
                return False
            print(f"✅ .env file found and readable")
            return True
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def check_env_vars():
    """Check if required environment variables are set"""
    # First check if .env file exists
    if not check_env_file():
        print("\n📝 Setup instructions:")
        print("1. Create a .env file in the project root")
        print("2. Add your API keys:")
        print("   GROQ_API_KEY=your_groq_api_key_here")
        print("   OPENWEATHER_API_KEY=your_openweather_api_key_here")
        print("\n🔑 Get your Groq API key from: https://console.groq.com/keys")
        return False
    
    required_vars = ['GROQ_API_KEY']
    optional_vars = ['OPENWEATHER_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var} is set")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure .env file is in the same directory as run.py")
        print("2. Check that your .env file has no spaces around the = sign")
        print("3. Make sure there are no quotes around the API key values")
        print("4. Example .env format:")
        print("   GROQ_API_KEY=gsk_your_actual_api_key_here")
        print("   OPENWEATHER_API_KEY=your_weather_api_key_here")
        return False
    
    # Check optional vars
    for var in optional_vars:
        if not os.getenv(var):
            print(f"ℹ️  Optional: {var} not set (weather features will be limited)")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import requests
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Install dependencies with:")
        print("   pip install -r requirements.txt")
        return False

def display_startup_info():
    """Display startup information"""
    print("=" * 60)
    print("🤖 AI Task Planning Agent")
    print("   Powered by Groq + Llama 3.1 8B Instant")
    print("=" * 60)
    print()

def main():
    """Main startup function"""
    display_startup_info()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check virtual environment
    check_virtual_env()
    
    # Check environment variables
    if not check_env_vars():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Import and run the application
    try:
        from main import app
        
        print("✅ Configuration validated")
        print("✅ Database initialized")
        print("✅ AI Agent ready (Llama 3.1 8B Instant)")
        print("\n🌐 Starting web server...")
        print("📱 Open your browser to: http://localhost:8000")
        print("📊 API documentation: http://localhost:8000/docs")
        print("⏹️  Press Ctrl+C to stop the server")
        print("\n" + "=" * 60)
        
        import uvicorn
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project directory and dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Check your configuration and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
