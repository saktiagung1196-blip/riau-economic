# Upload ke GitHub

Di halaman **Add file → Upload files** GitHub, masukkan seluruh isi folder project ini.

Pastikan struktur repository akhirnya minimal memiliki:

```text
app.py
init_data.py
requirements.txt
modules/
pages/
assets/
database/
.streamlit/
```

Jangan meng-upload file ZIP sebagai satu-satunya file repository karena Streamlit membutuhkan file aplikasi dan dependensinya dalam struktur folder yang benar.

Setelah commit, buka Streamlit Community Cloud dan pilih repository tersebut. Main file: `app.py`.
