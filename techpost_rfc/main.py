import os
import sys
import argparse
import logging
from graph import get_graph
from state import GraphState

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("techpost_rfc")

def main():
    parser = argparse.ArgumentParser(description="techpost_rfc: Convert technical docs to blog posts.")
    parser.add_argument("file_path", nargs="?", help="Path to the technical document.")
    args = parser.parse_args()
    
    file_path = args.file_path
    if not file_path:
        # Fallback to interactive input if no arg provided
        file_path = input("Enter the path to the document: ").strip()
    
    if not os.path.exists(file_path):
        logger.error(f"Error: File not found at {file_path}")
        sys.exit(1)
        
    logger.info(f"Processing document: {file_path}")
    logger.info("Initializing workflow...")
    
    app = get_graph()
    
    initial_state = {
        "document_metadata": {"file_path": file_path},
        "series_toc": [],
        "current_index": 0,
        "generated_posts": [],
        "document_content": "" # Will be loaded by load_document
    }
    
    logger.info("Starting workflow execution...")
    
    final_state = None
    logger.info("Starting workflow execution...")
    
    final_state = app.invoke(initial_state)
    
    generated_posts = final_state.get("generated_posts", [])
    logger.info(f"Successfully generated {len(generated_posts)} posts.")
    
    # Save results
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    for i, post in enumerate(generated_posts):
        title = post.get("title", f"Post_{i+1}")
        safe_title = "".join([c if c.isalnum() else "_" for c in title])
        filename = f"{i+1:02d}_{safe_title}.md"
        filepath = os.path.join(output_dir, filename)
        
        content = f"# {title}\n\n"
        content += post.get("draft", "")
        content += "\n\n## Demo & Implementation Ideas\n\n"
        content += post.get("demo_ideas", "")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Saved: {filepath}")

if __name__ == "__main__":
    main()
