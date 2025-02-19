import pdfplumber
import re

def extract_text_from_pdf(pdf_path):
    """
    Fungsi untuk mengekstrak teks dari file PDF dan membersihkan karakter yang tidak diinginkan.

    :param pdf_path: Path file PDF
    :return: List of dictionaries dengan struktur {'page': nomor_halaman, 'content': teks_halaman}
    """
    extracted_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Ekstrak teks dari halaman
            page_text = page.extract_text()
            
            if page_text:  # Jika halaman mengandung teks
                # Membersihkan teks dari karakter yang tidak perlu
                cleaned_text = re.sub(r'\s+', ' ', page_text).strip()
                # Menambahkan teks halaman ke dalam daftar
                extracted_pages.append({
                    "page": page_num,
                    "content": cleaned_text
                })

    return extracted_pages

def parse_extracted_text_to_knowledge_base(extracted_pages):
    """
    Memproses teks yang diekstrak dari PDF menjadi format yang dapat digunakan untuk basis pengetahuan.

    :param extracted_pages: List of dictionaries dengan struktur {'page': nomor_halaman, 'content': teks_halaman}
    :return: List of dictionaries dengan struktur basis pengetahuan {'gejala': teks, 'penyebab': teks}
    """
    knowledge_base = []
    for page in extracted_pages:
        # Split teks berdasarkan pola khusus, sesuaikan pola ini dengan struktur PDF
        lines = page["content"].split('. ')
        for line in lines:
            if ":" in line:  # Deteksi gejala dan penyebab berdasarkan pemisah ':'
                try:
                    gejala, penyebab = line.split(":", 1)
                    knowledge_base.append({
                        "gejala": gejala.strip(),
                        "penyebab": penyebab.strip()
                    })
                except ValueError:
                    # Jika format tidak sesuai, lewati
                    continue
    return knowledge_base

# Contoh penggunaan
if __name__ == "__main__":
    pdf_path = "path/to/your/pdf_file.pdf"  # Ganti dengan path file PDF
    extracted_pages = extract_text_from_pdf(pdf_path)
    knowledge_base = parse_extracted_text_to_knowledge_base(extracted_pages)
    
    # Menampilkan hasil
    print(knowledge_base)
