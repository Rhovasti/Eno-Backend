#!/usr/bin/env python3
"""
API endpoints for Eno Lore Integration.
Provides REST endpoints for accessing integrated lore data in narrative generation.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json

from lore_integration_manager import LoreIntegrationManager, LoreEntry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Eno Lore Integration API", version="1.0.0")

# Global lore manager instance
lore_manager = None


class LoreContextRequest(BaseModel):
    """Request model for lore context retrieval"""
    query: str
    location: Optional[str] = None
    character: Optional[str] = None
    limit: int = 3
    include_relationships: bool = True


class LoreContextResponse(BaseModel):
    """Response model for lore context"""
    success: bool
    context: str
    entries: List[Dict[str, Any]]
    total_found: int
    error: Optional[str] = None


class LoreEntryResponse(BaseModel):
    """Response model for individual lore entry"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    relationships: Dict[str, List[str]]
    source: str
    n4l_format: str


class LoreStatusResponse(BaseModel):
    """Response model for lore system status"""
    success: bool
    total_entries: int
    categories: Dict[str, int]
    n4l_parser_available: bool
    vector_db_available: bool
    knowledge_graph_available: bool
    last_update: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize lore manager on startup"""
    global lore_manager
    try:
        logger.info("Initializing Lore Integration Manager...")
        lore_manager = LoreIntegrationManager()
        lore_manager.load_archon_lore_data()
        
        # Try to export and parse N4L data
        lore_manager.export_to_n4l_and_parse()
        
        # Try to vectorize lore content
        lore_manager.vectorize_lore_content()
        
        logger.info(f"Lore system initialized with {len(lore_manager.lore_db.entries)} entries")
    except Exception as e:
        logger.error(f"Failed to initialize lore manager: {e}")
        # Continue without lore manager - API will return appropriate errors


@app.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint"""
    return {
        "service": "Eno Lore Integration API",
        "version": "1.0.0",
        "status": "active" if lore_manager else "unavailable"
    }


@app.get("/status", response_model=LoreStatusResponse)
async def get_status():
    """Get lore system status"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    # Count entries by category
    categories = {}
    for entry in lore_manager.lore_db.entries.values():
        categories[entry.category] = categories.get(entry.category, 0) + 1
    
    return LoreStatusResponse(
        success=True,
        total_entries=len(lore_manager.lore_db.entries),
        categories=categories,
        n4l_parser_available=lore_manager.n4l_parser_path and 
                            lore_manager.n4l_parser_path.exists() if hasattr(lore_manager.n4l_parser_path, 'exists') else False,
        vector_db_available=lore_manager.context_manager is not None,
        knowledge_graph_available=lore_manager.kg_manager is not None
    )


@app.post("/lore/context", response_model=LoreContextResponse)
async def get_lore_context(request: LoreContextRequest):
    """Retrieve lore context for narrative generation"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    try:
        # Get lore context
        context = lore_manager.get_lore_context_for_narrative(
            query=request.query,
            location=request.location,
            character=request.character,
            limit=request.limit
        )
        
        # Get individual entries for detailed response
        entries = []
        query_lower = request.query.lower()
        
        for entry in lore_manager.lore_db.entries.values():
            # Simple relevance scoring
            score = 0
            if query_lower in entry.content.lower():
                score += 3
            if query_lower in entry.title.lower():
                score += 2
            if any(query_lower in tag.lower() for tag in entry.tags):
                score += 1
            
            if score > 0:
                entry_dict = {
                    "id": entry.id,
                    "title": entry.title,
                    "content": entry.content[:500] + "..." if len(entry.content) > 500 else entry.content,
                    "category": entry.category,
                    "tags": entry.tags,
                    "relevance_score": score,
                    "relationships": entry.relationships if request.include_relationships else {}
                }
                entries.append(entry_dict)
        
        # Sort by relevance and limit
        entries.sort(key=lambda x: x["relevance_score"], reverse=True)
        entries = entries[:request.limit]
        
        return LoreContextResponse(
            success=True,
            context=context,
            entries=entries,
            total_found=len(entries)
        )
    
    except Exception as e:
        logger.error(f"Error retrieving lore context: {e}")
        return LoreContextResponse(
            success=False,
            context="",
            entries=[],
            total_found=0,
            error=str(e)
        )


@app.get("/lore/entry/{entry_id}", response_model=LoreEntryResponse)
async def get_lore_entry(entry_id: str):
    """Get detailed information about a specific lore entry"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    if entry_id not in lore_manager.lore_db.entries:
        raise HTTPException(status_code=404, detail="Lore entry not found")
    
    entry = lore_manager.lore_db.entries[entry_id]
    
    return LoreEntryResponse(
        id=entry.id,
        title=entry.title,
        content=entry.content,
        category=entry.category,
        tags=entry.tags,
        relationships=entry.relationships,
        source=entry.source,
        n4l_format=entry.to_n4l_format()
    )


@app.get("/lore/categories")
async def get_categories():
    """Get all available lore categories"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    categories = {}
    for entry in lore_manager.lore_db.entries.values():
        if entry.category not in categories:
            categories[entry.category] = []
        categories[entry.category].append({
            "id": entry.id,
            "title": entry.title,
            "tags": entry.tags
        })
    
    return {
        "categories": categories,
        "total_categories": len(categories),
        "total_entries": len(lore_manager.lore_db.entries)
    }


@app.get("/lore/search")
async def search_lore(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    limit: int = Query(10, description="Maximum results")
):
    """Search lore entries by query, category, or tags"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    results = []
    query_lower = q.lower()
    filter_tags = [tag.strip().lower() for tag in tags.split(",")] if tags else []
    
    for entry in lore_manager.lore_db.entries.values():
        # Apply filters
        if category and entry.category.lower() != category.lower():
            continue
        
        if filter_tags and not any(tag in [t.lower() for t in entry.tags] for tag in filter_tags):
            continue
        
        # Calculate relevance score
        score = 0
        if query_lower in entry.content.lower():
            score += 3
        if query_lower in entry.title.lower():
            score += 5
        if any(query_lower in tag.lower() for tag in entry.tags):
            score += 2
        
        if score > 0:
            results.append({
                "id": entry.id,
                "title": entry.title,
                "content": entry.content[:300] + "..." if len(entry.content) > 300 else entry.content,
                "category": entry.category,
                "tags": entry.tags,
                "score": score
            })
    
    # Sort by relevance and limit
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:limit]
    
    return {
        "results": results,
        "total_found": len(results),
        "query": q,
        "filters": {
            "category": category,
            "tags": filter_tags
        }
    }


@app.post("/lore/export/n4l")
async def export_n4l():
    """Export lore database to N4L format"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    try:
        success = lore_manager.export_to_n4l_and_parse()
        
        return {
            "success": success,
            "export_path": lore_manager.config['n4l_export_path'],
            "total_entries": len(lore_manager.lore_db.entries),
            "message": "N4L export completed successfully" if success else "N4L export completed with warnings"
        }
    
    except Exception as e:
        logger.error(f"Error exporting N4L: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/lore/vectorize")
async def vectorize_lore():
    """Vectorize lore content for semantic search"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    try:
        success = lore_manager.vectorize_lore_content()
        
        return {
            "success": success,
            "total_entries": len(lore_manager.lore_db.entries),
            "vector_db_available": lore_manager.context_manager is not None,
            "message": "Vectorization completed successfully" if success else "Vectorization completed with warnings"
        }
    
    except Exception as e:
        logger.error(f"Error vectorizing lore: {e}")
        raise HTTPException(status_code=500, detail=f"Vectorization failed: {str(e)}")


# Integration endpoint for narrative generator
@app.post("/narrative/context")
async def get_narrative_context(
    query: str,
    location: Optional[str] = None,
    character: Optional[str] = None,
    include_vector_context: bool = True,
    include_knowledge_graph: bool = True,
    include_lore_context: bool = True
):
    """Get comprehensive context for narrative generation including lore"""
    if not lore_manager:
        raise HTTPException(status_code=503, detail="Lore manager not available")
    
    context_parts = []
    
    try:
        # Get lore context
        if include_lore_context:
            lore_context = lore_manager.get_lore_context_for_narrative(
                query=query,
                location=location,
                character=character,
                limit=3
            )
            if lore_context and lore_context != "Lore context unavailable":
                context_parts.append(lore_context)
        
        # Get vector context (if available)
        if include_vector_context and lore_manager.context_manager:
            try:
                vector_context = lore_manager.context_manager.get_context_for_query(
                    query=query,
                    location_name=location,
                    n_memories=5
                )
                if vector_context:
                    context_parts.append("=== VECTOR MEMORY CONTEXT ===")
                    context_parts.append(vector_context.to_text())
            except:
                pass
        
        # Get knowledge graph context (if available)
        if include_knowledge_graph and lore_manager.kg_manager:
            try:
                # This would integrate with the knowledge graph
                context_parts.append("=== KNOWLEDGE GRAPH CONTEXT ===")
                context_parts.append("Knowledge graph integration active")
            except:
                pass
        
        full_context = "\n\n".join(context_parts)
        
        return {
            "success": True,
            "context": full_context,
            "components": {
                "lore": include_lore_context,
                "vector": include_vector_context and lore_manager.context_manager is not None,
                "knowledge_graph": include_knowledge_graph and lore_manager.kg_manager is not None
            },
            "query": query,
            "location": location,
            "character": character
        }
    
    except Exception as e:
        logger.error(f"Error getting narrative context: {e}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)