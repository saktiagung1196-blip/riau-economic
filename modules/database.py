import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / 'database' / 'pdrb_riau.db'
DB_PATH.parent.mkdir(exist_ok=True)

def get_conn():
    conn=sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def init_db():
    conn=get_conn()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS pdrb_provinsi (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kode_wilayah TEXT, wilayah TEXT, tahun INTEGER, triwulan TEXT,
      lapangan_usaha TEXT, adhb REAL, adhk REAL,
      UNIQUE(kode_wilayah,tahun,triwulan,lapangan_usaha)
    );
    CREATE TABLE IF NOT EXISTS pdrb_kabkot (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kode_wilayah TEXT, wilayah TEXT, tahun INTEGER, triwulan TEXT,
      adhb REAL, adhk REAL,
      UNIQUE(kode_wilayah,tahun,triwulan)
    );
    CREATE TABLE IF NOT EXISTS data_update_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT DEFAULT CURRENT_TIMESTAMP,
      jenis_data TEXT, file_name TEXT, jumlah_baris INTEGER, keterangan TEXT
    );
    ''')
    conn.commit(); conn.close()

def replace_all(prov,kab,filename='Initial source'):
    conn=get_conn()
    conn.execute('DELETE FROM pdrb_provinsi'); conn.execute('DELETE FROM pdrb_kabkot')
    prov[['kode_wilayah','wilayah','tahun','triwulan','lapangan_usaha','adhb','adhk']].to_sql('pdrb_provinsi',conn,if_exists='append',index=False)
    kab[['kode_wilayah','wilayah','tahun','triwulan','adhb','adhk']].to_sql('pdrb_kabkot',conn,if_exists='append',index=False)
    conn.execute('INSERT INTO data_update_log(jenis_data,file_name,jumlah_baris,keterangan) VALUES(?,?,?,?)',('Provinsi + Kab/Kota',filename,len(prov)+len(kab),'Data awal dari workbook BPS'))
    conn.commit(); conn.close()

def read_prov():
    conn=get_conn(); df=pd.read_sql_query('SELECT * FROM pdrb_provinsi',conn); conn.close(); return df

def read_kab():
    conn=get_conn(); df=pd.read_sql_query('SELECT * FROM pdrb_kabkot',conn); conn.close(); return df

def logs():
    conn=get_conn(); df=pd.read_sql_query('SELECT * FROM data_update_log ORDER BY id DESC',conn); conn.close(); return df
