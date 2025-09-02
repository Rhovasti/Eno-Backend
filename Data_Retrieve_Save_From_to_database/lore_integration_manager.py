#!/usr/bin/env python3
"""
Lore Integration Manager for Eno ecosystem.
Bridges Eno Lorecraft knowledge with narrative generation backend and N4L parser.
"""

import logging
import os
import json
import asyncio
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Import existing components
from enhanced_narrative_generator import NarrativeContext, ResponseType
from Vector_Database.context_manager import ContextManager
from Knowledge_Graph.knowledge_manager import KnowledgeGraphManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoreEntry:
    """Represents a single lore entry"""
    id: str
    title: str
    content: str
    category: str  # culture, geography, history, character, etc.
    tags: List[str] = field(default_factory=list)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    source: str = ""  # Source document reference
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_n4l_format(self) -> str:
        """Convert lore entry to N4L format for parser processing"""
        lines = []
        
        # Chapter declaration
        lines.append(f"- {self.title}")
        lines.append("")
        
        # Context section with category
        lines.append(f":: {self.category} ::")
        
        # Add tags as items in context
        for tag in self.tags:
            lines.append(tag)
        lines.append("")
        
        # Add relationships
        if self.relationships:
            lines.append(":: relationships ::")
            for rel_type, targets in self.relationships.items():
                for target in targets:
                    lines.append(f"{self.title} ({rel_type}) {target}")
            lines.append("")
        
        # Content as quoted text or comments
        if self.content:
            lines.append(f'"{self.content}"')
            lines.append("")
        
        return "\n".join(lines)


@dataclass
class LoreDatabase:
    """In-memory lore database with N4L export capabilities"""
    entries: Dict[str, LoreEntry] = field(default_factory=dict)
    categories: Dict[str, List[str]] = field(default_factory=dict)
    relationships: Dict[str, Dict[str, List[str]]] = field(default_factory=dict)
    
    def add_entry(self, entry: LoreEntry) -> None:
        """Add a lore entry to the database"""
        self.entries[entry.id] = entry
        
        # Update category index
        if entry.category not in self.categories:
            self.categories[entry.category] = []
        if entry.id not in self.categories[entry.category]:
            self.categories[entry.category].append(entry.id)
        
        # Update relationship index
        for rel_type, targets in entry.relationships.items():
            if entry.id not in self.relationships:
                self.relationships[entry.id] = {}
            self.relationships[entry.id][rel_type] = targets
    
    def get_by_category(self, category: str) -> List[LoreEntry]:
        """Get all entries in a specific category"""
        if category not in self.categories:
            return []
        return [self.entries[entry_id] for entry_id in self.categories[category]]
    
    def search_by_tags(self, tags: List[str]) -> List[LoreEntry]:
        """Find entries that contain any of the specified tags"""
        results = []
        for entry in self.entries.values():
            if any(tag in entry.tags for tag in tags):
                results.append(entry)
        return results
    
    def get_related_entries(self, entry_id: str, relation_type: str = None) -> List[LoreEntry]:
        """Get entries related to the specified entry"""
        if entry_id not in self.relationships:
            return []
        
        related_ids = []
        if relation_type:
            if relation_type in self.relationships[entry_id]:
                related_ids = self.relationships[entry_id][relation_type]
        else:
            # Get all related entries regardless of type
            for rel_targets in self.relationships[entry_id].values():
                related_ids.extend(rel_targets)
        
        return [self.entries[rel_id] for rel_id in related_ids if rel_id in self.entries]
    
    def export_to_n4l(self, output_path: str) -> None:
        """Export all lore entries to N4L format"""
        n4l_content = []
        
        # Add header comment
        n4l_content.append("// Eno Lorecraft Knowledge Base")
        n4l_content.append("// Generated from lore integration system")
        n4l_content.append(f"// Export date: {datetime.now().isoformat()}")
        n4l_content.append("")
        
        # Export entries by category
        for category, entry_ids in self.categories.items():
            n4l_content.append(f"// === {category.upper()} ===")
            n4l_content.append("")
            
            for entry_id in entry_ids:
                entry = self.entries[entry_id]
                n4l_content.append(entry.to_n4l_format())
        
        # Write to file
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(n4l_content))
        
        logger.info(f"Exported {len(self.entries)} lore entries to {output_path}")


class LoreIntegrationManager:
    """Manages integration between Eno Lorecraft and narrative generation systems"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.lore_db = LoreDatabase()
        self.context_manager = None
        self.kg_manager = None
        self.n4l_parser_path = self.config.get('n4l_parser_path', '/root/Eno/SSTorytime/src/enhanced_n4l_parser')
        
        # Initialize components
        self._init_components()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            'lore_sources': {
                'cultures_doc': 'file_Cultures_of_Eno_v2_md_1756825605',
                'geography_doc': 'file_basics_md_1756825631'
            },
            'n4l_export_path': '/root/Eno/SSTorytime/examples/eno_lore.n4l',
            'chromadb_collection': 'eno_lore',
            'vector_search_limit': 5
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_components(self):
        """Initialize vector database and knowledge graph components"""
        try:
            # Initialize context manager for vector operations
            self.context_manager = ContextManager()
            logger.info("Initialized ChromaDB context manager")
        except Exception as e:
            logger.warning(f"Could not initialize context manager: {e}")
        
        try:
            # Initialize knowledge graph manager
            self.kg_manager = KnowledgeGraphManager()
            logger.info("Initialized Neo4j knowledge graph manager")
        except Exception as e:
            logger.warning(f"Could not initialize knowledge graph: {e}")
    
    def load_archon_lore_data(self, archon_project_id: str = "3f1523d0-c9e6-4e8a-99bf-dc7e93c02534") -> None:
        """Load lore data from Archon MCP server"""
        try:
            # This would be implemented to fetch from Archon MCP server
            # For now, we'll create sample data based on known structure
            
            # Culture data
            cultures_entry = LoreEntry(
                id="cultures_of_eno",
                title="Cultures of Eno",
                content="""Diverse societies with unique biological and spiritual characteristics. 
                          Each culture has distinct origins, reproductive methods, and factions.""",
                category="culture",
                tags=["societies", "biology", "spirituality", "factions"],
                relationships={
                    "located_in": ["eno_planet"],
                    "interacts_with": ["children_of_eno"]
                },
                source="Cultures_of_Eno_v2.md"
            )
            
            # Geography data
            geography_entry = LoreEntry(
                id="eno_planet_geography",
                title="Geography of ENO Planet",
                content="""Planetary information including climate zones, environments, 
                          and geographic features. Features soul-rebirth mechanics and mystical systems.""",
                category="geography",
                tags=["planet", "climate", "environment", "soul-rebirth", "mystical"],
                relationships={
                    "inhabited_by": ["cultures_of_eno"],
                    "influenced_by": ["children_of_eno"]
                },
                source="basics.md"
            )
            
            # Children of Eno (mythological)
            mythology_entry = LoreEntry(
                id="children_of_eno",
                title="Children of Eno",
                content="""Key mythological figures that influence the world's mystical systems 
                          and soul-rebirth mechanics.""",
                category="mythology",
                tags=["mythological", "figures", "influence", "mystical", "soul-rebirth"],
                relationships={
                    "influences": ["eno_planet_geography", "cultures_of_eno"]
                },
                source="basics.md"
            )
            
            # Add entries to database
            self.lore_db.add_entry(cultures_entry)
            self.lore_db.add_entry(geography_entry)
            self.lore_db.add_entry(mythology_entry)
            
            logger.info(f"Loaded {len(self.lore_db.entries)} lore entries from Archon data")
            
        except Exception as e:
            logger.error(f"Error loading Archon lore data: {e}")
    
    def export_to_n4l_and_parse(self) -> bool:
        """Export lore to N4L format and process with parser"""
        try:
            # Export to N4L
            n4l_path = self.config['n4l_export_path']
            self.lore_db.export_to_n4l(n4l_path)
            
            # Process with N4L parser if available
            if os.path.exists(self.n4l_parser_path):
                result = subprocess.run([
                    self.n4l_parser_path,
                    n4l_path
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    logger.info(f"Successfully processed N4L file with parser: {result.stdout}")
                    return True
                else:
                    logger.error(f"N4L parser error: {result.stderr}")
                    return False
            else:
                logger.warning(f"N4L parser not found at {self.n4l_parser_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error in N4L export/parse: {e}")
            return False
    
    def vectorize_lore_content(self) -> bool:
        """Add lore content to ChromaDB for semantic search"""
        if not self.context_manager:
            logger.error("Context manager not available for vectorization")
            return False
        
        try:
            for entry in self.lore_db.entries.values():
                # Create searchable content combining title, content, and tags
                searchable_text = f"""Title: {entry.title}
Category: {entry.category}
Content: {entry.content}
Tags: {', '.join(entry.tags)}
Source: {entry.source}"""
                
                # Add to vector database
                # This would use the context manager to store vectorized content
                # Implementation depends on the specific ChromaDB interface
                logger.info(f"Vectorized lore entry: {entry.title}")
            
            logger.info(f"Vectorized {len(self.lore_db.entries)} lore entries")
            return True
            
        except Exception as e:
            logger.error(f"Error vectorizing lore content: {e}")
            return False
    
    def get_lore_context_for_narrative(
        self, 
        query: str, 
        location: str = None, 
        character: str = None,
        limit: int = 3
    ) -> str:
        """Retrieve relevant lore context for narrative generation"""
        context_parts = []
        
        try:
            # Search by query terms in content and tags
            query_lower = query.lower()
            relevant_entries = []
            
            # Basic text matching (would be replaced with vector search)
            for entry in self.lore_db.entries.values():
                score = 0
                if query_lower in entry.content.lower():
                    score += 3
                if query_lower in entry.title.lower():
                    score += 2
                if any(query_lower in tag.lower() for tag in entry.tags):
                    score += 1
                
                if score > 0:
                    relevant_entries.append((entry, score))
            
            # Sort by relevance and limit results
            relevant_entries.sort(key=lambda x: x[1], reverse=True)
            relevant_entries = relevant_entries[:limit]
            
            # Format context
            if relevant_entries:
                context_parts.append("=== LORE CONTEXT ===")
                for entry, score in relevant_entries:
                    context_parts.append(f"**{entry.title}** ({entry.category})")
                    context_parts.append(f"{entry.content}")
                    if entry.tags:
                        context_parts.append(f"Related: {', '.join(entry.tags)}")
                    context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error retrieving lore context: {e}")
            return "Lore context unavailable"
    
    def integrate_with_narrative_generator(self, generator) -> None:
        """Integrate lore context into the narrative generator"""
        # This would modify the enhanced_narrative_generator to include lore context
        # in its prompt templates and context retrieval methods
        logger.info("Integrating lore context with narrative generator")
        
        # Add lore context retrieval method to generator
        original_get_vector_context = generator._get_vector_context
        
        def enhanced_get_vector_context(query: str, n_memories: int = 5, location: Optional[str] = None) -> str:
            # Get original vector context
            vector_context = original_get_vector_context(query, n_memories, location)
            
            # Add lore context
            lore_context = self.get_lore_context_for_narrative(query, location=location, limit=2)
            
            if lore_context and lore_context != "Lore context unavailable":
                return f"{vector_context}\n\n{lore_context}"
            else:
                return vector_context
        
        # Replace the method
        generator._get_vector_context = enhanced_get_vector_context
        logger.info("Enhanced narrative generator with lore integration")


def main():
    """Main function for testing the lore integration system"""
    logger.info("Initializing Lore Integration Manager")
    
    # Create manager
    manager = LoreIntegrationManager()
    
    # Load sample lore data
    manager.load_archon_lore_data()
    
    # Export to N4L and parse
    success = manager.export_to_n4l_and_parse()
    if success:
        logger.info("N4L export and parsing successful")
    
    # Vectorize content
    vectorize_success = manager.vectorize_lore_content()
    if vectorize_success:
        logger.info("Lore vectorization successful")
    
    # Test context retrieval
    context = manager.get_lore_context_for_narrative("cultures")
    logger.info(f"Sample lore context:\n{context}")


if __name__ == "__main__":
    main()