#!/usr/bin/env python3
"""
Script to fetch all posts for a specific beat from the Eno game platform.
Supports authentication and handles special characters properly.
"""

import argparse
import json
import requests
from urllib.parse import urljoin

def login(base_url, email, password):
    """Login to the API and return authentication token"""
    login_url = urljoin(base_url, 'api/login')
    payload = {'email': email, 'password': password}
    
    try:
        response = requests.post(login_url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get('token')
    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
        if hasattr(response, 'text'):
            print(f"Response: {response.text}")
        return None

def fetch_posts(base_url, beat_id, token):
    """Fetch all posts for a specific beat ID"""
    posts_url = urljoin(base_url, f'api/beats/{beat_id}/posts')
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    try:
        response = requests.get(posts_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch posts: {e}")
        if hasattr(response, 'text'):
            print(f"Response: {response.text}")
        return []

def display_posts(posts):
    """Display posts in a formatted way"""
    if not posts:
        print("No posts found for this beat.")
        return
    
    print(f"Found {len(posts)} posts:")
    for i, post in enumerate(posts, 1):
        print(f"\n----- Post {i} -----")
        print(f"Title: {post.get('title', 'No title')}")
        print(f"Author: {post.get('username', 'Unknown')}")
        print(f"Type: {post.get('post_type', 'regular')}")
        print(f"Created: {post.get('created_at', 'Unknown date')}")
        print("\nContent:")
        print(post.get('content', 'No content'))
        print("-" * 50)

def save_posts_to_file(posts, filename):
    """Save posts to a file (JSON or text format)"""
    if filename.endswith('.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"Posts saved as JSON to {filename}")
    else:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Total posts: {len(posts)}\n\n")
            for i, post in enumerate(posts, 1):
                f.write(f"Post {i}:\n")
                f.write(f"Title: {post.get('title', 'No title')}\n")
                f.write(f"Author: {post.get('username', 'Unknown')}\n")
                f.write(f"Type: {post.get('post_type', 'regular')}\n")
                f.write(f"Created: {post.get('created_at', 'Unknown date')}\n")
                f.write("\nContent:\n")
                f.write(post.get('content', 'No content'))
                f.write("\n\n" + "-" * 50 + "\n\n")
        print(f"Posts saved as text to {filename}")

def main():
    parser = argparse.ArgumentParser(description='Fetch posts for a specific beat from the Eno game platform')
    parser.add_argument('beat_id', type=int, help='ID of the beat to fetch posts from')
    parser.add_argument('--url', default='http://localhost:3000/', help='Base URL of the Eno API (default: http://localhost:3000/)')
    parser.add_argument('--email', help='Email for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--save', help='Save output to file (specify filename)')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format (default: text)')
    
    args = parser.parse_args()
    
    # Authenticate if credentials provided
    token = None
    if args.email and args.password:
        print(f"Logging in as {args.email}...")
        token = login(args.url, args.email, args.password)
        if token:
            print("Authentication successful")
        else:
            print("Authentication failed, will try to continue without authentication")
    
    # Fetch posts
    print(f"Fetching posts for beat ID {args.beat_id}...")
    posts = fetch_posts(args.url, args.beat_id, token)
    
    # Display posts
    display_posts(posts)
    
    # Save to file if requested
    if args.save:
        filename = args.save
        if not filename.endswith('.json') and not filename.endswith('.txt'):
            filename += '.txt' if args.format == 'text' else '.json'
        save_posts_to_file(posts, filename)

if __name__ == "__main__":
    main()