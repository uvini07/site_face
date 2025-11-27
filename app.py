import streamlit as st
from pymongo import MongoClient
import gridfs
from PIL import Image
import io
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.transform import resize
import time

# === CONFIGURAÇÃO ===
st.set_page_config(page_title="🖼 Visual Compare", layout="wide")

st.markdown(
    """
    <div style="background-color:#6C63FF; padding:15px; border-radius:10px;">
    <h1 style="color:white; text-align:center;">🖼 Visual Comparator</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# === CSS COM TOP E LEFT EDITÁVEIS ===
st.markdown("""
<style>

/* Centraliza a área da câmera */
.camera-center {
    width: 100%;
    display: flex;
    justify-content: center;
    margin-top: 10px;
}

/* Caixa da câmera */
.camera-box {
    position: relative;
    width: 520px; 
    max-width: 95vw;
}

.user-frame {
    position: absolute;
    top: 190px;     /* Ajuste como quiser */
    left: 75px;    /* Ajuste como quiser */

    width: 70%;
    height: auto;

    pointer-events: none;
    z-index: 10;
}

.user-frame svg {
    width: 100%;
    height: auto;
    opacity: 0.9;
    stroke: #00FFAA;
    stroke-width: 5;
    fill: transparent;
    filter: drop-shadow(0px 0px 8px #00FFAA);
}

</style>
""", unsafe_allow_html=True)

# === MENU ===
st.sidebar.header("📌 Selecione o método de envio")
metodo = st.sidebar.radio("Escolha a forma de enviar sua imagem:",
                          options=["📹 Capturar com Câmera", "🗂 Carregar do dispositivo"])

user_image = None
cam_input = None
upload_input = None

# === CÂMERA COM OVERLAY AJUSTÁVEL ===
if metodo == "📹 Capturar com Câmera":
    st.markdown("### 📸 Capture sua foto:")

    st.markdown("""
    <div class="camera-center">
        <div class="camera-box">
            <div class="user-frame">
                <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="30" r="18"></circle>
                    <path d="M20 85 Q50 60 80 85" />
                </svg>
            </div>
    """, unsafe_allow_html=True)

    cam_input = st.camera_input("")

    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)

    if cam_input:
        user_image = Image.open(cam_input).convert("L")

else:
    upload_input = st.file_uploader("Escolher arquivo", type=['jpg', 'jpeg', 'png'])
    if upload_input:
        user_image = Image.open(upload_input).convert("L")

# === VERIFICAÇÃO ===
if user_image is None:
    st.warning("⚠️ Nenhuma imagem selecionada.")
    st.stop()

st.image(user_image, width=300)
arr_user = np.array(user_image)

# === BANCO DE DADOS ===
uri = "mongodb+srv://marcelinhojordao07_db_user:XSMudvXzW9T1aAf1@cluster15.bxyzonr.mongodb.net/?appName=Cluster15"
client = MongoClient(uri)
db = client["midias"]
fs = gridfs.GridFS(db)

arquivos = list(fs.find())
if not arquivos:
    st.error("⚠️ Nenhuma imagem na base.")
    st.stop()

results = []

for arquivo in arquivos:
    dados = fs.get(arquivo._id).read()
    db_image = Image.open(io.BytesIO(dados)).convert("L")

    if db_image.size != user_image.size:
        db_image = db_image.resize(user_image.size)

    arr_db = np.array(db_image)
    similarity = ssim(arr_user, arr_db, data_range=arr_db.max() - arr_db.min())

    results.append((arquivo.filename, db_image, similarity))

results.sort(key=lambda x: x[2], reverse=True)

most_similar = results[0]
least_similar = results[-1]

col1, col2 = st.columns(2)

with col1:
    st.subheader("✔ Mais semelhante")
    st.image(most_similar[1], use_column_width=True)

with col2:
    st.subheader("❌ Menos semelhante")
    st.image(least_similar[1], use_column_width=True)

# === SALVAR ===
if st.button("Salvar no banco"):
    img_bytes = cam_input.getvalue() if cam_input else upload_input.getvalue()
    filename = f"user_upload_{int(time.time())}.jpg"
    fs.put(img_bytes, filename=filename)
    st.success("Imagem salva com sucesso!")