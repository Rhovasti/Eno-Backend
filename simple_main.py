#!/usr/bin/env python3
"""
Simplified main orchestration module for the Eno backend system.
Provides a webhook server for real-time response generation without requiring all dependencies.
"""

import os
import sys
import json
import logging
import argparse
import time
import requests
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Clear existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add file handler
file_handler = logging.FileHandler('eno_backend.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Add console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Global queue for post processing
post_queue = queue.Queue()

class Configuration:
    """Configuration for the Eno backend system."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize with configuration from file.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = {
            "server": {
                "host": "0.0.0.0",
                "port": 5000,
                "webhook_token": "secret_token"
            },
            "api": {
                "base_url": "http://localhost:3000/",
                "email": "",
                "password": "",
                "polling_interval": 60  # seconds
            },
            "llm": {
                "service": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": ""
            },
            "auto_respond": {
                "enabled": True,
                "player_posts_only": True,
                "delay": 10  # seconds
            }
        }
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    # Update configuration with values from file
                    for section in file_config:
                        if section in self.config:
                            self.config[section].update(file_config[section])
                        else:
                            self.config[section] = file_config[section]
                logging.info(f"Loaded configuration from {self.config_file}")
            else:
                self.save_config()
                logging.info(f"Created default configuration file at {self.config_file}")
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logging.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Section name
            key: Key name
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default

class SimpleGameAPI:
    """
    Simplified API client for the Eno game platform.
    Handles authentication and API interactions.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:3000/",
        email: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize the Game API client.
        
        Args:
            base_url: Base URL of the Eno API
            email: User email for authentication
            password: User password for authentication
        """
        self.base_url = base_url
        self.email = email
        self.password = password
        self.token = None
        self.user = None
        
        # Authenticate if credentials are provided
        if email and password:
            self.login()
            
        logging.info(f"Initialized Game API client with base URL: {base_url}")
    
    def login(self) -> bool:
        """
        Login to the API and obtain authentication token.
        
        Returns:
            True if login was successful, False otherwise
        """
        login_url = f"{self.base_url}api/login"
        if login_url.endswith('/'):
            login_url = login_url[:-1]
        
        payload = {'email': self.email, 'password': self.password}
        
        try:
            response = requests.post(login_url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.token = data.get('token')
            self.user = data.get('user')
            logging.info(f"Login successful for user: {self.email}")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Login failed: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Response: {e.response.text}")
            self.token = None
            self.user = None
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Headers dictionary with authentication token
        """
        if not self.token:
            logging.warning("No authentication token available. Call login() first.")
            return {}
        
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def get_post(self, post_id: int) -> Dict[str, Any]:
        """
        Get details of a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Post details
        """
        post_url = f"{self.base_url}api/posts/{post_id}"
        if post_url.endswith('/'):
            post_url = post_url[:-1]
            
        headers = self.get_auth_headers()
        
        try:
            response = requests.get(post_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get post {post_id}: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Response: {e.response.text}")
            return {"error": str(e)}
    
    def create_post(self, beat_id: int, title: str, content: str, post_type: str = "gm") -> Dict[str, Any]:
        """
        Create a new post in a beat.
        
        Args:
            beat_id: ID of the beat
            title: Title of the post
            content: Content of the post
            post_type: Type of post (gm or player)
            
        Returns:
            API response with post details
        """
        if not self.token:
            logging.error("Authentication required to create post")
            return {"error": "Authentication required"}
        
        # Prepare payload for API
        payload = {
            "beatId": beat_id,
            "title": title,
            "content": content,
            "postType": post_type
        }
        
        # Send request to API
        posts_url = f"{self.base_url}api/posts"
        if posts_url.endswith('/'):
            posts_url = posts_url[:-1]
            
        try:
            response = requests.post(posts_url, json=payload, headers=self.get_auth_headers())
            response.raise_for_status()
            post_data = response.json()
            logging.info(f"Created post: {title} (ID: {post_data.get('id')}) in beat {beat_id}")
            return post_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create post: {e}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Response: {e.response.text}")
            return {"error": str(e)}
    
    def generate_response(self, beat_id: int, post_id: int) -> Dict[str, Any]:
        """
        Generate a simple response to a post.
        
        Args:
            beat_id: ID of the beat
            post_id: ID of the post to respond to
            
        Returns:
            Generated response
        """
        # Get the post to respond to
        post_data = self.get_post(post_id)
        if "error" in post_data:
            return post_data
        
        # Generate a simple response
        title = f"Response to {post_data.get('title', 'your post')}"
        content = f"""
        Thank you for your post: "{post_data.get('title', 'untitled')}".
        
        This is an automated response from the Eno backend system. In a real implementation,
        this would be generated using an LLM with context from the knowledge graph and vector database.
        
        Best regards,
        Eno Game Master
        """
        
        # Create post with the response
        return self.create_post(
            beat_id=beat_id,
            title=title,
            content=content,
            post_type="gm"
        )


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for webhooks."""
    
    def __init__(self, *args, game_api=None, config=None, **kwargs):
        self.game_api = game_api
        self.config = config
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        
        # Get request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(post_data)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        # Validate webhook token
        webhook_token = self.config.get("server", "webhook_token", "")
        if webhook_token and self.headers.get('X-Webhook-Token') != webhook_token:
            self.send_response(401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized"}).encode())
            return
        
        if parsed_path.path == '/webhook/post':
            # Handle new post webhook
            if 'postId' in data and 'beatId' in data:
                # Add to processing queue
                post_queue.put({
                    'post_id': data['postId'],
                    'beat_id': data['beatId'],
                    'timestamp': time.time()
                })
                
                self.send_response(202)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "accepted"}).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing postId or beatId"}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())


def process_post_queue(game_api, config):
    """
    Process posts in the queue.
    
    Args:
        game_api: Game API client
        config: Configuration
    """
    auto_respond = config.get("auto_respond", "enabled", True)
    player_posts_only = config.get("auto_respond", "player_posts_only", True)
    delay = config.get("auto_respond", "delay", 10)
    
    while True:
        try:
            if not post_queue.empty():
                post_data = post_queue.get()
                
                # Check if enough time has passed (to avoid responding too quickly)
                elapsed_time = time.time() - post_data['timestamp']
                if elapsed_time < delay:
                    # Not enough time has passed, put back in queue with original timestamp
                    post_queue.put(post_data)
                    time.sleep(1)
                    continue
                
                beat_id = post_data['beat_id']
                post_id = post_data['post_id']
                
                # Get post details
                post = game_api.get_post(post_id)
                
                # Skip if there was an error or post is not a player post (if player_posts_only is True)
                if "error" in post or (player_posts_only and post.get("postType") != "player"):
                    post_queue.task_done()
                    continue
                
                if auto_respond:
                    # Generate and post response
                    response = game_api.generate_response(
                        beat_id=beat_id,
                        post_id=post_id
                    )
                    
                    if "error" not in response:
                        logging.info(f"Generated response to post {post_id} in beat {beat_id} (Response ID: {response.get('id')})")
                    else:
                        logging.error(f"Failed to generate response: {response.get('error')}")
                
                post_queue.task_done()
            else:
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error processing post queue: {e}")
            time.sleep(5)


def poll_for_posts(game_api, config):
    """
    Poll for new posts if webhook is not available.
    Not implemented in this simplified version.
    """
    logging.info("Post polling is not implemented in the simplified version")
    while True:
        time.sleep(60)


def run_server(host, port, game_api, config):
    """
    Run webhook server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        game_api: Game API client
        config: Configuration
    """
    # Use a custom handler class that includes game_api and config
    handler = lambda *args, **kwargs: WebhookHandler(*args, game_api=game_api, config=config, **kwargs)
    
    # Create server
    server = HTTPServer((host, port), handler)
    logging.info(f"Starting server on {host}:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logging.info(f"Server stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Simplified Eno Backend')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--server', action='store_true', help='Run webhook server')
    parser.add_argument('--polling', action='store_true', help='Run post polling')
    parser.add_argument('--test', action='store_true', help='Test mode - just verify API connection')
    args = parser.parse_args()
    
    # Load configuration
    config = Configuration(args.config)
    
    # Initialize game API
    game_api = SimpleGameAPI(
        base_url=config.get("api", "base_url", "http://localhost:3000/"),
        email=config.get("api", "email", ""),
        password=config.get("api", "password", "")
    )
    
    # Test mode - just verify API connection and exit
    if args.test:
        if game_api.login():
            print("✅ API connection successful")
            return 0
        else:
            print("❌ API connection failed")
            return 1
    
    # Start post processing thread
    post_processor_thread = threading.Thread(
        target=process_post_queue,
        args=(game_api, config),
        daemon=True
    )
    post_processor_thread.start()
    
    # Start polling thread if requested
    if args.polling:
        polling_thread = threading.Thread(
            target=poll_for_posts,
            args=(game_api, config),
            daemon=True
        )
        polling_thread.start()
    
    # Start server if requested
    if args.server:
        run_server(
            host=config.get("server", "host", "0.0.0.0"),
            port=config.get("server", "port", 5000),
            game_api=game_api,
            config=config
        )
    
    # If neither server nor polling is requested, just run in test mode
    if not args.server and not args.polling and not args.test:
        logging.info("Running in test mode (no server or polling specified)")
        if game_api.login():
            print("✅ API connection successful")
            return 0
        else:
            print("❌ API connection failed")
            return 1


if __name__ == "__main__":
    sys.exit(main())