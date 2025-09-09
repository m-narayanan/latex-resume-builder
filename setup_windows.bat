@echo off
echo 🚀 LaTeX Resume Builder - Windows Setup
echo =====================================

echo.
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 📁 Creating .streamlit directory...
if not exist ".streamlit" mkdir .streamlit

echo.
echo 📄 Checking secrets file...
if not exist ".streamlit\secrets.toml" (
    echo ⚠️  Secrets file not found. Creating template...
    echo # Firebase Service Account Configuration > .streamlit\secrets.toml
    echo # Replace these values with your actual Firebase credentials >> .streamlit\secrets.toml
    echo. >> .streamlit\secrets.toml
    echo firebase_type = "service_account" >> .streamlit\secrets.toml
    echo firebase_project_id = "your-project-id-here" >> .streamlit\secrets.toml
    echo firebase_private_key_id = "your-private-key-id" >> .streamlit\secrets.toml
    echo firebase_private_key = """-----BEGIN PRIVATE KEY----- >> .streamlit\secrets.toml
    echo YOUR_PRIVATE_KEY_HERE >> .streamlit\secrets.toml
    echo -----END PRIVATE KEY-----""" >> .streamlit\secrets.toml
    echo firebase_client_email = "your-service-account@your-project.iam.gserviceaccount.com" >> .streamlit\secrets.toml
    echo firebase_client_id = "your-client-id" >> .streamlit\secrets.toml
    echo firebase_auth_uri = "https://accounts.google.com/o/oauth2/auth" >> .streamlit\secrets.toml
    echo firebase_token_uri = "https://oauth2.googleapis.com/token" >> .streamlit\secrets.toml
    echo firebase_auth_provider_cert_url = "https://www.googleapis.com/oauth2/v1/certs" >> .streamlit\secrets.toml
    
    echo ✅ Template created at .streamlit\secrets.toml
    echo 🔧 Please edit this file with your actual Firebase credentials
    notepad .streamlit\secrets.toml
) else (
    echo ✅ Secrets file exists
)

echo.
echo 🔒 Securing secrets file...
icacls ".streamlit\secrets.toml" /inheritance:d 2>nul
icacls ".streamlit\secrets.toml" /remove "Everyone" 2>nul
icacls ".streamlit\secrets.toml" /remove "Users" 2>nul

echo.
echo 🔍 Checking LaTeX installation...
pdflatex --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ LaTeX not found! Please install MiKTeX from https://miktex.org/download
    echo 📥 Download and install MiKTeX, then restart this script
    pause
    exit /b 1
) else (
    echo ✅ LaTeX found
)

echo.
echo 🧪 Running setup validation...
python firebase_setup.py

echo.
echo =====================================
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .streamlit\secrets.toml with your Firebase credentials
echo 2. Run: streamlit run main.py
echo 3. Test locally before deploying
echo.
echo 🚀 To start the app: streamlit run main.py
echo =====================================
pause