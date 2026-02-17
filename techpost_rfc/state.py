from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TOCItem(BaseModel):
    """Represents a single topic/chapter in the series."""
    topic: str = Field(description="The title of the topic or chapter.")
    summary: str = Field(description="A brief summary of what this chapter covers.")
    relevant_sections: List[str] = Field(description="List of section titles or numbers from the original document relevant to this topic.")

class GeneratedPost(BaseModel):
    """Represents a generated blog post."""
    title: str = Field(description="Title of the blog post.")
    draft: str = Field(description="The markdown content of the blog post draft.")
    demo_ideas: str = Field(description="Ideas for demos, code snippets, or diagrams.")

class GraphState(TypedDict):
    """
    Represents the state of the graph.

    Attributes:
        document_content: The full text content of the loaded document.
        document_metadata: Metadata associated with the document.
        series_toc: List of TOC items for the blog series.
        current_index: The index of the current topic being processed.
        generated_posts: List of generated blog posts.
    """
    document_content: str
    document_metadata: Dict[str, Any]
    series_toc: List[dict] # Storing as dicts for easier serialization, or List[TOCItem]
    current_index: int
    generated_posts: List[dict] # Storing as dicts or List[GeneratedPost]
    current_draft: Optional[str]
    current_demo_ideas: Optional[str]
