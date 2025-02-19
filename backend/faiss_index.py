import faiss
import numpy as np
import json
import os
import logging
from transformers import AutoTokenizer, AutoModel
import torch
from PyPDF2 import PdfReader

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FAISSIndexManager:
    def __init__(self, index_path, knowledge_base_path, embedding_dim=384, model_name="sentence-transformers/all-MiniLM-L6-v2", device=None):
        self.index_path = index_path
        self.knowledge_base_path = knowledge_base_path
        self.embedding_dim = embedding_dim
        self.index = None
        self.device = device if device else "cuda" if torch.cuda.is_available() else "cpu"

        # Load model and tokenizer for embedding generation
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)

    def load_knowledge_base_from_pdf(self):
        """
        Load knowledge base from a PDF file.

        :return: List of knowledge base entries
        """
        if not os.path.exists(self.knowledge_base_path):
            raise FileNotFoundError(f"PDF file not found at {self.knowledge_base_path}")

        knowledge_base = []
        reader = PdfReader(self.knowledge_base_path)

        for page in reader.pages:
            text = page.extract_text()
            if text:
                entries = self.parse_pdf_text(text)
                knowledge_base.extend(entries)

        if not knowledge_base:
            logger.warning("No valid entries found in the PDF file.")
        else:
            logger.info(f"Knowledge base loaded from PDF at {self.knowledge_base_path}. {len(knowledge_base)} entries found.")
        
        return knowledge_base

    @staticmethod
    def parse_pdf_text(text):
        """
        Parse text from PDF into knowledge base entries.

        :param text: Raw text from PDF
        :return: List of parsed entries
        """
        entries = []
        lines = text.split("\n")
        for line in lines:
            parts = line.split(":")  # Assuming format "gejala:penyebab"
            if len(parts) == 2:
                gejala, penyebab = parts[0].strip(), parts[1].strip()
                if gejala and penyebab:
                    entries.append({"gejala": gejala, "penyebab": penyebab})
        return entries

    def load_or_create_index(self):
        """
        Load existing FAISS index or create a new one if it doesn't exist.
        """
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            logger.info(f"FAISS index loaded from {self.index_path}.")
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info("New FAISS index created.")

    def add_to_index(self):
        """
        Add entries from knowledge base to the FAISS index.
        """
        knowledge_base = self.load_knowledge_base_from_pdf()
        if not knowledge_base:
            logger.error("No entries to add to the index.")
            return

        texts = [entry['gejala'] for entry in knowledge_base]
        metadata = knowledge_base

        embeddings = self.generate_embeddings(texts)
        self.index.add(embeddings)
        logger.info(f"Added {len(texts)} entries to the index.")

        # Save metadata
        metadata_path = self.index_path.replace('.index', '_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
        else:
            existing_metadata = []

        existing_metadata.extend(metadata)

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(existing_metadata, f, ensure_ascii=False, indent=4)
        logger.info(f"Metadata saved to {metadata_path}.")

    def generate_embeddings(self, texts):
        """
        Generate embeddings for the provided texts using the model.

        :param texts: List of texts to generate embeddings for
        :return: numpy array of embeddings
        """
        inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        return embeddings

    def search_index(self, query_text, top_k=5):
        """
        Search the FAISS index for the most similar texts based on a query.

        :param query_text: Text to search for in the index
        :param top_k: Number of nearest neighbors to return
        :return: List of results and distances
        """
        query_embedding = self.generate_embeddings([query_text])
        distances, indices = self.index.search(query_embedding, top_k)

        # Load metadata
        metadata_path = self.index_path.replace('.index', '_metadata.json')
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found at {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        results = []
        for idx in indices[0]:
            if idx < len(metadata):
                result = metadata[idx]
                results.append({
                    "gejala": result["gejala"],
                    "penyebab": result["penyebab"]
                })
            else:
                logger.warning(f"Index {idx} out of metadata range.")

        return results, distances[0]

    def save_index(self):
        """
        Save the FAISS index to disk.
        """
        if self.index is None:
            raise ValueError("Index has not been created or loaded.")
        faiss.write_index(self.index, self.index_path)
        logger.info(f"Index saved to {self.index_path}.")

    def load_metadata(self):
        """
        Load metadata from the corresponding metadata file.

        :return: List of metadata
        """
        metadata_path = self.index_path.replace('.index', '_metadata.json')
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata file {metadata_path} does not exist.")
            return []

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        logger.info(f"Metadata loaded from {metadata_path}.")
        return metadata
