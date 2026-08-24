#!/usr/bin/env python3
"""
Simple OAuth Test
"""

import requests
from urllib.parse import urlencode

# Your credentials
CLIENT_ID = "274670975613-nra48augu9dqhh1jnruj7fcl95rqver9.apps.googleusercontent.com"
REDIRECT_URI = "http://localhost:8501"

def test_oauth_url():
    """Test OAuth URL generation"""
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'email profile',
        'state': 'test123'
    }

    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"
    print("OAuth URL:")
    print(auth_url)
    print("\nTest by opening this URL in browser:")
    print(auth_url)

if __name__ == "__main__":
    test_oauth_url()