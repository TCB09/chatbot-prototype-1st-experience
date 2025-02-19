from sentence_transformers import SentenceTransformer
import json
import logging
from faiss_index import FAISSIndexManager
from pdf_extraction import extract_paragraphs_from_pdf  # Pastikan pdf_extraction.py sudah ada

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeBaseRetriever:
    def __init__(self, pdf_path, model_name="sentence-transformers/all-MiniLM-L6-v2", faiss_index_path="faiss_index.index"):
        """
        Inisialisasi retriever dengan model SentenceTransformer dan indeks FAISS.
        """
        try:
            self.retrieval_model = SentenceTransformer(model_name)
            self.faiss_manager = FAISSIndexManager(faiss_index_path)
            self.pdf_path = pdf_path

            # Muat atau buat ulang indeks FAISS
            self.faiss_manager.load_or_create_index()
            logger.info("Retriever berhasil diinisialisasi.")
        except Exception as e:
            logger.error(f"Error saat inisialisasi retriever: {e}")
            raise

    def load_metadata(self):
        """
        Memuat metadata (paragraf) untuk referensi dari FAISS.
        """
        try:
            metadata_path = self.faiss_manager.index_path.replace('.index', '_metadata.json')
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            logger.info("Metadata berhasil dimuat.")
            return metadata
        except Exception as e:
            logger.error(f"Error saat memuat metadata: {e}")
            return []

    def retrieve(self, query, top_k=5):
        """
        Mengambil dokumen paling relevan menggunakan FAISS.
        """
        try:
            # Encode query
            query_embedding = self.retrieval_model.encode(query, convert_to_tensor=False).reshape(1, -1)

            # Pencarian di indeks FAISS
            distances, indices = self.faiss_manager.search_index(query_embedding, top_k=top_k)

            # Memuat metadata
            metadata = self.load_metadata()
            if not metadata:
                logger.warning("Metadata tidak ditemukan.")
                return "Informasi tidak tersedia."

            # Ambil dokumen berdasarkan indeks
            results = [metadata[idx] for idx in indices[0] if idx != -1]
            logger.info(f"{len(results)} dokumen relevan ditemukan.")
            return results if results else "Informasi relevan tidak ditemukan."
        except Exception as e:
            logger.error(f"Error saat mengambil dokumen relevan: {e}")
            return "Terjadi kesalahan dalam pengambilan informasi."

    def initialize_faiss_index(self):
        """
        Membuat indeks FAISS dari basis pengetahuan.
        """
        try:
            # Ekstrak paragraf dari PDF
            paragraphs = extract_paragraphs_from_pdf(self.pdf_path)

            # Encode paragraf
            embeddings = self.retrieval_model.encode(paragraphs, convert_to_tensor=False)

            # Tambahkan ke indeks FAISS
            self.faiss_manager.add_to_index(embeddings, paragraphs)
            logger.info("Indeks FAISS berhasil diinisialisasi dengan basis pengetahuan.")
        except Exception as e:
            logger.error(f"Error saat inisialisasi indeks FAISS: {e}")
            raise

# Contoh penggunaan
if __name__ == "__main__":
    # Jalur ke file PDF dan indeks FAISS
    pdf_path = "C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/FIX DATASET.pdf"  # Sesuaikan path PDF
    faiss_index_path = "C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/faiss_index.index"  # Sesuaikan path FAISS index

    # Inisialisasi retriever
    retriever = KnowledgeBaseRetriever(pdf_path=pdf_path, faiss_index_path=faiss_index_path)

    # Inisialisasi ulang FAISS (hanya dilakukan untuk data baru)
    retriever.initialize_faiss_index()

    # Uji pencarian
    query = "Apa penyebab lampu mobil redup?"
    print("Dokumen relevan:", retriever.retrieve(query))
