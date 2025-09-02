# Eno Backend System

A narrative gaming backend system that generates responses and creates games, chapters, beats, and posts using Knowledge Graph and Vector Database components.

## Components

### 1. Knowledge Graph

- Stores entities like characters, locations, and events as nodes
- Maintains relationships between entities
- Provides context for narrative generation
- Based on Neo4j

### 2. Vector Database

- Stores narrative memories and textual context
- Enables semantic search for relevant context
- Supports memory management with importance and expiration
- Based on ChromaDB

### 3. Response Generator

- Creates narratives for games, chapters, and beats
- Generates responses to posts
- Uses the Knowledge Graph and Vector Database for context
- Integrates with LLM services (OpenAI by default)

### 4. Game API

- Provides an interface to the frontend messaging board
- Handles creation of games, chapters, beats, and posts
- Manages authentication and API interactions

### 5. Main Orchestration

- Provides webhook server for real-time response generation
- Supports polling for new posts if webhooks not available
- Manages configuration and processing queue

## Installation

1. Clone the repository:
```
git clone https://github.com/your-username/eno-backend.git
cd eno-backend
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Install Neo4j Community Edition for the Knowledge Graph component.

4. Configure the system by editing `config.json` (created on first run) or providing environment variables.

## Configuration

The system uses a JSON configuration file with the following structure:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "webhook_token": "secret_token"
  },
  "api": {
    "base_url": "http://localhost:3000/",
    "email": "your-email@example.com",
    "password": "your-password",
    "polling_interval": 60
  },
  "llm": {
    "service": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "your-api-key"
  },
  "vector_db": {
    "path": "./narrative_db",
    "embedding_model": "all-MiniLM-L6-v2"
  },
  "knowledge_graph": {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "your-password",
    "database": "population"
  },
  "auto_respond": {
    "enabled": true,
    "player_posts_only": true,
    "delay": 10
  }
}
```

## Usage

### Running the Backend System

Start the system with webhooks and polling:

```
python main.py --server --polling
```

Options:
- `--server`: Run the webhook server for real-time response generation
- `--polling`: Enable polling for new posts
- `--config`: Specify path to configuration file (default: `config.json`)

### Creating Games, Chapters, Beats, and Posts

Use the Game API module for content creation:

```
python Data_Retrieve_Export_From_to_user/game_api.py create-game --name "My Game" --description "An epic adventure" --genre "Fantasy" --themes "heroic" "dark" --email "user@example.com" --password "password"
```

Available commands:
- `create-game`: Create a new game
- `create-chapter`: Create a new chapter in a game
- `create-beat`: Create a new beat in a chapter
- `create-post`: Create a new post in a beat
- `generate-response`: Generate a response to a post
- `get-game`, `get-chapter`, `get-beat`, `get-post`: Get details of existing content
- `get-games`, `get-chapters`, `get-beats`, `get-posts`: Get lists of content

### Webhooks

The webhook server listens for POST requests to `/webhook/post` with the following payload:

```json
{
  "postId": 123,
  "beatId": 456
}
```

Include the webhook token in the `X-Webhook-Token` header for authentication.

### Testing

Run tests to verify functionality:

```
python -m unittest discover tests
```

## Development

This project follows Python code style guidelines outlined in PEP 8. See `CLAUDE.md` for additional development guidelines.

### Project Structure

- `/Knowledge_Graph`: Knowledge graph components
- `/Vector_Database`: Vector database components
- `/Data_Retrieve_Export_From_to_user`: API clients for frontend interaction
- `/Data_Retrieve_Save_From_to_database`: Response generation components
- `/tools`: Utility tools for various purposes

## License

This project is licensed under the terms of the included LICENSE file.