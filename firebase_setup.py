"""
Firebase Setup Helper Script
Run this script to verify your Firebase configuration and set up Firestore security rules.
"""

import json
import os
from typing import Dict, Any

def create_firestore_rules():
    """Generate Firestore security rules"""
    rules = '''rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own resumes
    match /resumes/{document} {
      allow read, write: if request.auth != null && 
                           request.auth.uid == resource.data.user_id;
      allow create: if request.auth != null && 
                      request.auth.uid == request.resource.data.user_id;
    }
    
    // Prevent access to other collections
    match /{document=**} {
      allow read, write: if false;
    }
  }
}'''
    
    with open('firestore.rules', 'w') as f:
        f.write(rules)
    
    print("✅ Firestore rules created in 'firestore.rules'")
    print("📋 Copy these rules to your Firebase Console:")
    print("   1. Go to Firestore Database → Rules")
    print("   2. Replace the existing rules with the content from 'firestore.rules'")
    print("   3. Click 'Publish'")

def validate_firebase_config():
    """Validate Firebase configuration from secrets"""
    try:
        import streamlit as st
        
        # Check if secrets file exists
        secrets_path = ".streamlit/secrets.toml"
        if not os.path.exists(secrets_path):
            print("❌ Secrets file not found!")
            print(f"📁 Please create {secrets_path} with your Firebase credentials")
            return False
        
        # Check required Firebase secrets
        required_secrets = [
            'firebase_project_id',
            'firebase_private_key', 
            'firebase_client_email'
        ]
        
        missing_secrets = []
        for secret in required_secrets:
            if not st.secrets.get(secret):
                missing_secrets.append(secret)
        
        if missing_secrets:
            print("❌ Missing required Firebase secrets:")
            for secret in missing_secrets:
                print(f"   - {secret}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error validating Firebase config: {str(e)}")
        return False