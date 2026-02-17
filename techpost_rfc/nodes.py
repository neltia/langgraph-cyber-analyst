import os
import logging
from langchain_community.document_loaders import UnstructuredMarkdownLoader, PyPDFLoader, TextLoader
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from datetime import datetime
from typing import List
from pydantic import BaseModel

from state import GraphState, TOCItem, GeneratedPost
from llm import get_llm

logger = logging.getLogger(__name__)


# --- Node: load_document ---
def load_document(state: GraphState) -> GraphState:
    """
    Loads the document from the file path provided in the state (or via some other mechanism, 
    but for now let's assume valid file path is passed in or we use a hardcoded one for testing, 
    actually user input will likely be injected into state before start).
    
    Wait, the initial state won't have the file path unless we put it in metadata or something.
    The main.py will handle injecting the file path.
    Let's assume state['document_metadata']['file_path'] holds the path.
    """
    file_path = state["document_metadata"].get("file_path")
    
    logger.info(f"Loading document from: {file_path}")
    
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".md":
        # Fallback to TextLoader to avoid 'unstructured' dependency issues on Windows
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        loader = TextLoader(file_path, encoding="utf-8") # Default to text

    docs = loader.load()
    content = "\n\n".join([d.page_content for d in docs])
    
    logger.info(f"Document loaded successfully. Length: {len(content)} chars.")
    
    return {"document_content": content}


# --- Node: extract_toc ---
class SeriesTOC(TOCItem):
    # This might not be right, we need a container.
    pass


class TOCContainer(BaseModel):
    items: List[TOCItem]


def extract_toc(state: GraphState) -> GraphState:
    """
    Extracts the Table of Contents (TOC) from the document.
    """
    logger.info("Extracting Table of Contents (TOC)...")
    
    # Use ollama by default as requested by user context
    llm = get_llm(model_type="ollama", model_name="qwen2.5-coder-14b-instruct") 
    
    parser = JsonOutputParser(pydantic_object=TOCContainer)
    
    system_prompt = """당신은 테크니컬 라이터입니다. 
    주어진 기술/표준 문서를 분석하여, 독자가 이해하기 쉬운 블로그 연재 시리즈 목차를 JSON 형태로 추출하세요.
    전체 문서를 논리적인 흐름(챕터/토픽 단위)으로 분해해야 합니다.
    
    반드시 다음 JSON 포맷을 따르세요:
    {format_instructions}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Document Content:\n{document_content}")
    ])
    
    chain = prompt | llm | parser

    result = chain.invoke({
        "document_content": state['document_content'][:50000],
        "format_instructions": parser.get_format_instructions()
    })
    
    # result should be a dict matching TOCContainer or just the dict itself if parser is loose
    # If using Pydantic parser, it returns a dict.
    # TOCContainer has 'items' which is a list of TOCItem
    
    if "items" in result:
        toc_list = result["items"]
    else:
        # Fallback if parser returns list directly
        toc_list = result if isinstance(result, list) else []

    logger.info(f"TOC extracted with {len(toc_list)} items.")

    return {"series_toc": toc_list, "current_index": 0, "generated_posts": []}


# --- Node: generate_draft ---
def generate_draft(state: GraphState) -> GraphState:
    """
    Generates a blog post draft for the current topic.
    """
    current_index = state["current_index"]
    toc_item = state["series_toc"][current_index]
    
    # We might want to retrieve relevant chunks here if the document is huge, 
    # but for MVP we putting the whole content in context (up to limit).
    # Ideally, we should use RAG or just the relevant sections if we had parsed them.
    # For now, let's just pass the whole document content (truncated if needed).
    
    llm = get_llm(model_type="ollama", model_name="qwen2.5-coder-14b-instruct")
    
    logger.info(f"Generating draft for topic: {toc_item['topic']}")

    # Rest of the function...
    template = """당신은 전문 기술 블로거입니다. 
    다음 문서를 바탕으로, 아래 주제에 대한 블로그 포스트 초안을 작성해 주세요.
    
    주제: {topic}
    요약: {summary}
    관련 섹션: {relevant_sections}
    
    문서 내용:
    {document_content}
    
    작성 가이드:
    - 독자가 이해하기 쉽게 설명하세요.
    - 마크다운 포맷으로 작성하세요.
    - 서론, 본론, 결론 구조를 갖추세요.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "topic": toc_item["topic"],
        "summary": toc_item["summary"],
        "relevant_sections": ", ".join(toc_item["relevant_sections"]),
        "document_content": state["document_content"][:50000] # Simple truncation
    })
    
    # We store the draft temporarily in the state or pass it to the next node?
    # The graph definition says generate_draft -> generate_demo_ideas -> aggregate_post.
    # So we can just return it to update the state, but we need a place to hold it temporarily.
    # Let's add a temporary key to the state or just update 'generated_posts' partially?
    # Better to have a 'current_draft' key in state, but GraphState definition needs to support it.
    # AGENTS.md says "Agent C Output: 임시 변수 current_draft 반환".
    # So we should add 'current_draft' to GraphState or just return it as a dict and let LangGraph merge it.
    # LangGraph merges outputs into state. So if we return {"current_draft": ...}, it will be in state.
    # But we need to declare it in GraphState if we use TypedDict.
    # Let's assume we can add it or we should update GraphState.
    
    return {"current_draft": response.content}


# --- Node: generate_demo_ideas ---
def generate_demo_ideas(state: GraphState) -> GraphState:
    """
    Generates demo ideas based on the draft and topic.
    """
    current_index = state["current_index"]
    toc_item = state["series_toc"][current_index]
    current_draft = state.get("current_draft", "")
    
    llm = get_llm(model_type="ollama", model_name="qwen2.5-coder-14b-instruct")
    
    logger.info(f"Generating demo ideas for topic: {toc_item['topic']}")
    
    template = """당신은 테크니컬 에반젤리스트입니다.
    작성된 블로그 포스트 초안을 읽고, 독자의 이해를 돕기 위한 실습 코드, 데모 아이디어, 또는 다이어그램(Mermaid)을 제안하세요.
    
    주제: {topic}
    
    초안 내용:
    {current_draft}
    
    제안할 내용:
    - 실습 가능한 코드 스니펫 (Python, Bash 등)
    - Mermaid 다이어그램 코드
    - Docker Compose 설정 등
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "topic": toc_item["topic"],
        "current_draft": current_draft
    })
    
    return {"current_demo_ideas": response.content}


# --- Node: aggregate_post ---
def aggregate_post(state: GraphState) -> GraphState:
    """
    Aggregates the draft and demo ideas into a GeneratedPost and updates the list.
    Increments the current_index.
    """
    current_index = state["current_index"]
    toc_item = state["series_toc"][current_index]
    current_draft = state.get("current_draft", "")
    current_demo_ideas = state.get("current_demo_ideas", "")
    
    new_post = {
        "title": toc_item["topic"],
        "draft": current_draft,
        "demo_ideas": current_demo_ideas
    }
    
    # We need to append to the list. 
    # In LangGraph, if we return {"generated_posts": [new_post]}, it might OVERWRITE if not using a reducer.
    # Standard TypedDict state in LangGraph replaces keys. 
    # To append, we should retrieve the old list and append.
    
    existing_posts = state.get("generated_posts", [])
    updated_posts = existing_posts + [new_post]
    
    logger.info(f"Aggregated post {current_index + 1}/{len(state['series_toc'])}: {new_post['title']}")
    
    return {
        "generated_posts": updated_posts,
        "current_index": current_index + 1,
        # Clear temporary state if needed, though not strictly necessary if overwritten next time
        "current_draft": None,
        "current_demo_ideas": None
    }
