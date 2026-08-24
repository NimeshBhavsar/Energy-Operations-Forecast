"""
Google OAuth2 Authentication for Streamlit
==========================================

Provides Google Sign-In functionality using OAuth2 flow.
Compatible with Google Passkeys when users have them configured.
"""

import streamlit as st
import requests
import json
from urllib.parse import urlencode, parse_qs
import secrets
import hashlib
import base64

def get_google_oauth_config():
    """Get Google OAuth configuration from secrets or environment."""
    try:
        # Try Streamlit secrets first
        client_id = st.secrets.get("GOOGLE_CLIENT_ID")
        client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = st.secrets.get("OAUTH_REDIRECT_URI")
    except:
        # Fallback to environment variables
        import os
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("OAUTH_REDIRECT_URI")

    if not all([client_id, client_secret, redirect_uri]):
        return None, "Google OAuth configuration missing. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and OAUTH_REDIRECT_URI."

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }, None

def generate_state_and_verifier():
    """Generate OAuth2 state and PKCE code verifier for security."""
    # Use shorter but still secure tokens for better compatibility
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')

    return state, code_verifier, code_challenge

def get_google_auth_url(config):
    """Generate Google OAuth2 authorization URL."""
    import time
    state = secrets.token_urlsafe(32)

    # Store state in session for verification
    st.session_state['oauth_state'] = state
    st.session_state['oauth_timestamp'] = time.time()

    auth_params = {
        'client_id': config['client_id'],
        'redirect_uri': config['redirect_uri'],
        'response_type': 'code',
        'scope': 'email profile',
        'state': state,
        'access_type': 'online'
    }

    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"
    return auth_url

def exchange_code_for_token(config, authorization_code, state):
    """Exchange authorization code for access token."""
    # Verify state
    if state != st.session_state.get('oauth_state'):
        return None, "Invalid state parameter"

    token_data = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': authorization_code,
        'grant_type': 'authorization_code',
        'redirect_uri': config['redirect_uri']
    }

    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Token exchange failed: {response.status_code}"
    except Exception as e:
        return None, f"Token exchange error: {str(e)}"

def get_user_info(access_token):
    """Get user information from Google API."""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Failed to get user info: {response.status_code}"
    except Exception as e:
        return None, f"User info error: {str(e)}"

def handle_oauth_callback():
    """Handle OAuth callback from Google."""
    # Check for authorization code in URL parameters
    query_params = st.experimental_get_query_params()

    if 'code' in query_params and 'state' in query_params:
        config, error = get_google_oauth_config()
        if error:
            st.error(f"❌ {error}")
            return False

        # Exchange code for token
        authorization_code = query_params['code']
        state_param = query_params['state']
        # Handle case where state might be a list (Streamlit query params can return lists)
        state_value = state_param[0] if isinstance(state_param, list) else state_param

        # The state verification is now handled inside exchange_code_for_token
        token_response, error = exchange_code_for_token(config, authorization_code, state_value)
        if error:
            st.error(f"❌ Authentication failed: {error}")
            # Clear OAuth data
            for key in ['oauth_state', 'oauth_timestamp']:
                if key in st.session_state:
                    del st.session_state[key]
            return False

        # Get user information
        access_token = token_response.get('access_token')
        user_info, error = get_user_info(access_token)
        if error:
            st.error(f"❌ Failed to get user information: {error}")
            return False

        # Store user information in session state
        st.session_state['user'] = {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'verified_email': user_info.get('verified_email', False),
            'access_token': access_token
        }

        # Clear OAuth state after successful authentication
        for key in ['oauth_state', 'oauth_timestamp']:
            if key in st.session_state:
                del st.session_state[key]

        # Clear query parameters by rerunning
        try:
            st.experimental_set_query_params({})
        except TypeError:
            # Fallback for versions where set_query_params doesn't take args
            pass
        st.rerun()

        return True

    return False

def show_login_page():
    """Display the login page with Google Sign-In."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>⚡ Energy Operations Forecast</h1>
        <h3>Please sign in to access the dashboard</h3>
    </div>
    """, unsafe_allow_html=True)

    # Clear any stale OAuth data on fresh login page load
    query_params = st.experimental_get_query_params()
    if not ('code' in query_params or 'state' in query_params):
        # Only clear if we're not in the middle of OAuth callback
        for key in ['oauth_state', 'oauth_timestamp']:
            if key in st.session_state:
                del st.session_state[key]

    # Check OAuth configuration
    config, error = get_google_oauth_config()
    if error:
        st.error(f"❌ {error}")
        st.info("""
        **Setup Required:**
        1. Create Google OAuth client credentials
        2. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and OAUTH_REDIRECT_URI in Streamlit secrets
        3. Configure redirect URI in Google Console
        """)
        return

    # Create three columns for centered button
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        auth_url = get_google_auth_url(config)

        st.markdown(f"""
        <div style="text-align: center; margin: 2rem 0;">
            <a href="{auth_url}" target="_self">
                <button style="
                    background: #4285f4;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 500;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    text-decoration: none;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">
                    <svg width="20" height="20" viewBox="0 0 24 24">
                        <path fill="white" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="white" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="white" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="white" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; color: #666;">
            <p>🔒 Secure authentication using Google OAuth2</p>
            <p>✨ Supports Google Passkeys when available</p>
        </div>
        """, unsafe_allow_html=True)

def show_user_info():
    """Display user information and logout option."""
    user = st.session_state.get('user')
    if not user:
        return

    name = user.get('name', 'Unknown')
    email = user.get('email', 'No email')
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "?"
    verified = " ✓" if user.get('verified_email') else ""

    with st.sidebar:
        st.markdown("---")

        # Rendered as one line so Streamlit keeps it as a single HTML block.
        # Initials are drawn locally rather than fetched from a placeholder
        # image host, which leaves no broken image if the avatar is missing.
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.7rem;'
            'padding:0.15rem 0 0.5rem 0;">'
            '<div style="flex:0 0 auto;width:40px;height:40px;border-radius:50%;'
            'background:#2563eb;color:#fff;display:flex;align-items:center;'
            'justify-content:center;font-weight:700;font-size:0.9rem;'
            'letter-spacing:0.02em;">'
            f'{initials}</div>'
            '<div style="min-width:0;">'
            f'<div style="font-weight:600;font-size:0.9rem;color:#0f172a;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
            f'{name}{verified}</div>'
            f'<div style="font-size:0.78rem;color:#64748b;white-space:nowrap;'
            f'overflow:hidden;text-overflow:ellipsis;">{email}</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )

        # Logout button
        if st.button("🚪 Sign Out", use_container_width=True):
            # Clear user session
            if 'user' in st.session_state:
                del st.session_state['user']
            st.rerun()

def require_login():
    """
    Main authentication function to be called at the top of your Streamlit app.
    Returns True if user is authenticated, False otherwise.
    """
    # DEMO MODE: Skip authentication for showcase
    # Set demo user if not already set
    if 'user' not in st.session_state:
        st.session_state['user'] = {
            'email': 'demo@energy-ops.com',
            'name': 'Demo User',
            'verified_email': True,
            'access_token': 'demo_token'
        }

    # Show user info in sidebar
    show_user_info()
    return True

def require_login_original():
    """
    Original authentication function (for future use with real Gmail).
    """
    # Handle OAuth callback if present
    if handle_oauth_callback():
        return True

    # Check if user is already logged in
    user = st.session_state.get('user')
    if user and user.get('email'):
        show_user_info()
        return True

    # Show login page
    show_login_page()
    return False

def get_current_user():
    """Get the currently logged-in user information."""
    return st.session_state.get('user')

def is_authenticated():
    """Check if user is currently authenticated."""
    user = st.session_state.get('user')
    return user and user.get('email') is not None