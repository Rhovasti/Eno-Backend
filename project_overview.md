# Project Overview

## Purpose
The goal of this project is to develop a backend program that retrieves posts from a narrative gaming messaging board and generates replies or story continuations based on the content of the posts. This backend should seamlessly interact with both the frontend (messaging board) and the underlying world model, which consists of a knowledge graph and a vector database.

## Objectives
- Retrieve posts from the messaging board in real-time or at set intervals.
- Generate story continuations or responses based on existing posts.
- Store and update relevant world knowledge in a knowledge graph.
- Maintain a vector database for storing textual context and references.
- Ensure proper interaction between the backend, the messaging board, and the world model.

## Project Components

### 1. Messaging Board Integration
- Establish a connection to the messaging board.
- Retrieve user posts efficiently.
- Post AI-generated responses back to the board.

### 2. Knowledge Graph
- Represent entities (characters, locations, events) as nodes.
- Define relationships between entities as edges.
- Maintain a temporal structure to track changes over time.
- Update the graph dynamically as new posts and generated content appear.

### 3. Vector Database
- Store textual references relevant to the game world.
- Retrieve similar content for context-aware responses.
- Maintain a balance between immediate conversation and long-term world-building.

### 4. Backend System
- Process retrieved posts and analyze their content.
- Interact with both the knowledge graph and the vector database.
- Generate coherent and engaging replies.
- Optimize performance to handle multiple interactions efficiently.

## Current Progress
- Basic Python scripts for post retrieval and posting exist in the repository.
- Knowledge graph and vector database structure needs to be implemented.
- Logic for generating responses is yet to be developed.

## Next Steps
- Design API structure for backend interactions.
- Implement initial version of the knowledge graph.
- Set up vector database and integrate with retrieval logic.
- Develop a prototype for AI-generated responses.
- Test end-to-end interaction between the messaging board, backend, and world model.

## Project Management
To track goals and milestones:
- Use this document to outline features and track progress.
- Implement a task management system (e.g., GitHub Issues, Trello, or Notion).
- Define key deliverables and deadlines.

This document will be updated as the project progresses.

