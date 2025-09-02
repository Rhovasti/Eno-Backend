#!/usr/bin/env python3
import requests
import json
import sys

def test_api_connection(base_url, email, password):
    """
    Test connection to the Eno API.
    
    Args:
        base_url: Base URL of the API
        email: User email for authentication
        password: User password for authentication
    """
    # Normalize base URL
    if not base_url.endswith('/'):
        base_url += '/'
    
    login_url = f"{base_url}api/login"
    
    print(f"Attempting to connect to API at {login_url}")
    
    try:
        # Try to login
        login_data = {
            'email': email,
            'password': password
        }
        
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            user = data.get('user')
            
            print(f"✅ Login successful!")
            print(f"User: {user.get('username')} (ID: {user.get('id')})")
            print(f"Roles: {user.get('roles')}")
            print(f"Admin: {user.get('is_admin')}")
            
            # Try to get games to verify token works
            games_url = f"{base_url}api/games"
            headers = {'Authorization': f'Bearer {token}'}
            
            games_response = requests.get(games_url, headers=headers)
            
            if games_response.status_code == 200:
                games = games_response.json()
                game_count = len(games)
                print(f"✅ Successfully retrieved {game_count} games")
                
                if game_count > 0:
                    print("\nGames:")
                    for game in games:
                        print(f"- {game.get('name')} (ID: {game.get('id')})")
            else:
                print(f"❌ Failed to get games: {games_response.status_code} - {games_response.text}")
                
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Read from config.json if available, otherwise use command line args
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Test connection to Eno API')
    parser.add_argument('--url', help='Base URL of the API')
    parser.add_argument('--email', help='User email for authentication')
    parser.add_argument('--password', help='User password for authentication')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Try to read from config file
    config_file = args.config
    config = {}
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"Loaded configuration from {config_file}")
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    # Use command line args if provided, otherwise use config file
    base_url = args.url or config.get('api', {}).get('base_url')
    email = args.email or config.get('api', {}).get('email')
    password = args.password or config.get('api', {}).get('password')
    
    if not base_url or not email or not password:
        print("Error: Missing required parameters (url, email, password)")
        print("Please provide them as command line args or in config.json")
        sys.exit(1)
    
    success = test_api_connection(base_url, email, password)
    
    if not success:
        sys.exit(1)