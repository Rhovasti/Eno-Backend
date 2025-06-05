# Eno-Backend

Eno-Backend is a backend program designed to retrieve posts from a narrative gaming messaging board and generate replies or story continuations. It interacts with a world model composed of a knowledge graph and a vector database to create dynamic and contextually relevant content.

## Project Overview

The goal of this project is to develop a backend program that retrieves posts from a narrative gaming messaging board and generates replies or story continuations based on the content of the posts. This backend should seamlessly interact with both the frontend (messaging board) and the underlying world model, which consists of a knowledge graph and a vector database.

### Objectives

- Retrieve posts from the messaging board in real-time or at set intervals.
- Generate story continuations or responses based on existing posts.
- Store and update relevant world knowledge in a knowledge graph.
- Maintain a vector database for storing textual context and references.
- Ensure proper interaction between the backend, the messaging board, and the world model.

## Features

- Real-time or interval-based post retrieval from messaging boards.
- AI-powered generation of story continuations and responses.
- Dynamic world model utilizing a Knowledge Graph (Neo4j) for structured entity and relationship storage.
- Vector Database (ChromaDB) for semantic search and textual context management.
- SQL Database (SQLAlchemy) for structured game data (character sheets, events, etc.).
- Type-safe interfaces for database interactions (Pydantic, Python dataclasses).
- Modular architecture with distinct components for data storage, retrieval, and processing.
- Includes tools for world-building: Name Generator, Map Maker, Universal Translator.

## Components

- **Messaging Board Integration**: Handles communication with the narrative gaming messaging board, retrieving posts and posting generated content.
- **Knowledge Graph**: Utilizes Neo4j to store and manage structured information about game world entities (characters, locations, events) and their relationships. See `Knowledge_Graph/README.md` for more details.
- **SQL Database**: Employs SQLAlchemy to manage structured game data such as character sheets, event logs, and location details. See `SQLdatabase/README.md` for more details.
- **Vector Database**: Uses ChromaDB to store text embeddings for semantic search, enabling context-aware text generation and retrieval. See `Vector_Database/README.md` for more details.
- **Tools**: A collection of utilities to aid in world-building and content generation:
    - *Name Generator*: Generates culturally appropriate names for characters and entities. (See `tools/name_generator/tool_overview.md` and `tools/name_generator/naming_conventions.md`)
    - *Map Maker*: Tools for managing map data. (See `tools/map_maker/tool_overview.md`)
    - *Universal Translator*: Translates text between fictional languages. (See `tools/universal_translator/tool_overview.md`)

## Getting Started

### Prerequisites

- Python 3.x

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Eno-Backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

- Configure database connections (Neo4j, SQL, ChromaDB) as per details in component READMEs and `config.json` if applicable.
- Neo4j default connection: `bolt://localhost:7687`, user: `neo4j`, password: `nasukili12`, database: `population` (can be configured in `Knowledge_Graph/graph_connector.py` and `Vector_Database/context_manager.py`).

### Basic Usage

- Explore individual components by running their respective scripts and tests (e.g., `python Knowledge_Graph/explore_graph.py --help`).
- Refer to the README files in each component directory (`Knowledge_Graph/`, `SQLdatabase/`, `Vector_Database/`) for detailed usage instructions and examples.

## Testing

The project includes tests for its core components. To run the tests, navigate to the root directory of the project and execute the following commands:
```bash
python test_knowledge_graph.py
python test_sql_database.py
python test_vector_db.py
```
Ensure that the necessary databases (Neo4j, etc.) are running and configured correctly before running the tests.
Refer to the individual test files for more details on what aspects they cover.

## Contributing

Contributions to Eno-Backend are welcome! If you'd like to contribute, please follow these general guidelines:

1. **Fork the repository.**
2. **Create a new branch** for your feature or bug fix: `git checkout -b feature-name` or `git checkout -b bugfix-name`.
3. **Make your changes** and ensure they adhere to the project's coding style.
4. **Write tests** for any new features or bug fixes.
5. **Ensure all tests pass** locally.
6. **Commit your changes** with a clear and descriptive commit message.
7. **Push your branch** to your forked repository.
8. **Open a pull request** to the main Eno-Backend repository, detailing the changes you've made.

Please also feel free to open issues for bugs, feature requests, or suggestions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.