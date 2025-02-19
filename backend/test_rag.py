from rag_pipeline import RAGPipeline

# Inisialisasi pipeline dengan jalur ke knowledge_base.json
pipeline = RAGPipeline('knowledge_base.json')

# Tes query
query = "Apa itu sistem injeksi bahan bakar?"
results = pipeline.retrieve_documents(query)

# Tampilkan hasil
print("Hasil pencarian untuk query:", query)
for doc, score in results:
    print(f"Dokumen: {doc} | Skor: {score}")
