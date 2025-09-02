#!/usr/bin/env python3
"""
On-demand Game Master script for the Eno game platform.
Processes player posts and generates a GM response when manually invoked.
"""

import logging
import os
import sys
import json
import argparse
import time
import textwrap
from typing import List, Dict, Any, Optional

from Data_Retrieve_Export_From_to_user.game_api import GameAPI
from Data_Retrieve_Save_From_to_database.response_generator import (
    ResponseGenerator,
    PostResponse
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

logger = logging.getLogger(__name__)
# Add console handler to ensure output is visible
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
# Add file handler
file_handler = logging.FileHandler('on_demand_gm.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_file}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def get_beat_posts(game_api: GameAPI, beat_id: int) -> List[Dict[str, Any]]:
    """
    Get all posts for a beat.
    
    Args:
        game_api: Game API client
        beat_id: ID of the beat
        
    Returns:
        List of posts
    """
    posts = game_api.get_posts_for_beat(beat_id)
    logger.info(f"Retrieved {len(posts)} posts for beat {beat_id}")
    return posts

def get_latest_posts_since_gm_post(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Get all player posts since the last GM post.
    
    Args:
        posts: List of all posts for a beat
        
    Returns:
        List of player posts since the last GM post
    """
    # Sort posts by created_at timestamp
    sorted_posts = sorted(posts, key=lambda x: x.get('created_at', ''))
    
    # Find the index of the last GM post
    last_gm_post_index = -1
    for i, post in enumerate(sorted_posts):
        if post.get('post_type') == 'gm':
            last_gm_post_index = i
    
    # Get all player posts after the last GM post
    if last_gm_post_index == -1:
        # No GM posts yet, return all player posts
        return [p for p in sorted_posts if p.get('post_type') == 'player']
    else:
        # Return all player posts after the last GM post
        return [p for p in sorted_posts[last_gm_post_index+1:] if p.get('post_type') == 'player']

def format_player_posts_for_prompt(player_posts: List[Dict[str, Any]]) -> str:
    """
    Format player posts for inclusion in the prompt.
    
    Args:
        player_posts: List of player posts
        
    Returns:
        Formatted string with player posts
    """
    if not player_posts:
        return "No player posts to consider."
    
    formatted_posts = []
    for post in player_posts:
        formatted_posts.append(
            f"Player: {post.get('username', 'Unknown')}\n"
            f"Title: {post.get('title', 'Untitled')}\n"
            f"Content: {post.get('content', '')}\n"
        )
    
    return "Recent player posts:\n\n" + "\n".join(formatted_posts)

def print_in_box(text: str, width: int = 80):
    """
    Print text in a box for better visibility.
    
    Args:
        text: Text to print
        width: Width of the box
    """
    print("╔" + "═" * (width - 2) + "╗")
    
    # Wrap text to fit within the box
    wrapped_lines = []
    for line in text.split('\n'):
        if len(line) > width - 4:
            # Wrap this line
            wrapped = textwrap.wrap(line, width - 4)
            wrapped_lines.extend(wrapped)
        else:
            wrapped_lines.append(line)
    
    for line in wrapped_lines:
        padding = width - 4 - len(line)
        print("║ " + line + " " * padding + " ║")
    
    print("╚" + "═" * (width - 2) + "╝")

def get_user_confirmation(title: str, content: str, auto_mode: bool = False) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Get user confirmation and optional edits before posting.
    
    Args:
        title: Post title
        content: Post content
        auto_mode: If True, skip confirmation and always return True
        
    Returns:
        Tuple of (confirmed, new_title, new_content)
        If confirmed is False, new_title and new_content are None
    """
    if auto_mode:
        return True, None, None
    
    print("\n")
    print_in_box(f"TITLE: {title}", 100)
    print("\n")
    print_in_box(content, 100)
    print("\n")
    
    while True:
        choice = input("Post this response? [Y]es/[N]o/[E]dit: ").strip().lower()
        
        if choice == 'y' or choice == 'yes':
            return True, None, None
        elif choice == 'n' or choice == 'no':
            print("Skipping this post.")
            return False, None, None
        elif choice == 'e' or choice == 'edit':
            print("\nEditing mode:")
            new_title = input(f"New title [{title}]: ").strip()
            if not new_title:
                new_title = title
            
            print("\nEnter new content (type 'DONE' on a line by itself when finished):")
            print("--------------------------------")
            new_content_lines = []
            while True:
                line = input()
                if line == 'DONE':
                    break
                new_content_lines.append(line)
            
            new_content = "\n".join(new_content_lines)
            if not new_content:
                new_content = content
            
            print("\nUpdated post:")
            print_in_box(f"TITLE: {new_title}", 100)
            print("\n")
            print_in_box(new_content, 100)
            print("\n")
            
            confirm = input("Confirm these changes? [Y]es/[N]o (to edit again): ").strip().lower()
            if confirm == 'y' or confirm == 'yes':
                return True, new_title, new_content
        else:
            print("Invalid choice. Please enter Y, N, or E.")

def generate_gm_response(
    game_api: GameAPI,
    beat_id: int,
    game_name: str,
    chapter_title: str,
    beat_title: str,
    auto_mode: bool = False,
    conditional_mode: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Generate a GM response based on player posts since the last GM post.
    
    Args:
        game_api: Game API client
        beat_id: ID of the beat
        game_name: Name of the game
        chapter_title: Title of the chapter
        beat_title: Title of the beat
        auto_mode: If True, don't ask for confirmation
        conditional_mode: If True, ask for confirmation before posting
        
    Returns:
        Created post or None if there are no player posts to respond to
    """
    # Get all posts for the beat
    all_posts = get_beat_posts(game_api, beat_id)
    
    # Get player posts since the last GM post
    player_posts = get_latest_posts_since_gm_post(all_posts)
    
    if not player_posts:
        logger.info(f"No player posts to respond to for beat {beat_id}")
        return None
    
    logger.info(f"Generating response to {len(player_posts)} player posts for beat {beat_id}")
    
    # Format player posts for the prompt
    player_posts_text = format_player_posts_for_prompt(player_posts)
    
    # Create a custom prompt with game, chapter, and beat context
    custom_prompt = f"""
Game: {game_name}
Chapter: {chapter_title}
Beat: {beat_title}

{player_posts_text}

Based on the player posts above, create an engaging GM response that moves the narrative forward.
Consider the actions and intentions of all players involved.
The response should acknowledge player contributions and present new challenges or developments.
"""
    
    # Generate response using the ResponseGenerator
    post_response = game_api.response_generator.generate_post_response(
        beat_id=beat_id,
        post_content=custom_prompt,
        post_type="gm"
    )
    
    # If in conditional mode, get user confirmation and optional edits
    if conditional_mode:
        confirmed, new_title, new_content = get_user_confirmation(
            post_response.title, 
            post_response.content,
            auto_mode
        )
        
        if not confirmed:
            logger.info(f"User skipped response for beat {beat_id}")
            return None
        
        if new_title is not None:
            post_response.title = new_title
        
        if new_content is not None:
            post_response.content = new_content
    
    # Create post with the response
    created_post = game_api.create_post(
        beat_id=beat_id,
        title=post_response.title,
        content=post_response.content,
        post_type="gm"
    )
    
    logger.info(f"Created GM response post for beat {beat_id} (Post ID: {created_post.get('id')})")
    return created_post

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='On-demand Game Master for the Eno platform')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--game-id', type=int, help='ID of the game to process')
    parser.add_argument('--chapter-id', type=int, help='ID of the chapter to process')
    parser.add_argument('--beat-id', type=int, help='ID of the beat to process')
    parser.add_argument('--all-beats', action='store_true', help='Process all beats in the specified chapter')
    parser.add_argument('--all-chapters', action='store_true', help='Process all chapters in the specified game')
    parser.add_argument('--all-games', action='store_true', help='Process all games')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    # Add options for auto vs conditional modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--auto', action='store_true', help='Automatically post generated responses without confirmation')
    mode_group.add_argument('--conditional', action='store_true', help='Ask for confirmation and allow edits before posting')
    
    args = parser.parse_args()
    
    # Enable debug if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize response generator
    api_key = config.get("llm", {}).get("api_key", "")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            logger.info("Using OpenAI API key from environment variable")
        else:
            logger.error("No OpenAI API key found in config or environment variables")
            return
    
    logger.info("Initializing response generator")
    response_generator = ResponseGenerator(
        vector_db_path=config.get("vector_db", {}).get("path", "./narrative_db"),
        embedding_model=config.get("vector_db", {}).get("embedding_model", "all-MiniLM-L6-v2"),
        neo4j_uri=config.get("knowledge_graph", {}).get("uri", "bolt://localhost:7687"),
        neo4j_user=config.get("knowledge_graph", {}).get("username", "neo4j"),
        neo4j_password=config.get("knowledge_graph", {}).get("password", "nasukili12"),
        neo4j_database=config.get("knowledge_graph", {}).get("database", "population"),
        llm_service=config.get("llm", {}).get("service", "openai"),
        llm_model=config.get("llm", {}).get("model", "gpt-3.5-turbo"),
        api_key=api_key
    )
    
    # Initialize game API
    logger.info("Initializing game API")
    game_api = GameAPI(
        base_url=config.get("api", {}).get("base_url", "http://localhost:3000/"),
        email=config.get("api", {}).get("email", ""),
        password=config.get("api", {}).get("password", ""),
        response_generator=response_generator
    )
    
    # Determine operation mode
    auto_mode = args.auto
    conditional_mode = args.conditional or not auto_mode  # Default to conditional if neither is specified
    
    # Display mode information
    if auto_mode:
        logger.info("Running in AUTO mode: No confirmation required")
    else:
        logger.info("Running in CONDITIONAL mode: Confirmation required before posting")
    
    # Process based on command-line arguments
    if args.all_games:
        # Process all games
        games = game_api.get_games()
        for game in games:
            game_id = game.get('id')
            game_name = game.get('name')
            logger.info(f"Processing game: {game_name} (ID: {game_id})")
            
            # Get all chapters for this game
            chapters = game_api.get_chapters_for_game(game_id)
            for chapter in chapters:
                chapter_id = chapter.get('id')
                chapter_title = chapter.get('title')
                logger.info(f"Processing chapter: {chapter_title} (ID: {chapter_id})")
                
                # Get all beats for this chapter
                beats = game_api.get_beats_for_chapter(chapter_id)
                for beat in beats:
                    beat_id = beat.get('id')
                    beat_title = beat.get('title')
                    logger.info(f"Processing beat: {beat_title} (ID: {beat_id})")
                    
                    # Generate GM response for this beat
                    generate_gm_response(
                        game_api, 
                        beat_id, 
                        game_name, 
                        chapter_title, 
                        beat_title,
                        auto_mode,
                        conditional_mode
                    )
    
    elif args.game_id and args.all_chapters:
        # Process all chapters in the specified game
        game = game_api.get_game(args.game_id)
        game_name = game.get('name')
        logger.info(f"Processing game: {game_name} (ID: {args.game_id})")
        
        # Get all chapters for this game
        chapters = game_api.get_chapters_for_game(args.game_id)
        for chapter in chapters:
            chapter_id = chapter.get('id')
            chapter_title = chapter.get('title')
            logger.info(f"Processing chapter: {chapter_title} (ID: {chapter_id})")
            
            # Get all beats for this chapter
            beats = game_api.get_beats_for_chapter(chapter_id)
            for beat in beats:
                beat_id = beat.get('id')
                beat_title = beat.get('title')
                logger.info(f"Processing beat: {beat_title} (ID: {beat_id})")
                
                # Generate GM response for this beat
                generate_gm_response(
                    game_api, 
                    beat_id, 
                    game_name, 
                    chapter_title, 
                    beat_title,
                    auto_mode,
                    conditional_mode
                )
    
    elif args.chapter_id and args.all_beats:
        # Process all beats in the specified chapter
        chapter = game_api.get_chapter(args.chapter_id)
        chapter_title = chapter.get('title')
        game_id = chapter.get('gameId')
        game = game_api.get_game(game_id)
        game_name = game.get('name')
        logger.info(f"Processing chapter: {chapter_title} (ID: {args.chapter_id}) in game: {game_name}")
        
        # Get all beats for this chapter
        beats = game_api.get_beats_for_chapter(args.chapter_id)
        for beat in beats:
            beat_id = beat.get('id')
            beat_title = beat.get('title')
            logger.info(f"Processing beat: {beat_title} (ID: {beat_id})")
            
            # Generate GM response for this beat
            generate_gm_response(
                game_api, 
                beat_id, 
                game_name, 
                chapter_title, 
                beat_title,
                auto_mode,
                conditional_mode
            )
    
    elif args.beat_id:
        # Process the specified beat
        beat = game_api.get_beat(args.beat_id)
        beat_title = beat.get('title')
        chapter_id = beat.get('chapterId')
        chapter = game_api.get_chapter(chapter_id)
        chapter_title = chapter.get('title')
        game_id = chapter.get('gameId')
        game = game_api.get_game(game_id)
        game_name = game.get('name')
        logger.info(f"Processing beat: {beat_title} (ID: {args.beat_id}) in chapter: {chapter_title}, game: {game_name}")
        
        # Generate GM response for this beat
        generate_gm_response(
            game_api, 
            args.beat_id, 
            game_name, 
            chapter_title, 
            beat_title,
            auto_mode,
            conditional_mode
        )
    
    else:
        logger.error("Please specify what to process (--beat-id, --chapter-id with --all-beats, --game-id with --all-chapters, or --all-games)")
        parser.print_help()

if __name__ == "__main__":
    main()