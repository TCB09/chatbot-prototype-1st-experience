from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer
import json
import torch
import logging
from rag_pipeline import RagPipeline  # Integrasi RAG pipeline
from faiss_index import FAISSIndexManager  # Import FAISS index manager

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QAModel:
    def __init__(self, generation_model_name, pdf_path, faiss_index_path, retrieval_model_name="sentence-transformers/all-MiniLM-L6-v2", similarity_threshold=0.5):
        """
        Inisialisasi model QA dengan model pre-trained dan knowledge base.
        """
        try:
            # Memuat model generasi jawaban dan tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(generation_model_name)
            self.generation_model = AutoModelForSeq2SeqLM.from_pretrained(generation_model_name).to(self.get_device())

            # Memuat model retrieval berbasis dense (SentenceTransformer)
            self.retrieval_model = SentenceTransformer(retrieval_model_name)

            # Inisialisasi FAISS Index Manager
            self.faiss_index_manager = FAISSIndexManager(index_path=faiss_index_path, knowledge_base_path=pdf_path)
            self.faiss_index_manager.load_or_create_index()

            # Threshold untuk kesamaan cosine
            self.similarity_threshold = similarity_threshold

            logger.info("Model QA, pipeline RAG, FAISS index, dan knowledge base berhasil diinisialisasi.")
        except Exception as e:
            logger.error(f"Kesalahan saat inisialisasi: {e}")
            raise

    @staticmethod
    def get_device():
        """
        Mendapatkan perangkat yang tersedia (GPU atau CPU).
        """
        return "cuda" if torch.cuda.is_available() else "cpu"

    def retrieve_relevant_info(self, query):
        """
        Mengambil informasi relevan dari knowledge base menggunakan FAISS index.
        """
        try:
            logger.info("Mencari informasi relevan menggunakan FAISS index...")
            faiss_results, _ = self.faiss_index_manager.search_index(query)
            if faiss_results:
                logger.info("Informasi relevan ditemukan di FAISS index.")
                return faiss_results[0]["penyebab"]
            else:
                logger.warning("Tidak ada informasi relevan ditemukan di FAISS index.")
                return "Tidak ada informasi relevan ditemukan."
        except Exception as e:
            logger.error(f"Kesalahan saat mengambil informasi relevan: {e}")
            return "Tidak ada informasi relevan ditemukan."

    def generate_answer(self, question, context):
        """
        Menghasilkan jawaban menggunakan model generasi berdasarkan konteks yang diperoleh.
        """
        try:
            input_text = f"question: {question} context: {context}"
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).to(self.get_device())

            # Menghasilkan jawaban dengan model generasi
            outputs = self.generation_model.generate(**inputs, max_length=150, num_beams=2, early_stopping=True)
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            logger.info("Jawaban berhasil dihasilkan.")
            return answer
        except Exception as e:
            logger.error(f"Kesalahan saat menghasilkan jawaban: {e}")
            return "Terjadi kesalahan saat menghasilkan jawaban."

    def answer_question(self, question):
        """
        Menjawab pertanyaan dengan mengambil konteks relevan dan menggunakan model QA.
        """
        try:
            # Mengambil informasi relevan
            relevant_info = self.retrieve_relevant_info(question)

            # Menghasilkan jawaban
            answer = self.generate_answer(question, relevant_info)

            return answer
        except Exception as e:
            logger.error(f"Kesalahan saat menjawab pertanyaan: {e}")
            return "Terjadi kesalahan dalam menjawab pertanyaan."

# Penggunaan contoh
if __name__ == "__main__":
    model = QAModel(
        generation_model_name="google/flan-t5-small",
        pdf_path="C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/penyakit_telinga.pdf",  # Sesuaikan path FIX DATASET.pdf Anda
        faiss_index_path="C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/faiss_index.index"  # Sesuaikan path FAISS index
    )
    print("Sistem pakar siap! Ajukan pertanyaan Anda.")
    while True:
        question = input("Pertanyaan: ")
        if question.lower() in ["exit", "keluar"]:
            print("Terima kasih telah menggunakan sistem pakar.")
            break
        try:
            answer = model.answer_question(question)
            print(f"Jawaban: {answer}")
        except Exception as e:
            print(f"Error: {e}")  
