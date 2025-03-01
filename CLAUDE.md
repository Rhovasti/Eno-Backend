# Eno Backend Development Guidelines

## Setup & Commands
- Install requirements: `pip install -r requirements.txt`
- Run tests: `python -m unittest discover tests`
- Lint code: `flake8 .`
- Type checking: `mypy .`

## Code Style
- **Formatting**: Follow PEP 8 guidelines
- **Imports**: Group standard library, third-party, and local imports
- **Types**: Use type annotations from `typing` module (List, Dict, Optional, Union, etc.)
- **Dataclasses**: Use `@dataclass` for data structures
- **Error Handling**: Use try/except with specific exception types, log errors
- **Logging**: Use Python's `logging` module with appropriate levels

## Naming Conventions
- **Classes**: CamelCase (`NarrativeMemory`, `GameMetadata`)
- **Functions/Methods**: snake_case (`generate_name`, `load_naming_data`)
- **Variables**: snake_case (`master_names`, `file_path`)
- **Constants**: UPPER_SNAKE_CASE (`DATA_DIR`, `MASTER_FILE`)

## Project Structure
- Tools are organized in separate directories with `tool_overview.md` files
- Data access patterns use descriptive directory names
- Use dataclasses for structured data representation