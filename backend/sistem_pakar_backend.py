from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer, util
import logging
from rag_pipeline import RagPipeline  # Untuk pipeline RAG
from qa_model import QAModel  # Impor model QA dari qa_model.py
from pdf_extraction import extract_text_from_pdf  # Untuk ekstraksi PDF

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inisialisasi aplikasi Flask
app = Flask(__name__)



# Menambahkan CORS untuk mengizinkan permintaan dari frontend
CORS(app)

# Konfigurasi file dan model
generation_model_name = "google/flan-t5-small"
pdf_path = "C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/penyakit_telinga.pdf"  # Lokasi PDF
faiss_index_path = "C:/Users/thejo/OneDrive/Desktop/sistem_pakar_baru/backend/faiss_index"  # Lokasi FAISS Index

# Inisialisasi RagPipeline
rag_pipeline = RagPipeline(pdf_path=pdf_path)

# Inisialisasi model QA
qa_model = QAModel(
    generation_model_name=generation_model_name,
    pdf_path=pdf_path,
    faiss_index_path=faiss_index_path
)

# Inisialisasi model embedding
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Fungsi untuk memuat dan memproses basis pengetahuan dari PDF
def preprocess_knowledge_base():
    try:
        text = extract_text_from_pdf(pdf_path)
        logger.info("Teks PDF berhasil diekstraksi.")
        
        knowledge_base = []
        for entry in text:
            gejala = entry.get("gejala", "").strip()
            penyebab = entry.get("penyebab", "").strip()
            solusi = entry.get("solusi", "").strip()
            
            if gejala:
                embedding = embedding_model.encode(gejala, convert_to_tensor=True)
                knowledge_base.append({
                    "gejala": gejala,
                    "penyebab": penyebab,
                    "solusi": solusi,
                    "embedding": embedding
                })
        logger.info("Knowledge base berhasil diproses dengan embedding.")
        return knowledge_base
    except Exception as e:
        logger.error(f"Error memproses knowledge base: {e}")
        return []

# Memuat basis pengetahuan
knowledge_base = preprocess_knowledge_base()

# Fungsi untuk pencarian jawaban dari knowledge base
def get_answer_from_knowledge_base(query):
    try:
        query_embedding = embedding_model.encode(query, convert_to_tensor=True)
        max_similarity = 0
        best_match = None

        for entry in knowledge_base:
            similarity = util.pytorch_cos_sim(query_embedding, entry['embedding'])[0][0].item()
            if similarity > 0.8 and similarity > max_similarity:  # Threshold relevansi
                max_similarity = similarity
                best_match = entry

        if best_match:
            return {
                "gejala": best_match['gejala'],
                "penyebab": best_match['penyebab'],
                "solusi": best_match.get('solusi', 'Solusi tidak tersedia')
            }
        return None
    except Exception as e:
        logger.error(f"Error mencari di knowledge base: {e}")
        return None

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()  # Mengambil data JSON dari request
        if not isinstance(data, dict):
            return jsonify({'error': 'Data yang diterima bukan format JSON yang valid.'}), 400

        query = data.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Query tidak boleh kosong.'}), 400

        logger.info(f"Query diterima: {query}")

        # Mencari jawaban dari knowledge base
        kb_answer = get_answer_from_knowledge_base(query)

        if kb_answer:
            return jsonify({
                'answer': f"<b>Gejala:</b> {kb_answer['gejala']}<br>"
                          f"<b>Penyebab:</b> {kb_answer['penyebab']}<br>"
                          f"<b>Solusi:</b> {kb_answer['solusi']}<br>",
                'follow_up': "Apakah jawaban ini memadai? 😊"
            })
        else:
            # Jika tidak ada jawaban dari knowledge base, fallback ke RAG atau QA model
            logger.info("Tidak ada jawaban dari knowledge base, menggunakan RAG pipeline.")
            rag_answer = rag_pipeline.retrieve_relevant_info(query)
            if rag_answer:
                return jsonify({
                    'answer': f"<b>Informasi Relevan:</b> {rag_answer}<br>",
                    'follow_up': "Apakah jawaban ini memadai? 😊"
                })

            logger.info("Fallback ke QA model.")
            qa_answer = qa_model.answer_question(query)
            return jsonify({'answer': qa_answer, 'follow_up': "Apakah jawaban ini memadai? 😊"})

    except Exception as e:
        logger.error(f"Error pada endpoint /ask: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/rag', methods=['POST'])
def rag_query():
    try:
        data = request.json  # Mengambil data JSON dari request
        if not isinstance(data, dict):
            return jsonify({'error': 'Data yang diterima bukan format JSON yang valid.'}), 400

        question = data.get('question', '')
        if not question:
            return jsonify({'error': 'Pertanyaan tidak boleh kosong'}), 400

        answer = rag_pipeline.answer_question(question)
        return jsonify({'question': question, 'answer': answer})
    except Exception as e:
        logger.error(f"Error pada endpoint /rag: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug', methods=['GET'])
def debug():
    try:
        logger.info("Endpoint debug diakses.")
        return jsonify({'status': 'Sistem berjalan dengan baik.', 'model': generation_model_name})
    except Exception as e:
        logger.error(f"Error pada endpoint /debug: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Sistem pakar backend berjalan pada mode debug.")
    app.run(host='0.0.0.0', port=5000, debug=True)
