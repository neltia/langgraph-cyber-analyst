from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


class VectorEngine:
    def __init__(self, db_path="./db"):
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.db_path = db_path

    def build_db(self, refined_data):
        docs = []
        for d in refined_data:
            page_text = f"{d['content']}\nDetection Guide: {d['detection']}"

            doc = Document(
                page_content=page_text,
                metadata={
                    "tid": d['id'],
                    "tactic": str(d['tactics']),
                    "is_sub": d['is_sub']
                }
            )
            docs.append(doc)

        return Chroma.from_documents(docs, self.embeddings, persist_directory=self.db_path)

    def get_db(self):
        return Chroma(persist_directory=self.db_path, embedding_function=self.embeddings)
