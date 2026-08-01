import streamlit as st
import json
from github import Github
from openai import OpenAI

st.set_page_config(page_title="Sınırsız YZ", page_icon="🧠")

# GitHub ve OpenAI Şifrelerini Streamlit'ten çekiyoruz
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"] # Örn: yusuf/sinirsiz-yz
except:
    st.error("Lütfen API anahtarlarını Streamlit ayarlarına ekleyin.")
    st.stop()

# Bağlantıları Kur
client = OpenAI(api_key=OPENAI_API_KEY)
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# GitHub'daki Kalıcı Hafızayı Oku
hafiza_dosyasi = repo.get_contents("hafiza.json")
hafiza_icerik = json.loads(hafiza_dosyasi.decoded_content.decode('utf-8'))

st.title("🧠 Sınırsız Yapay Zeka")
st.write("Bana görev ver, soru sor veya yeni bir şey öğret. Öğrendiklerimi hafızama kaydederim!")

# Sohbet geçmişini ekranda tutma
if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

# Kullanıcıdan mesaj alma
user_input = st.chat_input("Mesajınızı buraya yazın...")

if user_input:
    # Kullanıcının mesajını ekrana yaz
    st.session_state.mesajlar.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Yapay Zekanın Beyin Yapısı ve Görevi
    sistem_mesaji = f"""
    Sen her şeyi yapabilen, öğrenebilen otonom bir yapay zekasın. 
    Kalıcı Hafızan (Geçmişte öğrendiklerin ve kuralların): {json.dumps(hafiza_icerik, ensure_ascii=False)}
    
    Kullanıcının mesajına en iyi şekilde cevap ver. 
    ÖNEMLİ KURAL: Eğer kullanıcı sana YENİ, KALICI bir bilgi öğretiyorsa, kendisiyle ilgili bir detay veriyorsa veya gelecekte hatırlaman gereken bir kural koyuyorsa bunu 'yeni_bilgi' kısmına yaz. Sadece normal bir sohbet ediyorsa 'yeni_bilgi' kısmını BOŞ BIRAK.
    
    YANITINI KESİNLİKLE AŞAĞIDAKİ JSON FORMATINDA VER:
    {{
        "cevap": "Kullanıcıya vereceğin samimi ve detaylı yanıt",
        "yeni_bilgi": "Öğrendiğin yeni bilgi cümlesi (yoksa boş bırak)"
    }}
    """

    # Yapay Zekayı Çalıştır
    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            cevap_raw = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": sistem_mesaji}] + st.session_state.mesajlar,
                response_format={ "type": "json_object" } # Sadece JSON üretmeye zorlar
            )
            
            # Yanıtı parçala
            sonuc = json.loads(cevap_raw.choices[0].message.content)
            yz_cevabi = sonuc.get("cevap", "Bir hata oluştu.")
            yeni_ogrenilen = sonuc.get("yeni_bilgi", "")

            # Cevabı ekrana yazdır
            st.markdown(yz_cevabi)
            st.session_state.mesajlar.append({"role": "assistant", "content": yz_cevabi})

            # EĞER YENİ BİR ŞEY ÖĞRENDİYSE GITHUB'A (HAFIZASINA) KAYDET
            if yeni_ogrenilen and yeni_ogrenilen.strip() != "":
                hafiza_icerik.append(yeni_ogrenilen)
                guncel_hafiza = json.dumps(hafiza_icerik, ensure_ascii=False, indent=2)
                
                # GitHub'daki dosyayı günceller
                repo.update_file(
                    hafiza_dosyasi.path,
                    f"Otomatik Hafıza Kaydı: {yeni_ogrenilen[:20]}...",
                    guncel_hafiza,
                    hafiza_dosyasi.sha
                )
                st.success(f"💾 **Yeni bilgi kalıcı hafızama kaydedildi:** {yeni_ogrenilen}")
