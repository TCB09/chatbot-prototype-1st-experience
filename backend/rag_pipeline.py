from sentence_transformers import util, SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging
import PyPDF2
import torch

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeBaseRetriever:
    def __init__(self, pdf_path):
        """
        Inisialisasi retriever untuk mengambil informasi relevan dari basis pengetahuan PDF.
        """
        try:
            # Memuat knowledge base dari file PDF
            self.knowledge_base = self.load_pdf(pdf_path)
            logger.info("Knowledge base berhasil dimuat dari PDF.")
        except Exception as e:
            logger.error(f"Error saat memuat knowledge base: {e}")
            raise

    @staticmethod
    def load_pdf(pdf_path):
        """
        Membaca dan memuat konten dari file PDF.
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                knowledge_base = []

                for page in reader.pages:
                    text = page.extract_text().strip()
                    if text:
                        knowledge_base.append(text)

                return knowledge_base
        except Exception as e:
            logger.error(f"Kesalahan saat membaca PDF dari {pdf_path}: {e}")
            raise

    def retrieve(self, query, threshold=0.5):
        """
        Mencari informasi relevan dari knowledge base menggunakan kesamaan cosine.
        """
        try:
            # Inisialisasi model SentenceTransformer untuk pencarian berbasis semantik
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

            # Menghitung embedding untuk query
            query_embedding = model.encode([query], convert_to_tensor=True)

            # Menghitung similarity dengan setiap entri di knowledge base
            similarities = []
            for text in self.knowledge_base:
                text_embedding = model.encode([text], convert_to_tensor=True)
                similarity = util.pytorch_cos_sim(query_embedding, text_embedding)[0][0].item()
                similarities.append((text, similarity))

            # Urutkan berdasarkan similarity tertinggi
            similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

            # Ambil entri dengan similarity tertinggi jika lebih besar dari threshold
            if similarities and similarities[0][1] > threshold:
                return similarities[0][0]
            else:
                return None
        except Exception as e:
            logger.error(f"Kesalahan saat melakukan retrieval: {e}")
            return None


class RagPipeline:
    def __init__(self, pdf_path, generation_model_name="google/flan-t5-small"):
        """
        Inisialisasi pipeline RAG dengan retriever dan model generasi jawaban.
        """
        try:
            # Memuat retriever dari KnowledgeBaseRetriever
            self.retriever = KnowledgeBaseRetriever(pdf_path)

            # Memuat model T5 untuk generasi jawaban dan tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(generation_model_name)
            self.generation_model = AutoModelForSeq2SeqLM.from_pretrained(generation_model_name)

            logger.info("Pipeline RAG berhasil diinisialisasi.")
        except Exception as e:
            logger.error(f"Error saat inisialisasi RAG: {e}")
            raise

    def retrieve_relevant_info(self, query):
        """
        Mencari informasi relevan dari basis pengetahuan menggunakan retriever.
        """
        try:
            # Gunakan retriever untuk mendapatkan dokumen relevan
            relevant_info = self.retriever.retrieve(query)
            if not relevant_info:
                logger.warning("Tidak ada informasi relevan yang ditemukan.")
                return "Maaf, saya tidak dapat menemukan informasi yang relevan."
            logger.info("Informasi relevan ditemukan.")
            return relevant_info
        except Exception as e:
            logger.error(f"Error saat mencari informasi relevan: {e}")
            return "Maaf, saya tidak dapat menemukan informasi yang relevan."

    def generate_answer(self, question, context, max_length=150, num_beams=2):
        """
        Menghasilkan jawaban menggunakan model T5.
        """
        try:
            input_text = f"question: {question} context: {context}"
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)

            # Menghasilkan jawaban
            outputs = self.generation_model.generate(
                **inputs, max_length=max_length, num_beams=num_beams, early_stopping=True
            )
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            logger.info("Jawaban berhasil dihasilkan.")
            return answer
        except Exception as e:
            logger.error(f"Error saat menghasilkan jawaban: {e}")
            return "Terjadi kesalahan saat menghasilkan jawaban."

    def answer_question(self, query):
        """
        Menjawab pertanyaan dengan mengintegrasikan retrieval dan generation.
        """
        try:
            # Langkah 1: Cari informasi relevan
            relevant_info = self.retrieve_relevant_info(query)

            # Langkah 2: Hasilkan jawaban berdasarkan informasi relevan
            context = relevant_info if isinstance(relevant_info, str) else ""

            answer = self.generate_answer(query, context)
            return answer
        except Exception as e:
            logger.error(f"Error pada pipeline RAG: {e}")
            return "Terjadi kesalahan pada pipeline RAG."


# Contoh penggunaan untuk menguji pipeline
if __name__ == "__main__":
    pdf_path = "C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/dataset_mobil.pdf"  # Sesuaikan path PDF Anda
    pipeline = RagPipeline(pdf_path=pdf_path)
    query = "Apa yang menyebabkan lampu mobil redup?"
    answer = pipeline.answer_question(query)
    print("Jawaban:", answer)
