document.addEventListener('DOMContentLoaded', () => {
  const slides = document.querySelectorAll('.hero-slide');
  let currentSlide = 0;
  const slideInterval = 5000; // Durasi per slide dalam ms (5 detik)

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.classList.remove('active');
      if (i === index) {
        slide.classList.add('active');
      } 
    });
  }

  function nextSlide() {
    currentSlide = (currentSlide + 1) % slides.length;
    showSlide(currentSlide);
  }

  showSlide(currentSlide); // Tampilkan slide pertama saat halaman dimuat
  setInterval(nextSlide, slideInterval); // Ganti slide setiap 5 detik
});

const aboutImage = document.querySelector('.about-image');

window.addEventListener('scroll', () => {
  const rect = aboutImage.getBoundingClientRect();
  const windowHeight = window.innerHeight;

  // Mengecek apakah gambar berada di tengah layar
  if (rect.top >= windowHeight / 3 && rect.top <= windowHeight / 1.5) {
    aboutImage.classList.add('in-view');
  } else {
    aboutImage.classList.remove('in-view');
  }
});

document.addEventListener('scroll', function() {
  const konsultasiSection = document.querySelector('.konsultasi'); // Pilih elemen .konsultasi
  const sectionPosition = konsultasiSection.getBoundingClientRect().top; // Posisi elemen dari atas layar
  const screenPosition = window.innerHeight / 1.3; // Posisi trigger

  // Jika bagian .konsultasi muncul di layar, tambahkan kelas 'show'
  if (sectionPosition < screenPosition) {
    konsultasiSection.classList.add('show');
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const services = document.querySelectorAll(".our-service-animate");

  function handleScroll() {
    services.forEach(service => {
      const rect = service.getBoundingClientRect();
      const isVisible = rect.top <= window.innerHeight - 50; // Offset untuk mengaktifkan lebih awal

      if (isVisible && !service.classList.contains("show")) {
        service.classList.add("show");
      }
    });
  }

  window.addEventListener("scroll", handleScroll);
  handleScroll(); // Memastikan cek pertama kali saat load
});

document.addEventListener("scroll", function() {
  const ourServicesSection = document.querySelector(".our-services-section"); // Ganti dengan kelas spesifik pada bagian ini
  const elements = ourServicesSection.querySelectorAll("h2, p"); // Target h2 dan p

  elements.forEach(element => {
    const elementTop = element.getBoundingClientRect().top;
    const triggerPoint = window.innerHeight / 1.3;

    if (elementTop < triggerPoint) {
      element.classList.add("fade-in", "show");
    }
  });
});

document.querySelectorAll('.service-item').forEach(item => {
  item.addEventListener('click', () => {
    toggleFlip(item);
  });
});

function toggleFlip(element) {
  element.classList.toggle('flipped');
}

document.addEventListener("DOMContentLoaded", function() {
  // Menangani klik pada tombol Chat Now
  document.querySelector(".chat-btn").addEventListener("click", function() {
    document.getElementById("chatbox").style.display = "flex";
  });

  // Menangani klik pada tombol Close di Chat Box
  document.getElementById("close-chat").addEventListener("click", function() {
    document.getElementById("chatbox").style.display = "none";
  });

  // Menangani pengiriman pesan
  document.getElementById("send-message").addEventListener("click", async function() {
    var userMessage = document.getElementById("user-input").value;
    if (userMessage.trim() !== "") {
      // Tampilkan pesan pengguna di chat
      var chatContent = document.getElementById("chat-content");
      chatContent.innerHTML += "<div><strong>You:</strong> " + userMessage + "</div>";
      document.getElementById("user-input").value = "";

      // Proses pesan dan tampilkan jawaban (contoh sistem pakar sederhana)
      setTimeout(async function() {
        var response = await getDiagnosis(userMessage);  // Mendapatkan diagnosis berdasarkan gejala
        chatContent.innerHTML += "<div><strong>System:</strong> " + response + "</div>";
        chatContent.scrollTop = chatContent.scrollHeight; // Scroll ke bawah
      }, 1000);
    }
  });
});

// Menambahkan fungsi untuk memuat file JSON
async function loadGejalaData() {
  try {
    const response = await fetch('data/data_gejala_kerusakan.json');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error loading gejala data:", error);
    return null;
  }
}

// Fungsi untuk menambah pesan ke chat
function addMessage(content, sender) {
  const messageContainer = document.createElement('div');
  messageContainer.classList.add('chat-message', sender);
  messageContainer.textContent = content;

  // Menambahkan pesan ke chat-content
  const chatContent = document.getElementById('chat-content');
  chatContent.appendChild(messageContainer);
  chatContent.scrollTop = chatContent.scrollHeight;  // Scroll otomatis ke pesan terakhir
}

// Fungsi untuk mencari diagnosis berdasarkan gejala
async function getDiagnosis(userMessage) {
  const gejalaData = await loadGejalaData();

  if (!gejalaData) {
    return "Terjadi kesalahan saat memuat data gejala.";
  }

  // Mencari kerusakan berdasarkan gejala
  const matchedKerusakan = gejalaData.gejala.find(item => userMessage.toLowerCase().includes(item.gejala.toLowerCase()));

  if (matchedKerusakan) {
    return matchedKerusakan.kerusakan;
  } else {
    return "Gejala tidak dikenali, coba lagi dengan kata kunci lain.";
  }
}

// Fungsi untuk mengirim pertanyaan ke server dan mendapatkan jawaban
async function getDiagnosis(userMessage) {
  try {
    const response = await fetch('http://127.0.0.1:5000/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question: userMessage })
    });

    const data = await response.json();
    return data.answer || "Tidak ada jawaban yang ditemukan.";
  } catch (error) {
    return "Terjadi kesalahan saat menghubungi server.";
  }
}
