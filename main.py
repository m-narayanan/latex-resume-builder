import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import os
from datetime import datetime
import subprocess
import tempfile
import requests
import base64
from typing import Dict, List, Any
import uuid

# Configure Streamlit page
st.set_page_config(
    page_title="LaTeX Resume Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Security: Load sensitive configuration from Streamlit secrets
@st.cache_resource
def init_firebase():
    """Initialize Firebase with secure configuration"""
    try:
        if not firebase_admin._apps:
            # Use Streamlit secrets for secure configuration
            firebase_config = {
                "type": st.secrets.get("firebase_type", "service_account"),
                "project_id": st.secrets.get("firebase_project_id", "your-project-id"),
                "private_key_id": st.secrets.get("firebase_private_key_id", ""),
                "private_key": st.secrets.get("firebase_private_key", "").replace('\\n', '\n'),
                "client_email": st.secrets.get("firebase_client_email", ""),
                "client_id": st.secrets.get("firebase_client_id", ""),
                "auth_uri": st.secrets.get("firebase_auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": st.secrets.get("firebase_token_uri", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": st.secrets.get("firebase_auth_provider_cert_url", "")
            }
            
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
        
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase initialization failed. Please check your configuration. Error: {str(e)}")
        return None

# Initialize Firebase
db = init_firebase()

# LaTeX Templates
LATEX_TEMPLATES = {
    "Standard Single-Column": {
        "name": "Standard Single-Column",
        "description": "Classic professional resume layout",
        "margin": "0.5in",
        "font_size": "11pt",
        "color_scheme": "black"
    },
    "Modern Two-Column": {
        "name": "Modern Two-Column", 
        "description": "Modern layout with skills sidebar",
        "margin": "0.4in",
        "font_size": "10pt",
        "color_scheme": "blue"
    },
    "Compact Professional": {
        "name": "Compact Professional",
        "description": "Space-efficient professional design",
        "margin": "0.3in", 
        "font_size": "10pt",
        "color_scheme": "darkblue"
    }
}

# Default resume data (dummy data for security)
DEFAULT_RESUME_DATA = {
    "personal_info": {
        "name": "John Doe",
        "phone": "+1-555-123-4567",
        "email": "john.doe@email.com",
        "linkedin": "linkedin.com/in/johndoe",
        "github": "github.com/johndoe"
    },
    "professional_summary": "Software Engineer with 3+ years of experience in full-stack development and cloud technologies. Passionate about building scalable applications and solving complex problems.",
    "technical_skills": [
        {"category": "Programming Languages", "skills": "Python, JavaScript, Java, Go"},
        {"category": "Frameworks & Libraries", "skills": "React, Node.js, Django, Flask"},
        {"category": "Databases", "skills": "PostgreSQL, MongoDB, Redis"},
        {"category": "Cloud & DevOps", "skills": "AWS, Docker, Kubernetes, CI/CD"}
    ],
    "experience": [
        {
            "title": "Software Engineer",
            "company": "Tech Solutions Inc.",
            "location": "San Francisco, CA",
            "dates": "Jan 2023 - Present",
            "bullets": [
                "Developed scalable web applications serving 10k+ daily users",
                "Improved system performance by 40% through optimization",
                "Led cross-functional team of 5 developers"
            ]
        },
        {
            "title": "Junior Developer",
            "company": "StartupXYZ",
            "location": "Remote",
            "dates": "Jun 2021 - Dec 2022",
            "bullets": [
                "Built REST APIs using Python and Flask",
                "Implemented automated testing reducing bugs by 50%",
                "Collaborated with product team on feature requirements"
            ]
        }
    ],
    "projects": [
        {
            "name": "E-commerce Platform",
            "tech_stack": "React, Node.js, PostgreSQL, AWS",
            "bullets": [
                "Built full-stack e-commerce platform with payment integration",
                "Implemented secure user authentication and authorization",
                "Deployed using Docker containers on AWS ECS"
            ]
        },
        {
            "name": "Data Analytics Dashboard", 
            "tech_stack": "Python, Streamlit, Pandas, PostgreSQL",
            "bullets": [
                "Created interactive dashboard for business intelligence",
                "Processed and visualized large datasets (1M+ records)",
                "Automated daily reporting with scheduled scripts"
            ]
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "institution": "University of Technology",
            "location": "Boston, MA", 
            "dates": "2017-2021",
            "gpa": "3.8"
        }
    ],
    "certifications": [
        {
            "name": "AWS Certified Developer",
            "issuer": "Amazon Web Services",
            "link": "https://aws.amazon.com/certification/"
        }
    ],
    "section_order": ["professional_summary", "technical_skills", "experience", "projects", "education", "certifications"],
    "custom_sections": {}
}

class ResumeBuilder:
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'resume_data' not in st.session_state:
            st.session_state.resume_data = DEFAULT_RESUME_DATA.copy()
        
        if 'formatting_options' not in st.session_state:
            st.session_state.formatting_options = {
                'template': 'Standard Single-Column',
                'margin_top': 0.5,
                'margin_bottom': 0.5, 
                'margin_left': 0.5,
                'margin_right': 0.5,
                'font_size': 11,
                'item_spacing': 0.04,
                'section_spacing': 0.15
            }
        
        if 'user_authenticated' not in st.session_state:
            st.session_state.user_authenticated = False
            
        if 'user_email' not in st.session_state:
            st.session_state.user_email = ""
            
        if 'user_resumes' not in st.session_state:
            st.session_state.user_resumes = []

    def render_authentication(self):
        """Render authentication interface"""
        st.sidebar.markdown("### 🔐 Authentication")
        
        if st.session_state.user_authenticated:
            st.sidebar.success(f"✅ Logged in as: {st.session_state.user_email}")
            if st.sidebar.button("🚪 Logout"):
                self.logout_user()
        else:
            auth_tab1, auth_tab2 = st.sidebar.tabs(["Login", "Sign Up"])
            
            with auth_tab1:
                with st.form("login_form"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("Login"):
                        self.login_user(email, password)
            
            with auth_tab2:
                with st.form("signup_form"):
                    email = st.text_input("Email", key="signup_email")
                    password = st.text_input("Password", type="password", key="signup_password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    if st.form_submit_button("Sign Up"):
                        if password == confirm_password:
                            self.signup_user(email, password)
                        else:
                            st.error("Passwords don't match!")

    def login_user(self, email: str, password: str):
        """Simulate user login (implement with Firebase Auth)"""
        try:
            # TODO: Implement actual Firebase Authentication
            # user = auth.get_user_by_email(email)
            # Simulate successful login for demo
            st.session_state.user_authenticated = True
            st.session_state.user_email = email
            st.session_state.user_id = str(uuid.uuid4())  # Replace with actual Firebase UID
            st.success("✅ Login successful!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Login failed: {str(e)}")

    def signup_user(self, email: str, password: str):
        """Simulate user signup (implement with Firebase Auth)"""
        try:
            # TODO: Implement actual Firebase Authentication
            # user = auth.create_user(email=email, password=password)
            # Simulate successful signup for demo
            st.session_state.user_authenticated = True
            st.session_state.user_email = email
            st.session_state.user_id = str(uuid.uuid4())  # Replace with actual Firebase UID
            st.success("✅ Account created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Signup failed: {str(e)}")

    def logout_user(self):
        """Logout user and clear session"""
        st.session_state.user_authenticated = False
        st.session_state.user_email = ""
        st.session_state.user_id = ""
        st.session_state.user_resumes = []
        st.success("👋 Logged out successfully!")
        st.rerun()

    def render_resume_management(self):
        """Render resume management interface"""
        if not st.session_state.user_authenticated:
            st.sidebar.info("🔒 Login to save and manage resumes")
            return
        
        st.sidebar.markdown("### 📁 My Resumes")
        
        # Load saved resumes
        if st.sidebar.button("🔄 Refresh Resumes"):
            self.load_user_resumes()
        
        # Resume selection dropdown
        if st.session_state.user_resumes:
            selected_resume = st.sidebar.selectbox(
                "Select Resume:",
                options=["Current"] + [r['name'] for r in st.session_state.user_resumes],
                key="resume_selector"
            )
            
            if selected_resume != "Current":
                if st.sidebar.button(f"📂 Load '{selected_resume}'"):
                    self.load_resume(selected_resume)
                    
                if st.sidebar.button(f"🗑️ Delete '{selected_resume}'", key=f"delete_{selected_resume}"):
                    self.delete_resume(selected_resume)
        
        # Save current resume
        st.sidebar.markdown("---")
        with st.sidebar.form("save_resume_form"):
            resume_name = st.text_input("Resume Name")
            resume_description = st.text_area("Description (optional)", height=60)
            if st.form_submit_button("💾 Save Resume"):
                if resume_name:
                    self.save_resume(resume_name, resume_description)
                else:
                    st.error("Please enter a resume name")
        
        # Quick actions
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("📄 New Resume"):
                self.create_new_resume()
        with col2:
            if st.button("📋 Sample Resume"):
                self.load_sample_resume()

    def load_user_resumes(self):
        """Load user's saved resumes from Firestore"""
        if not db or not st.session_state.user_authenticated:
            return
        
        try:
            docs = db.collection('resumes').where('user_id', '==', st.session_state.user_id).stream()
            resumes = []
            for doc in docs:
                data = doc.to_dict()
                resumes.append({
                    'id': doc.id,
                    'name': data.get('name', 'Untitled'),
                    'description': data.get('description', ''),
                    'created_at': data.get('created_at'),
                    'updated_at': data.get('updated_at')
                })
            st.session_state.user_resumes = resumes
        except Exception as e:
            st.sidebar.error(f"Failed to load resumes: {str(e)}")

    def save_resume(self, name: str, description: str = ""):
        """Save current resume to Firestore"""
        if not db or not st.session_state.user_authenticated:
            st.error("Authentication required to save resume")
            return
        
        try:
            resume_data = {
                'name': name,
                'description': description,
                'user_id': st.session_state.user_id,
                'resume_data': st.session_state.resume_data,
                'formatting_options': st.session_state.formatting_options,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            db.collection('resumes').add(resume_data)
            st.sidebar.success(f"✅ Resume '{name}' saved!")
            self.load_user_resumes()
        except Exception as e:
            st.sidebar.error(f"Failed to save resume: {str(e)}")

    def load_resume(self, resume_name: str):
        """Load a saved resume"""
        try:
            resume = next(r for r in st.session_state.user_resumes if r['name'] == resume_name)
            doc = db.collection('resumes').document(resume['id']).get()
            
            if doc.exists:
                data = doc.to_dict()
                st.session_state.resume_data = data['resume_data']
                st.session_state.formatting_options = data['formatting_options']
                st.success(f"✅ Loaded resume '{resume_name}'")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to load resume: {str(e)}")

    def delete_resume(self, resume_name: str):
        """Delete a saved resume"""
        try:
            resume = next(r for r in st.session_state.user_resumes if r['name'] == resume_name)
            db.collection('resumes').document(resume['id']).delete()
            st.sidebar.success(f"🗑️ Deleted resume '{resume_name}'")
            self.load_user_resumes()
        except Exception as e:
            st.sidebar.error(f"Failed to delete resume: {str(e)}")

    def create_new_resume(self):
        """Create a new blank resume"""
        st.session_state.resume_data = {
            "personal_info": {"name": "", "phone": "", "email": "", "linkedin": "", "github": ""},
            "professional_summary": "",
            "technical_skills": [],
            "experience": [],
            "projects": [],
            "education": [],
            "certifications": [],
            "section_order": ["professional_summary", "technical_skills", "experience", "projects", "education", "certifications"],
            "custom_sections": {}
        }
        st.success("📄 New blank resume created!")
        st.rerun()

    def load_sample_resume(self):
        """Load sample resume with demo data"""
        st.session_state.resume_data = DEFAULT_RESUME_DATA.copy()
        st.success("📋 Sample resume loaded!")
        st.rerun()

    def render_formatting_options(self):
        """Render formatting controls in sidebar"""
        st.sidebar.markdown("### 🎨 Formatting Options")
        
        with st.sidebar.expander("Template & Style", expanded=True):
            st.session_state.formatting_options['template'] = st.selectbox(
                "Template:",
                options=list(LATEX_TEMPLATES.keys()),
                index=list(LATEX_TEMPLATES.keys()).index(st.session_state.formatting_options['template'])
            )
            
            st.session_state.formatting_options['font_size'] = st.slider(
                "Font Size (pt):", 9, 14, st.session_state.formatting_options['font_size']
            )
        
        with st.sidebar.expander("Page Margins", expanded=False):
            st.session_state.formatting_options['margin_top'] = st.slider(
                "Top Margin (in):", 0.2, 1.0, st.session_state.formatting_options['margin_top'], 0.1
            )
            st.session_state.formatting_options['margin_bottom'] = st.slider(
                "Bottom Margin (in):", 0.2, 1.0, st.session_state.formatting_options['margin_bottom'], 0.1
            )
            st.session_state.formatting_options['margin_left'] = st.slider(
                "Left Margin (in):", 0.2, 1.0, st.session_state.formatting_options['margin_left'], 0.1
            )
            st.session_state.formatting_options['margin_right'] = st.slider(
                "Right Margin (in):", 0.2, 1.0, st.session_state.formatting_options['margin_right'], 0.1
            )
        
        with st.sidebar.expander("Spacing", expanded=False):
            st.session_state.formatting_options['item_spacing'] = st.slider(
                "Item Spacing (in):", 0.02, 0.1, st.session_state.formatting_options['item_spacing'], 0.01
            )
            st.session_state.formatting_options['section_spacing'] = st.slider(
                "Section Spacing (in):", 0.05, 0.3, st.session_state.formatting_options['section_spacing'], 0.05
            )

    def render_editor(self):
        """Render the main resume editor"""
        st.markdown("## ✏️ Resume Editor")
        
        # Personal Information
        with st.expander("👤 Personal Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.resume_data['personal_info']['name'] = st.text_input(
                    "Full Name", value=st.session_state.resume_data['personal_info'].get('name', '')
                )
                st.session_state.resume_data['personal_info']['email'] = st.text_input(
                    "Email", value=st.session_state.resume_data['personal_info'].get('email', '')
                )
                st.session_state.resume_data['personal_info']['linkedin'] = st.text_input(
                    "LinkedIn", value=st.session_state.resume_data['personal_info'].get('linkedin', '')
                )
            with col2:
                st.session_state.resume_data['personal_info']['phone'] = st.text_input(
                    "Phone", value=st.session_state.resume_data['personal_info'].get('phone', '')
                )
                st.session_state.resume_data['personal_info']['github'] = st.text_input(
                    "GitHub", value=st.session_state.resume_data['personal_info'].get('github', '')
                )

        # Professional Summary
        with st.expander("📝 Professional Summary", expanded=True):
            st.session_state.resume_data['professional_summary'] = st.text_area(
                "Professional Summary",
                value=st.session_state.resume_data.get('professional_summary', ''),
                height=100,
                help="Write a brief professional summary highlighting your key skills and experience"
            )

        # Technical Skills
        with st.expander("💻 Technical Skills", expanded=True):
            self.render_technical_skills_editor()

        # Experience
        with st.expander("💼 Experience", expanded=True):
            self.render_experience_editor()

        # Projects
        with st.expander("🚀 Projects", expanded=True):
            self.render_projects_editor()

        # Education
        with st.expander("🎓 Education", expanded=True):
            self.render_education_editor()

        # Certifications
        with st.expander("🏆 Certifications", expanded=True):
            self.render_certifications_editor()

    def render_technical_skills_editor(self):
        """Render technical skills section editor"""
        if 'technical_skills' not in st.session_state.resume_data:
            st.session_state.resume_data['technical_skills'] = []
        
        skills = st.session_state.resume_data['technical_skills']
        
        for i, skill in enumerate(skills):
            col1, col2, col3 = st.columns([3, 4, 1])
            with col1:
                skill['category'] = st.text_input(f"Category {i+1}", value=skill.get('category', ''), key=f"skill_cat_{i}")
            with col2:
                skill['skills'] = st.text_input(f"Skills {i+1}", value=skill.get('skills', ''), key=f"skill_list_{i}")
            with col3:
                if st.button("❌", key=f"remove_skill_{i}", help="Remove skill category"):
                    skills.pop(i)
                    st.rerun()
        
        if st.button("➕ Add Skill Category"):
            skills.append({'category': '', 'skills': ''})
            st.rerun()

    def render_experience_editor(self):
        """Render experience section editor"""
        if 'experience' not in st.session_state.resume_data:
            st.session_state.resume_data['experience'] = []
        
        experiences = st.session_state.resume_data['experience']
        
        for i, exp in enumerate(experiences):
            st.markdown(f"**Experience {i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                exp['title'] = st.text_input(f"Job Title", value=exp.get('title', ''), key=f"exp_title_{i}")
                exp['company'] = st.text_input(f"Company", value=exp.get('company', ''), key=f"exp_company_{i}")
            with col2:
                exp['location'] = st.text_input(f"Location", value=exp.get('location', ''), key=f"exp_location_{i}")
                exp['dates'] = st.text_input(f"Dates", value=exp.get('dates', ''), key=f"exp_dates_{i}")
            
            # Bullets
            if 'bullets' not in exp:
                exp['bullets'] = []
            
            for j, bullet in enumerate(exp['bullets']):
                col1, col2 = st.columns([9, 1])
                with col1:
                    exp['bullets'][j] = st.text_area(f"Achievement {j+1}", value=bullet, key=f"exp_bullet_{i}_{j}", height=60)
                with col2:
                    if st.button("❌", key=f"remove_exp_bullet_{i}_{j}", help="Remove achievement"):
                        exp['bullets'].pop(j)
                        st.rerun()
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"➕ Add Achievement", key=f"add_exp_bullet_{i}"):
                    exp['bullets'].append('')
                    st.rerun()
            with col2:
                if st.button(f"🗑️ Remove Experience {i+1}", key=f"remove_exp_{i}"):
                    experiences.pop(i)
                    st.rerun()
            
            st.markdown("---")
        
        if st.button("➕ Add Experience"):
            experiences.append({
                'title': '', 'company': '', 'location': '', 'dates': '', 'bullets': ['']
            })
            st.rerun()

    def render_projects_editor(self):
        """Render projects section editor"""
        if 'projects' not in st.session_state.resume_data:
            st.session_state.resume_data['projects'] = []
        
        projects = st.session_state.resume_data['projects']
        
        for i, project in enumerate(projects):
            st.markdown(f"**Project {i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                project['name'] = st.text_input(f"Project Name", value=project.get('name', ''), key=f"proj_name_{i}")
            with col2:
                project['tech_stack'] = st.text_input(f"Tech Stack", value=project.get('tech_stack', ''), key=f"proj_tech_{i}")
            
            # Bullets
            if 'bullets' not in project:
                project['bullets'] = []
            
            for j, bullet in enumerate(project['bullets']):
                col1, col2 = st.columns([9, 1])
                with col1:
                    project['bullets'][j] = st.text_area(f"Description {j+1}", value=bullet, key=f"proj_bullet_{i}_{j}", height=60)
                with col2:
                    if st.button("❌", key=f"remove_proj_bullet_{i}_{j}", help="Remove description"):
                        project['bullets'].pop(j)
                        st.rerun()
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"➕ Add Description", key=f"add_proj_bullet_{i}"):
                    project['bullets'].append('')
                    st.rerun()
            with col2:
                if st.button(f"🗑️ Remove Project {i+1}", key=f"remove_proj_{i}"):
                    projects.pop(i)
                    st.rerun()
            
            st.markdown("---")
        
        if st.button("➕ Add Project"):
            projects.append({'name': '', 'tech_stack': '', 'bullets': ['']})
            st.rerun()

    def render_education_editor(self):
        """Render education section editor"""
        if 'education' not in st.session_state.resume_data:
            st.session_state.resume_data['education'] = []
        
        education = st.session_state.resume_data['education']
        
        for i, edu in enumerate(education):
            st.markdown(f"**Education {i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                edu['degree'] = st.text_input(f"Degree", value=edu.get('degree', ''), key=f"edu_degree_{i}")
                edu['institution'] = st.text_input(f"Institution", value=edu.get('institution', ''), key=f"edu_institution_{i}")
            with col2:
                edu['location'] = st.text_input(f"Location", value=edu.get('location', ''), key=f"edu_location_{i}")
                edu['dates'] = st.text_input(f"Dates", value=edu.get('dates', ''), key=f"edu_dates_{i}")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                edu['gpa'] = st.text_input(f"GPA (optional)", value=edu.get('gpa', ''), key=f"edu_gpa_{i}")
            with col2:
                if st.button(f"🗑️ Remove Education {i+1}", key=f"remove_edu_{i}"):
                    education.pop(i)
                    st.rerun()
            
            st.markdown("---")
        
        if st.button("➕ Add Education"):
            education.append({
                'degree': '', 'institution': '', 'location': '', 'dates': '', 'gpa': ''
            })
            st.rerun()

    def render_certifications_editor(self):
        """Render certifications section editor"""
        if 'certifications' not in st.session_state.resume_data:
            st.session_state.resume_data['certifications'] = []
        
        certifications = st.session_state.resume_data['certifications']
        
        for i, cert in enumerate(certifications):
            st.markdown(f"**Certification {i+1}**")
            col1, col2, col3 = st.columns([3, 3, 1])
            with col1:
                cert['name'] = st.text_input(f"Certification Name", value=cert.get('name', ''), key=f"cert_name_{i}")
            with col2:
                cert['issuer'] = st.text_input(f"Issuer", value=cert.get('issuer', ''), key=f"cert_issuer_{i}")
            with col3:
                if st.button("❌", key=f"remove_cert_{i}", help="Remove certification"):
                    certifications.pop(i)
                    st.rerun()
            
            cert['link'] = st.text_input(f"Link (optional)", value=cert.get('link', ''), key=f"cert_link_{i}")
            st.markdown("---")
        
        if st.button("➕ Add Certification"):
            certifications.append({'name': '', 'issuer': '', 'link': ''})
            st.rerun()

    def generate_latex(self) -> str:
        """Generate LaTeX code from resume data"""
        data = st.session_state.resume_data
        fmt = st.session_state.formatting_options
        
        # Escape LaTeX special characters
        def escape_latex(text):
            if not text:
                return ""
            chars = {
                '&': r'\&',
                '%': r'\%',
                '$': r'\$',
                '#': r'\#',
                '^': r'\textasciicircum{}',
                '_': r'\_',
                '{': r'\{',
                '}': r'\}',
                '~': r'\textasciitilde{}',
                '\\': r'\textbackslash{}'
            }
            for char, replacement in chars.items():
                text = text.replace(char, replacement)
            return text
        
        # Start building LaTeX
        latex = f"""\\documentclass[a4paper, {fmt['font_size']}pt]{{article}}
\\usepackage{{enumitem}}
\\usepackage{{fontawesome5}}
\\usepackage{{latexsym}}
\\usepackage{{titlesec}}
\\usepackage{{marvosym}}
\\usepackage[usenames,dvipsnames]{{color}}
\\usepackage{{verbatim}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{fancyhdr}}
\\usepackage[english]{{babel}}
\\usepackage{{tabularx}}
\\input{{glyphtounicode}}
\\usepackage[a4paper, top={fmt['margin_top']}in, bottom={fmt['margin_bottom']}in, left={fmt['margin_left']}in, right={fmt['margin_right']}in]{{geometry}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyfoot{{}}
\\renewcommand{{\\headrulewidth}}{{0pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}

\\setlist[itemize]{{itemsep={fmt['item_spacing']}in, topsep=4pt, bottomsep=4pt, leftmargin=0.15in}}
\\urlstyle{{same}}
\\raggedbottom
\\raggedright
\\setlength{{\\tabcolsep}}{{0in}}

\\titleformat{{\\section}}{{\\vspace{{-5pt}}\\scshape\\raggedright\\large}}{{}}{{0em}}{{}}[\\color{{black}}\\titlerule \\vspace{{-5pt}}]

\\pdfgentounicode=1

\\newcommand{{\\resumeItem}}[1]{{\\item\\small{{ #1\\vspace{{-2pt}} }}}}

\\newcommand{{\\resumeSubheading}}[4]{{
  \\vspace{{-3pt}}\\item
  \\begin{{tabular*}}{{0.97\\textwidth}}[t]{{l@{{\\extracolsep{{\\fill}}}}r}}
    \\textbf{{#1}} & \\small #2 \\\\
    \\textit{{\\small#3}} & \\textit{{\\small #4}} \\\\
  \\end{{tabular*}}\\vspace{{-5pt}}
}}

\\newcommand{{\\resumeProjectHeading}}[2]{{
  \\item\\vspace{{-3pt}}
  \\begin{{tabular*}}{{0.97\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
    \\small#1 & \\small #2 \\\\
  \\end{{tabular*}}\\vspace{{-9pt}}
}}

\\renewcommand{{\\labelitemii}}{{$\\vcenter{{\\hbox{{\\tiny$\\bullet$}}}}$}}

\\newcommand{{\\resumeSubHeadingListStart}}{{\\begin{{itemize}}[leftmargin=0.15in, label={{}}]}}
\\newcommand{{\\resumeSubHeadingListEnd}}{{\\end{{itemize}}}}
\\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}[leftmargin=0.2in]}}
\\newcommand{{\\resumeItemListEnd}}{{\\end{{itemize}}\\vspace{{-4pt}}}}

\\begin{{document}}

\\begin{{center}}
  \\textbf{{\\Huge \\scshape {escape_latex(data['personal_info'].get('name', ''))}}} \\\\ \\vspace{{4pt}}
  \\small"""
        
        # Add contact information
        contact_parts = []
        if data['personal_info'].get('phone'):
            contact_parts.append(f"\\faPhone\\ {escape_latex(data['personal_info']['phone'])}")
        if data['personal_info'].get('email'):
            contact_parts.append(f"\\faEnvelope\\ \\href{{mailto:{data['personal_info']['email']}}}{{{escape_latex(data['personal_info']['email'])}}}")
        if data['personal_info'].get('linkedin'):
            linkedin_url = data['personal_info']['linkedin']
            if not linkedin_url.startswith('http'):
                linkedin_url = 'https://' + linkedin_url
            contact_parts.append(f"\\faIcon{{linkedin}} \\href{{{linkedin_url}}}{{{escape_latex(data['personal_info']['linkedin'])}}}")
        if data['personal_info'].get('github'):
            github_url = data['personal_info']['github']
            if not github_url.startswith('http'):
                github_url = 'https://' + github_url
            contact_parts.append(f"\\faGithub\\ \\href{{{github_url}}}{{{escape_latex(data['personal_info']['github'])}}}")
        
        latex += " $|$\n  ".join(contact_parts)
        latex += "\n\\end{center}\n"
        
        # Professional Summary
        if data.get('professional_summary'):
            latex += f"""
\\vspace{{-0.19in}}
\\section{{Professional Summary}}
\\begin{{itemize}}[leftmargin=0.15in, label={{}}]
\\small \\item {escape_latex(data['professional_summary'])}
\\end{{itemize}}
"""
        
        # Technical Skills
        if data.get('technical_skills'):
            latex += f"""
\\vspace{{-{fmt['section_spacing']}in}}
\\section{{Technical Skills}}
\\begin{{itemize}}[leftmargin=0.15in, label={{}}]
"""
            for skill in data['technical_skills']:
                if skill.get('category') and skill.get('skills'):
                    latex += f"\\item \\textbf{{{escape_latex(skill['category'])}:}} {escape_latex(skill['skills'])}\n"
            latex += "\\end{itemize}\n"
        
        # Experience
        if data.get('experience'):
            latex += f"""
\\vspace{{-{fmt['section_spacing']}in}}
\\section{{Experience}}
\\resumeSubHeadingListStart
"""
            for exp in data['experience']:
                if exp.get('title') and exp.get('company'):
                    latex += f"""\\resumeSubheading
    {{{escape_latex(exp.get('title', ''))}}} {{{escape_latex(exp.get('dates', ''))}}}
    {{{escape_latex(exp.get('company', ''))}}} {{{escape_latex(exp.get('location', ''))}}}
"""
                    if exp.get('bullets'):
                        latex += "\\resumeItemListStart\n"
                        for bullet in exp['bullets']:
                            if bullet.strip():
                                latex += f"\\resumeItem{{{escape_latex(bullet)}}}\n"
                        latex += "\\resumeItemListEnd\n"
            latex += "\\resumeSubHeadingListEnd\n"
        
        # Projects
        if data.get('projects'):
            latex += f"""
\\vspace{{-{fmt['section_spacing']}in}}
\\section{{Projects}}
\\resumeSubHeadingListStart
"""
            for project in data['projects']:
                if project.get('name'):
                    tech_stack = f" $|$ \\emph{{{escape_latex(project.get('tech_stack', ''))}}}" if project.get('tech_stack') else ""
                    latex += f"""\\resumeProjectHeading
    {{\\textbf{{{escape_latex(project['name'])}}}{tech_stack}}}{{}}
"""
                    if project.get('bullets'):
                        latex += "\\resumeItemListStart\n"
                        for bullet in project['bullets']:
                            if bullet.strip():
                                latex += f"\\resumeItem{{{escape_latex(bullet)}}}\n"
                        latex += "\\resumeItemListEnd\n"
            latex += "\\resumeSubHeadingListEnd\n"
        
        # Education
        if data.get('education'):
            latex += f"""
\\vspace{{-{fmt['section_spacing']}in}}
\\section{{Education}}
\\resumeSubHeadingListStart
"""
            for edu in data['education']:
                if edu.get('degree') and edu.get('institution'):
                    gpa_text = f"CGPA: {edu['gpa']}" if edu.get('gpa') else ""
                    latex += f"""\\resumeSubheading
    {{{escape_latex(edu['degree'])}}} {{{gpa_text}}}
    {{{escape_latex(edu['institution'])}, {escape_latex(edu.get('location', ''))}}}} {{{escape_latex(edu.get('dates', ''))}}}
"""
            latex += "\\resumeSubHeadingListEnd\n"
        
        # Certifications
        if data.get('certifications'):
            latex += f"""
\\vspace{{-{fmt['section_spacing']}in}}
\\section{{Professional Certifications}}
\\begin{{itemize}}[leftmargin=0.15in, label={{}}]
"""
            for cert in data['certifications']:
                if cert.get('name'):
                    cert_text = f"\\textbf{{{escape_latex(cert['name'])}}}"
                    if cert.get('issuer'):
                        if cert.get('link'):
                            cert_text += f" $|$ \\href{{{cert['link']}}}{{{escape_latex(cert['issuer'])}}}"
                        else:
                            cert_text += f" $|$ {escape_latex(cert['issuer'])}"
                    latex += f"\\small{{\\item{{{cert_text} \\vspace{{2pt}}}}\n}}\n"
            latex += "\\end{itemize}\n"
        
        latex += "\n\\end{document}"
        return latex

    def compile_pdf(self, latex_content: str) -> bytes:
        """Compile LaTeX to PDF using pdflatex"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                tex_file = os.path.join(temp_dir, "resume.tex")
                pdf_file = os.path.join(temp_dir, "resume.pdf")
                
                # Write LaTeX content to file
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Compile with pdflatex
                result = subprocess.run([
                    'pdflatex', '-interaction=nonstopmode', 
                    '-output-directory', temp_dir, tex_file
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(pdf_file):
                    with open(pdf_file, 'rb') as f:
                        return f.read()
                else:
                    st.error("PDF compilation failed. LaTeX errors:")
                    st.code(result.stdout + "\n" + result.stderr)
                    return None
                    
        except subprocess.TimeoutExpired:
            st.error("PDF compilation timed out")
            return None
        except FileNotFoundError:
            st.error("pdflatex not found. Please install TeX Live or MiKTeX")
            return None
        except Exception as e:
            st.error(f"PDF compilation error: {str(e)}")
            return None

    def open_in_overleaf(self, latex_content: str):
        """Open resume in Overleaf"""
        try:
            # Encode LaTeX content for URL
            encoded_content = base64.b64encode(latex_content.encode('utf-8')).decode('utf-8')
            
            # Create Overleaf URL
            overleaf_url = f"https://www.overleaf.com/docs?snip_uri=data:application/x-tex;base64,{encoded_content}"
            
            # Create JavaScript to open in new tab
            js_code = f"""
            <script>
                window.open('{overleaf_url}', '_blank');
            </script>
            """
            
            st.components.v1.html(js_code, height=0)
            st.success("✅ Opening in Overleaf...")
            
        except Exception as e:
            st.error(f"Failed to open in Overleaf: {str(e)}")

    def render_preview_and_export(self):
        """Render preview and export options"""
        st.markdown("## 👁️ Preview & Export")
        
        # Generate LaTeX
        latex_content = self.generate_latex()
        
        # Create tabs
        preview_tab, export_tab = st.tabs(["📄 LaTeX Preview", "📤 Export Options"])
        
        with preview_tab:
            st.markdown("### Generated LaTeX Code")
            st.code(latex_content, language='latex', line_numbers=True)
        
        with export_tab:
            st.markdown("### Export Your Resume")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📝 LaTeX File")
                st.download_button(
                    label="📥 Download .tex File",
                    data=latex_content,
                    file_name=f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tex",
                    mime="text/plain",
                    help="Download LaTeX source code"
                )
            
            with col2:
                st.markdown("#### 🌐 Overleaf")
                if st.button("🔗 Open in Overleaf", help="Open resume in Overleaf editor"):
                    self.open_in_overleaf(latex_content)
            
            st.markdown("---")
            
            # PDF Export
            st.markdown("#### 📄 PDF Export")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎯 Generate PDF", help="Compile LaTeX to PDF"):
                    with st.spinner("Compiling PDF..."):
                        pdf_data = self.compile_pdf(latex_content)
                        if pdf_data:
                            st.session_state.pdf_data = pdf_data
                            st.success("✅ PDF generated successfully!")
            
            with col2:
                if 'pdf_data' in st.session_state:
                    st.download_button(
                        label="📥 Download PDF",
                        data=st.session_state.pdf_data,
                        file_name=f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )

    def run(self):
        """Main application runner"""
        # Header
        st.title("📄 LaTeX Resume Builder")
        st.markdown("Create professional, ATS-optimized resumes with LaTeX quality")
        
        # Sidebar
        self.render_authentication()
        st.sidebar.markdown("---")
        self.render_resume_management()
        st.sidebar.markdown("---")
        self.render_formatting_options()
        
        # Main content
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self.render_editor()
        
        with col2:
            self.render_preview_and_export()
        
        # Footer
        st.markdown("---")
        st.markdown(
            "💡 **Tips:** Use action verbs, quantify achievements, and tailor your resume for each job application."
        )

# Run the application
if __name__ == "__main__":
    app = ResumeBuilder()
    app.run()