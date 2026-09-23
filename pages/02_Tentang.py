import streamlit as st
from modules.navigation import render_sidebar


st.set_page_config(page_title='Tentang - Riau Economic Intelligence',page_icon='ℹ️',layout='wide')
render_sidebar('tentang')
st.title('ℹ️ Tentang')
st.markdown('''
### RIAU ECONOMIC INTELLIGENCE
**Dashboard PDRB Provinsi Riau**

Aplikasi ini dirancang sebagai dashboard analitik untuk memantau perkembangan PDRB Provinsi Riau dan PDRB 12 kabupaten/kota.

**Sumber data yang digunakan pada versi awal**
- Workbook Provinsi Riau: PDRB ADHB dan ADHK menurut lapangan usaha.
- Workbook Kabupaten/Kota: PDRB ADHK dan ADHB menurut kabupaten/kota.

**Indikator**
- ADHB
- ADHK
- Pertumbuhan YoY
- Pertumbuhan QoQ
- Pertumbuhan C-to-C
- Distribusi lapangan usaha

**Peta**
Batas wilayah kabupaten/kota ditarik dari layanan geospasial Badan Informasi Geospasial (BIG) saat aplikasi berjalan.

> Catatan: aplikasi mengikuti satuan yang terdapat pada workbook sumber. Data yang tampil berasal dari file yang tersimpan di database aplikasi.
''')
