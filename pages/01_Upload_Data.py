import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
from modules.parser import load_sources
from modules.database import init_db,replace_all,read_prov,read_kab,logs

from modules.navigation import render_sidebar


st.set_page_config(page_title='Upload Data - Riau Economic Intelligence',page_icon='🔄',layout='wide')
render_sidebar('upload')
init_db()
st.title('🔄 Upload Data')
st.caption('Upload workbook mengikuti format sumber BPS yang digunakan saat ini. Sistem membaca sheet Data 1 dan Data 2 secara otomatis.')

st.info('Format yang didukung pada versi ini: **provinsi riau.xlsx** untuk data Provinsi Riau dan **data per kab kot.xlsx** untuk 12 kabupaten/kota. Struktur tahun + Triwulan I–IV + Tahunan dipertahankan.')

f1=st.file_uploader('Upload file Provinsi Riau (.xlsx)',type=['xlsx'],key='prov')
f2=st.file_uploader('Upload file Kabupaten/Kota (.xlsx)',type=['xlsx'],key='kab')

if f1 or f2:
    st.markdown('### Preview file')
    for f in [f1,f2]:
        if f:
            x=pd.ExcelFile(f); st.write(f'**{f.name}** — sheet: {", ".join(x.sheet_names)}')
            for sh in x.sheet_names:
                df=pd.read_excel(f,sheet_name=sh,header=None,nrows=7)
                st.write(f'**{sh}**'); st.dataframe(df,hide_index=True,use_container_width=True)

if st.button('💾 Simpan / Update Data',type='primary',use_container_width=False):
    if not (f1 and f2):
        st.error('Untuk menjaga konsistensi dashboard, upload kedua file sekaligus: Provinsi Riau dan Kabupaten/Kota.')
    else:
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'provinsi.xlsx'; k=Path(td)/'kabkot.xlsx'; p.write_bytes(f1.getvalue()); k.write_bytes(f2.getvalue())
            try:
                prov,kab=load_sources(str(p),str(k))
                replace_all(prov,kab,f'{f1.name} + {f2.name}')
                st.success(f'Data berhasil diperbarui: {len(prov):,} baris provinsi dan {len(kab):,} baris kabupaten/kota.')
                st.rerun()
            except Exception as e:
                st.error(f'Gagal membaca file: {e}')

st.markdown('### Status data saat ini')
prov=read_prov(); kab=read_kab()
a,b,c=st.columns(3); a.metric('Baris Provinsi',f'{len(prov):,}'); b.metric('Baris Kab/Kota',f'{len(kab):,}'); c.metric('Wilayah Kab/Kota',f'{kab.wilayah.nunique():,}')

st.markdown('### Riwayat Update')
st.dataframe(logs(),hide_index=True,use_container_width=True)
