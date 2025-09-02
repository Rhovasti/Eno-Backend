#!/usr/bin/env python3
"""
API module for managing games, chapters, beats, and posts on the Eno game platform.
Handles creation, retrieval, and response generation.
"""

import logging
import os
import json
import argparse
import requests
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
from dataclasses import dataclass, asdict

from Data_Retrieve_Save_From_to_database.response_generator import (
    ResponseGenerator, 
    GameConfig, 
    ChapterConfig, 
    BeatConfig, 
    PostResponse
)

# Set up logging
logging.basicConfig(
    filename='game_api.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GameAPI:
    """
    API client for the Eno game platform.
    Handles authentication and API interactions.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:3000/",
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        response_generator: Optional[ResponseGenerator] = None
    ):
        """
        Initialize the Game API client.
        
        Args:
            base_url: Base URL of the Eno API
            email: User email for authentication
            password: User password for authentication
            api_key: API key for LLM service (optional)
            response_generator: Optional ResponseGenerator instance
        """
        self.base_url = base_url
        self.email = email
        self.password = password
        self.token = None
        self.user = None
        
        # Initialize response generator if not provided
        if response_generator:
            self.response_generator = response_generator
        else:
            self.response_generator = ResponseGenerator(
                api_key=api_key
            )
        
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
        login_url = urljoin(self.base_url, 'api/login')
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
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
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
    
    def create_game(self, config: GameConfig) -> Dict[str, Any]:
        """
        Create a new game with generated narrative.
        
        Args:
            config: Game configuration
            
        Returns:
            API response with game details
        """
        if not self.token:
            logging.error("Authentication required to create game")
            return {"error": "Authentication required"}
        
        # Generate narrative for the game
        narrative = self.response_generator.create_game_narrative(config)
        
        # Prepare payload for API
        payload = {
            "name": config.name,
            "description": config.description,
            "genre": config.genre,
            "setting": config.world_setting,
            "narrative": narrative,
            "metadata": {
                "themes": config.themes,
                "tone": config.tone,
                "player_freedom": config.player_freedom,
                "narrative_complexity": config.narrative_complexity
            }
        }
        
        # Send request to API
        games_url = urljoin(self.base_url, 'api/games')
        try:
            response = requests.post(games_url, json=payload, headers=self.get_auth_headers())
            response.raise_for_status()
            game_data = response.json()
            logging.info(f"Created game: {config.name} (ID: {game_data.get('id')})")
            return game_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create game: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def create_chapter(self, game_id: int, config: ChapterConfig) -> Dict[str, Any]:
        """
        Create a new chapter in a game with generated narrative.
        
        Args:
            game_id: ID of the game
            config: Chapter configuration
            
        Returns:
            API response with chapter details
        """
        if not self.token:
            logging.error("Authentication required to create chapter")
            return {"error": "Authentication required"}
        
        # Get game details
        game_data = self.get_game(game_id)
        if "error" in game_data:
            return game_data
        
        # Generate narrative for the chapter
        narrative = self.response_generator.create_chapter_narrative(
            game_name=game_data.get('name', f"Game {game_id}"),
            config=config
        )
        
        # Prepare payload for API
        payload = {
            "gameId": game_id,
            "title": config.title,
            "description": config.description,
            "setting": config.setting,
            "narrative": narrative,
            "metadata": {
                "goals": config.goals,
                "key_characters": config.key_characters,
                "key_events": config.key_events
            }
        }
        
        # Send request to API
        chapters_url = urljoin(self.base_url, 'api/chapters')
        try:
            response = requests.post(chapters_url, json=payload, headers=self.get_auth_headers())
            response.raise_for_status()
            chapter_data = response.json()
            logging.info(f"Created chapter: {config.title} (ID: {chapter_data.get('id')}) in game {game_id}")
            return chapter_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create chapter: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def create_beat(
        self,
        chapter_id: int,
        config: BeatConfig
    ) -> Dict[str, Any]:
        """
        Create a new beat in a chapter with generated narrative.
        
        Args:
            chapter_id: ID of the chapter
            config: Beat configuration
            
        Returns:
            API response with beat details
        """
        if not self.token:
            logging.error("Authentication required to create beat")
            return {"error": "Authentication required"}
        
        # Get chapter details
        chapter_data = self.get_chapter(chapter_id)
        if "error" in chapter_data:
            return chapter_data
        
        # Get game details
        game_id = chapter_data.get('gameId')
        game_data = self.get_game(game_id)
        if "error" in game_data:
            return game_data
        
        # Generate narrative for the beat
        narrative = self.response_generator.create_beat_narrative(
            game_name=game_data.get('name', f"Game {game_id}"),
            chapter_title=chapter_data.get('title', f"Chapter {chapter_id}"),
            config=config
        )
        
        # Prepare payload for API
        payload = {
            "chapterId": chapter_id,
            "title": config.title,
            "description": config.description,
            "narrative": narrative,
            "metadata": {
                "mood": config.mood,
                "location": config.location,
                "characters_present": config.characters_present,
                "goals": config.goals
            }
        }
        
        # Send request to API
        beats_url = urljoin(self.base_url, 'api/beats')
        try:
            response = requests.post(beats_url, json=payload, headers=self.get_auth_headers())
            response.raise_for_status()
            beat_data = response.json()
            logging.info(f"Created beat: {config.title} (ID: {beat_data.get('id')}) in chapter {chapter_id}")
            return beat_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create beat: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def create_post(
        self,
        beat_id: int,
        title: str,
        content: str,
        post_type: str = "gm"
    ) -> Dict[str, Any]:
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
        posts_url = urljoin(self.base_url, 'api/posts')
        try:
            response = requests.post(posts_url, json=payload, headers=self.get_auth_headers())
            response.raise_for_status()
            post_data = response.json()
            logging.info(f"Created post: {title} (ID: {post_data.get('id')}) in beat {beat_id}")
            return post_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to create post: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def generate_and_post_response(
        self,
        beat_id: int,
        post_id: int,
        character_name: Optional[str] = None,
        post_type: str = "gm"
    ) -> Dict[str, Any]:
        """
        Generate a response to a post and create a new post with it.
        
        Args:
            beat_id: ID of the beat
            post_id: ID of the post to respond to
            character_name: Optional name of the character (for player posts)
            post_type: Type of post to generate (gm or player)
            
        Returns:
            API response with the new post details
        """
        if not self.token:
            logging.error("Authentication required to generate and post response")
            return {"error": "Authentication required"}
        
        # Get the post to respond to
        post_data = self.get_post(post_id)
        if "error" in post_data:
            return post_data
        
        # Generate response
        post_response = self.response_generator.generate_post_response(
            beat_id=beat_id,
            post_content=post_data.get('content', ''),
            character_name=character_name,
            post_type=post_type
        )
        
        # Create post with the response
        return self.create_post(
            beat_id=beat_id,
            title=post_response.title,
            content=post_response.content,
            post_type=post_response.post_type
        )
    
    def get_game(self, game_id: int) -> Dict[str, Any]:
        """
        Get details of a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Game details
        """
        game_url = urljoin(self.base_url, f'api/games/{game_id}')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(game_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get game {game_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def get_chapter(self, chapter_id: int) -> Dict[str, Any]:
        """
        Get details of a chapter.
        
        Args:
            chapter_id: ID of the chapter
            
        Returns:
            Chapter details
        """
        chapter_url = urljoin(self.base_url, f'api/chapters/{chapter_id}')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(chapter_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get chapter {chapter_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def get_beat(self, beat_id: int) -> Dict[str, Any]:
        """
        Get details of a beat.
        
        Args:
            beat_id: ID of the beat
            
        Returns:
            Beat details
        """
        beat_url = urljoin(self.base_url, f'api/beats/{beat_id}')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(beat_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get beat {beat_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def get_post(self, post_id: int) -> Dict[str, Any]:
        """
        Get details of a post.
        
        Args:
            post_id: ID of the post
            
        Returns:
            Post details
        """
        post_url = urljoin(self.base_url, f'api/posts/{post_id}')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(post_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get post {post_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return {"error": str(e)}
    
    def get_posts_for_beat(self, beat_id: int) -> List[Dict[str, Any]]:
        """
        Get all posts for a beat.
        
        Args:
            beat_id: ID of the beat
            
        Returns:
            List of posts
        """
        posts_url = urljoin(self.base_url, f'api/beats/{beat_id}/posts')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(posts_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get posts for beat {beat_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return []
    
    def get_games(self) -> List[Dict[str, Any]]:
        """
        Get all games.
        
        Returns:
            List of games
        """
        games_url = urljoin(self.base_url, 'api/games')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(games_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get games: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return []
    
    def get_chapters_for_game(self, game_id: int) -> List[Dict[str, Any]]:
        """
        Get all chapters for a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            List of chapters
        """
        chapters_url = urljoin(self.base_url, f'api/games/{game_id}/chapters')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(chapters_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get chapters for game {game_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return []
    
    def get_beats_for_chapter(self, chapter_id: int) -> List[Dict[str, Any]]:
        """
        Get all beats for a chapter.
        
        Args:
            chapter_id: ID of the chapter
            
        Returns:
            List of beats
        """
        beats_url = urljoin(self.base_url, f'api/chapters/{chapter_id}/beats')
        headers = self.get_auth_headers() if self.token else {}
        
        try:
            response = requests.get(beats_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get beats for chapter {chapter_id}: {e}")
            if hasattr(response, 'text'):
                logging.error(f"Response: {response.text}")
            return []


def main():
    """
    Command-line interface for the Game API.
    """
    parser = argparse.ArgumentParser(description='Manage games, chapters, beats, and posts on the Eno game platform')
    parser.add_argument('--url', default='http://localhost:3000/', help='Base URL of the Eno API')
    parser.add_argument('--email', help='Email for authentication')
    parser.add_argument('--password', help='Password for authentication')
    parser.add_argument('--api-key', help='API key for LLM service')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Create game parser
    game_parser = subparsers.add_parser('create-game', help='Create a new game')
    game_parser.add_argument('--name', required=True, help='Name of the game')
    game_parser.add_argument('--description', required=True, help='Description of the game')
    game_parser.add_argument('--genre', required=True, help='Genre of the game')
    game_parser.add_argument('--themes', nargs='+', default=[], help='Themes of the game')
    game_parser.add_argument('--tone', default='dramatic', help='Tone of the game')
    game_parser.add_argument('--setting', default='', help='Setting of the game')
    
    # Create chapter parser
    chapter_parser = subparsers.add_parser('create-chapter', help='Create a new chapter')
    chapter_parser.add_argument('--game-id', type=int, required=True, help='ID of the game')
    chapter_parser.add_argument('--title', required=True, help='Title of the chapter')
    chapter_parser.add_argument('--description', required=True, help='Description of the chapter')
    chapter_parser.add_argument('--goals', nargs='+', default=[], help='Goals of the chapter')
    chapter_parser.add_argument('--setting', default='', help='Setting of the chapter')
    chapter_parser.add_argument('--characters', nargs='+', default=[], help='Key characters in the chapter')
    
    # Create beat parser
    beat_parser = subparsers.add_parser('create-beat', help='Create a new beat')
    beat_parser.add_argument('--chapter-id', type=int, required=True, help='ID of the chapter')
    beat_parser.add_argument('--title', required=True, help='Title of the beat')
    beat_parser.add_argument('--description', required=True, help='Description of the beat')
    beat_parser.add_argument('--mood', default='neutral', help='Mood of the beat')
    beat_parser.add_argument('--location', default='', help='Location of the beat')
    beat_parser.add_argument('--characters', nargs='+', default=[], help='Characters present in the beat')
    beat_parser.add_argument('--goals', nargs='+', default=[], help='Goals of the beat')
    
    # Create post parser
    post_parser = subparsers.add_parser('create-post', help='Create a new post')
    post_parser.add_argument('--beat-id', type=int, required=True, help='ID of the beat')
    post_parser.add_argument('--title', required=True, help='Title of the post')
    post_parser.add_argument('--content', help='Content of the post')
    post_parser.add_argument('--file', help='Read content from file instead of command line')
    post_parser.add_argument('--type', choices=['gm', 'player'], default='gm', help='Type of post')
    
    # Generate response parser
    response_parser = subparsers.add_parser('generate-response', help='Generate a response to a post')
    response_parser.add_argument('--beat-id', type=int, required=True, help='ID of the beat')
    response_parser.add_argument('--post-id', type=int, required=True, help='ID of the post to respond to')
    response_parser.add_argument('--character', help='Name of the character (for player posts)')
    response_parser.add_argument('--type', choices=['gm', 'player'], default='gm', help='Type of post to generate')
    
    # Get game parser
    get_game_parser = subparsers.add_parser('get-game', help='Get details of a game')
    get_game_parser.add_argument('--id', type=int, required=True, help='ID of the game')
    
    # Get chapter parser
    get_chapter_parser = subparsers.add_parser('get-chapter', help='Get details of a chapter')
    get_chapter_parser.add_argument('--id', type=int, required=True, help='ID of the chapter')
    
    # Get beat parser
    get_beat_parser = subparsers.add_parser('get-beat', help='Get details of a beat')
    get_beat_parser.add_argument('--id', type=int, required=True, help='ID of the beat')
    
    # Get post parser
    get_post_parser = subparsers.add_parser('get-post', help='Get details of a post')
    get_post_parser.add_argument('--id', type=int, required=True, help='ID of the post')
    
    # Get posts for beat parser
    get_posts_parser = subparsers.add_parser('get-posts', help='Get all posts for a beat')
    get_posts_parser.add_argument('--beat-id', type=int, required=True, help='ID of the beat')
    
    # Get games parser
    subparsers.add_parser('get-games', help='Get all games')
    
    # Get chapters parser
    get_chapters_parser = subparsers.add_parser('get-chapters', help='Get all chapters for a game')
    get_chapters_parser.add_argument('--game-id', type=int, required=True, help='ID of the game')
    
    # Get beats parser
    get_beats_parser = subparsers.add_parser('get-beats', help='Get all beats for a chapter')
    get_beats_parser.add_argument('--chapter-id', type=int, required=True, help='ID of the chapter')
    
    args = parser.parse_args()
    
    # Initialize API client
    api = GameAPI(
        base_url=args.url,
        email=args.email,
        password=args.password,
        api_key=args.api_key
    )
    
    # Execute command
    if args.command == 'create-game':
        config = GameConfig(
            name=args.name,
            description=args.description,
            genre=args.genre,
            themes=args.themes,
            tone=args.tone,
            world_setting=args.setting
        )
        result = api.create_game(config)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'create-chapter':
        config = ChapterConfig(
            title=args.title,
            description=args.description,
            goals=args.goals,
            setting=args.setting,
            key_characters=args.characters
        )
        result = api.create_chapter(args.game_id, config)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'create-beat':
        config = BeatConfig(
            title=args.title,
            description=args.description,
            mood=args.mood,
            location=args.location,
            characters_present=args.characters,
            goals=args.goals
        )
        result = api.create_beat(args.chapter_id, config)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'create-post':
        # Get content from file if specified
        content = args.content
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {args.file}: {e}")
                return
        
        if not content:
            print("Error: No content provided. Use either --content or --file.")
            return
        
        result = api.create_post(args.beat_id, args.title, content, args.type)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'generate-response':
        result = api.generate_and_post_response(
            args.beat_id,
            args.post_id,
            args.character,
            args.type
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-game':
        result = api.get_game(args.id)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-chapter':
        result = api.get_chapter(args.id)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-beat':
        result = api.get_beat(args.id)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-post':
        result = api.get_post(args.id)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-posts':
        result = api.get_posts_for_beat(args.beat_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-games':
        result = api.get_games()
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-chapters':
        result = api.get_chapters_for_game(args.game_id)
        print(json.dumps(result, indent=2))
    
    elif args.command == 'get-beats':
        result = api.get_beats_for_chapter(args.chapter_id)
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()