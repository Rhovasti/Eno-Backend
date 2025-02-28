#!/usr/bin/env python3
"""
Script to create a new post in a specific beat on the Eno game platform.
Supports authentication, posting as GM or player, and handles special characters properly.
"""

import argparse
import json
import sys
import requests
from urllib.parse import urljoin

def login(base_url, email, password):
    """Login to the API and return authentication token and user details"""
    login_url = urljoin(base_url, 'api/login')
    payload = {'email': email, 'password': password}
    
    try:
        response = requests.post(login_url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get('token'), data.get('user')
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        if hasattr(response, 'text'):
            print(f"Response: {response.text}")
        return None, None

def create_post(base_url, beat_id, title, content, post_type, token):
    """Create a new post in the specified beat"""
    posts_url = urljoin(base_url, 'api/posts')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    payload = {
        'beatId': beat_id,
        'title': title,
        'content': content,
        'postType': post_type
    }
    
    try:
        response = requests.post(posts_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to create post: {e}")
        if hasattr(response, 'text'):
            print(f"Response: {response.text}")
        return None

def read_content_from_file(filename):
    """Read post content from a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        sys.exit(1)

def check_user_roles(user, post_type):
    """Check if user has appropriate role for the post type"""
    if not user:
        return False
    
    # Admin can post anything
    if user.get('is_admin'):
        return True
    
    # Check roles
    try:
        roles = user.get('roles', '[]')
        if isinstance(roles, str):
            roles = json.loads(roles)
        
        # GM posts require GM role
        if post_type == 'gm' and 'gm' not in roles:
            return False
        
        # Player posts require player role, but most users should have this
        if post_type == 'player' and 'player' not in roles:
            return False
            
        return True
    except Exception as e:
        print(f"Error checking user roles: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Create a new post in a beat on the Eno game platform')
    parser.add_argument('beat_id', type=int, help='ID of the beat to post to')
    parser.add_argument('--url', default='http://localhost:3000/', help='Base URL of the Eno API (default: http://localhost:3000/)')
    parser.add_argument('--email', required=True, help='Email for authentication')
    parser.add_argument('--password', required=True, help='Password for authentication')
    parser.add_argument('--title', required=True, help='Title of the post')
    parser.add_argument('--content', help='Content of the post (text)')
    parser.add_argument('--file', help='Read content from file instead of command line')
    parser.add_argument('--type', choices=['gm', 'player'], default='player', help='Post type (default: player)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.content and args.file:
        print("Error: Both --content and --file specified. Please use only one.")
        sys.exit(1)
    
    if not args.content and not args.file:
        print("Error: No content provided. Use either --content or --file.")
        sys.exit(1)
    
    # Get content from file if specified
    content = args.content
    if args.file:
        content = read_content_from_file(args.file)
    
    # Authenticate
    print(f"Logging in as {args.email}...")
    token, user = login(args.url, args.email, args.password)
    
    if not token or not user:
        print("Authentication failed. Cannot continue.")
        sys.exit(1)
    
    print("Authentication successful")
    
    # Check user roles
    if not check_user_roles(user, args.type):
        print(f"Error: Your user account doesn't have the necessary permissions to post as {args.type}.")
        print(f"User roles: {user.get('roles')}")
        sys.exit(1)

    # Debug output
    if args.debug:
        print("\nUser details:")
        print(f"User ID: {user.get('id')}")
        print(f"Username: {user.get('username')}")
        print(f"Roles: {user.get('roles')}")
        print(f"Admin: {user.get('is_admin')}")
        print("\nPost details:")
        print(f"Beat ID: {args.beat_id}")
        print(f"Title: {args.title}")
        print(f"Post type: {args.type}")
        print(f"Content length: {len(content)} characters")
    
    # Create post
    print(f"Creating {args.type} post in beat {args.beat_id}...")
    result = create_post(args.url, args.beat_id, args.title, content, args.type, token)
    
    if result:
        print("Post created successfully!")
        print(f"Post ID: {result.get('id')}")
        print(f"Message: {result.get('message')}")
    else:
        print("Failed to create post")
        sys.exit(1)

if __name__ == "__main__":
    main()