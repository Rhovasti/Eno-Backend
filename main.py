#!/usr/bin/env python3
"""
Main orchestration module for the Eno backend system.
Provides a webhook server for real-time response generation.
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import Dict, List, Optional, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import queue

from Data_Retrieve_Export_From_to_user.game_api import GameAPI
from Data_Retrieve_Save_From_to_database.response_generator import (
    ResponseGenerator, 
    GameConfig, 
    ChapterConfig, 
    BeatConfig
)
from Vector_Database.context_manager import ContextManager
from Knowledge_Graph.knowledge_manager import KnowledgeGraphManager

# Set up logging
logging.basicConfig(
    filename='eno_backend.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eno_backend.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

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
            "vector_db": {
                "path": "./narrative_db",
                "embedding_model": "all-MiniLM-L6-v2"
            },
            "knowledge_graph": {
                "uri": "bolt://localhost:7687",
                "username": "neo4j",
                "password": "nasukili12",
                "database": "population"
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
    
    def set(self, section: str, key: str, value: Any):
        """
        Set a configuration value.
        
        Args:
            section: Section name
            key: Key name
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save_config()


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP request handler for webhooks."""
    
    def __init__(self, *args, game_api: GameAPI, config: Configuration, **kwargs):
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


def process_post_queue(game_api: GameAPI, config: Configuration):
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
                    response = game_api.generate_and_post_response(
                        beat_id=beat_id,
                        post_id=post_id,
                        post_type="gm"  # Always respond as GM
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


def poll_for_posts(game_api: GameAPI, config: Configuration):
    """
    Poll for new posts if webhook is not available.
    
    Args:
        game_api: Game API client
        config: Configuration
    """
    polling_interval = config.get("api", "polling_interval", 60)
    last_processed_posts = {}  # beat_id -> List of post IDs
    
    while True:
        try:
            # Get all games
            games = game_api.get_games()
            
            for game in games:
                game_id = game.get('id')
                if not game_id:
                    continue
                
                # Get chapters for game
                chapters = game_api.get_chapters_for_game(game_id)
                
                for chapter in chapters:
                    chapter_id = chapter.get('id')
                    if not chapter_id:
                        continue
                    
                    # Get beats for chapter
                    beats = game_api.get_beats_for_chapter(chapter_id)
                    
                    for beat in beats:
                        beat_id = beat.get('id')
                        if not beat_id:
                            continue
                        
                        # Get posts for beat
                        posts = game_api.get_posts_for_beat(beat_id)
                        
                        # Initialize if not already in dictionary
                        if beat_id not in last_processed_posts:
                            last_processed_posts[beat_id] = [post.get('id') for post in posts]
                            continue
                        
                        # Check for new posts
                        current_post_ids = [post.get('id') for post in posts if post.get('id')]
                        new_post_ids = [post_id for post_id in current_post_ids if post_id not in last_processed_posts[beat_id]]
                        
                        # Add new posts to processing queue
                        for post_id in new_post_ids:
                            post_queue.put({
                                'post_id': post_id,
                                'beat_id': beat_id,
                                'timestamp': time.time()
                            })
                        
                        # Update last processed posts
                        last_processed_posts[beat_id] = current_post_ids
            
            time.sleep(polling_interval)
        except Exception as e:
            logging.error(f"Error polling for posts: {e}")
            time.sleep(polling_interval)


def run_server(host: str, port: int, game_api: GameAPI, config: Configuration):
    """
    Run webhook server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        game_api: Game API client
        config: Configuration
    """
    # Create handler with game_api and config
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
    parser = argparse.ArgumentParser(description='Eno Backend')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--server', action='store_true', help='Run webhook server')
    parser.add_argument('--polling', action='store_true', help='Run post polling')
    args = parser.parse_args()
    
    # Load configuration
    config = Configuration(args.config)
    
    # Initialize response generator
    response_generator = ResponseGenerator(
        vector_db_path=config.get("vector_db", "path", "./narrative_db"),
        embedding_model=config.get("vector_db", "embedding_model", "all-MiniLM-L6-v2"),
        neo4j_uri=config.get("knowledge_graph", "uri", "bolt://localhost:7687"),
        neo4j_user=config.get("knowledge_graph", "username", "neo4j"),
        neo4j_password=config.get("knowledge_graph", "password", "nasukili12"),
        neo4j_database=config.get("knowledge_graph", "database", "population"),
        llm_service=config.get("llm", "service", "openai"),
        llm_model=config.get("llm", "model", "gpt-3.5-turbo"),
        api_key=config.get("llm", "api_key", "")
    )
    
    # Initialize game API
    game_api = GameAPI(
        base_url=config.get("api", "base_url", "http://localhost:3000/"),
        email=config.get("api", "email", ""),
        password=config.get("api", "password", ""),
        api_key=config.get("llm", "api_key", ""),
        response_generator=response_generator
    )
    
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
    
    # If neither server nor polling is requested, just run in processing mode
    if not args.server and not args.polling:
        logging.info("Running in processing mode (no server or polling)")
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()