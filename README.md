# 📄 GUI LaTeX Resume Builder

A professional, secure web application for creating ATS-optimized resumes using LaTeX, built with Streamlit and Firebase.

## ✨ Features

- **🔐 Secure Authentication**: Firebase Authentication with email/password
- **💾 Cloud Storage**: Resume data stored securely in Firestore
- **📝 Dynamic Editor**: User-friendly interface for all resume sections
- **🎨 Customizable Templates**: Multiple professional LaTeX templates
- **📄 PDF Export**: Direct PDF compilation with pdflatex
- **🌐 Overleaf Integration**: One-click export to Overleaf
- **📱 Responsive Design**: Works on desktop and mobile
- **🔒 Privacy-First**: All sensitive data secured with Streamlit secrets

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **LaTeX distribution** (for PDF compilation):
   - **Windows**: [MiKTeX](https://miktex.org/download)
   - **macOS**: [MacTeX](https://www.tug.org/mactex/)
   - **Linux**: `sudo apt-get install texlive-full`
3. **Firebase Project** with Firestore enabled

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd latex-resume-builder
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Firebase**:
   - Create a new Firebase project at [Firebase Console](https://console.firebase.google.com)
   - Enable Authentication (Email/Password provider)
   - Enable Firestore Database
   - Generate a service account key (Project Settings → Service Accounts → Generate New Private Key)

4. **Configure secrets**:
   ```bash
   mkdir -p .streamlit
   cp .streamlit/secrets.toml.template .streamlit/secrets.toml
   ```
   
   Edit `.streamlit/secrets.toml` with your Firebase credentials:
   ```toml
   firebase_project_id = "your-project-id"
   firebase_private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----"
   firebase_client_email = "your-service-account@your-project.iam.gserviceaccount.com"
   # ... other Firebase config
   ```

5. **Run the application**:
   ```bash
   streamlit run main.py
   ```

## 🔧 Configuration

### Firebase Setup

1. **Authentication Rules**: Enable Email/Password authentication in Firebase Console
2. **Firestore Security Rules**:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /resumes/{document} {
         allow read, write: if request.auth != null && request.auth.uid == resource.data.user_id;
         allow create: if request.auth != null && request.auth.uid == request.resource.data.user_id;
       }
     }
   }
   ```

### Environment Variables (Production)

For Streamlit Cloud deployment, add these secrets in your app settings:

```toml
firebase_type = "service_account"
firebase_project_id = "your-project-id"
firebase_private_key_id = "your-key-id"
firebase_private_key = "your-private-key"
firebase_client_email = "your-service-account-email"
firebase_client_id = "your-client-id"
firebase_auth_uri = "https://accounts.google.com/o/oauth2/auth"
firebase_token_uri = "https://oauth2.googleapis.com/token"
firebase_auth_provider_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
```

## 📖 Usage

### Creating Your First Resume

1. **Sign Up/Login**: Create an account or log in with existing credentials
2. **Edit Content**: Use the intuitive editor to add your information:
   - Personal information (name, contact details)
   - Professional summary
   - Technical skills (categorized)
   - Work experience with bullet points
   - Projects with descriptions
   - Education details
   - Certifications
3. **Customize Format**: Adjust margins, font size, spacing in the sidebar
4. **Preview**: See real-time LaTeX code generation
5. **Export**: Download PDF, .tex file, or open directly in Overleaf

### Managing Multiple Resumes

- **Save Resume**: Give your resume a unique name and description
- **Load Resume**: Switch between saved resumes instantly
- **Delete Resume**: Remove old versions with confirmation
- **New Resume**: Start fresh with a blank template
- **Sample Resume**: Load demo data for reference

### Template Options

- **Standard Single-Column**: Classic professional layout
- **Modern Two-Column**: Contemporary design with sidebar
- **Compact Professional**: Space-efficient for extensive content

## 🛡️ Security Features

- **Secret Management**: All sensitive data stored in Streamlit secrets
- **Input Sanitization**: LaTeX injection prevention
- **Firebase Security Rules**: User data isolation
- **No Hardcoded Credentials**: Environment-based configuration
- **HTTPS Only**: Secure data transmission

## 🚀 Deployment

### Streamlit Cloud

1. Push your code to GitHub (secrets will be configured in Streamlit Cloud)
2. Connect your repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add your Firebase secrets in the app settings
4. Deploy!

### Self-Hosted

1. Set up your server with Python 3.8+
2. Install LaTeX distribution
3. Configure secrets file
4. Run with: `streamlit run main.py --server.port 8501`

## 📁 Project Structure

```
latex-resume-builder/
├── main.py                 # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore            # Git ignore rules
├── .streamlit/
│   └── secrets.toml      # Firebase credentials (not in repo)
└── templates/            # LaTeX templates (future expansion)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature"`
5. Push and create a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Important Security Notes

- **Never commit** `.streamlit/secrets.toml` to version control
- **Always use** environment variables for production deployments  
- **Regularly rotate** Firebase service account keys
- **Monitor** Firebase usage for unusual activity

## 🐛 Troubleshooting

### Common Issues

1. **PDF Compilation Fails**:
   - Ensure LaTeX is properly installed
   - Check for special characters in resume content
   - Verify system PATH includes LaTeX binaries

2. **Firebase Connection Error**:
   - Verify service account credentials
   - Check Firestore security rules
   - Ensure project ID is correct

3. **Overleaf Integration Issues**:
   - Check internet connection
   - Verify LaTeX content is valid
   - Try downloading .tex file instead

### Getting Help

- 📧 Email: [your-email@domain.com]
- 🐛 Issues: [GitHub Issues](link-to-your-repo/issues)
- 💬 Discussions: [GitHub Discussions](link-to-your-repo/discussions)

---

**Built with ❤️ using Streamlit, Firebase, and LaTeX**