import pandas as pd
import numpy as np
from pathlib import Path

SECTOR_ORDER = [
    'A. Pertanian, Kehutanan, dan Perikanan','B. Pertambangan dan Penggalian','C. Industri Pengolahan',
    'D. Pengadaan Listrik dan Gas','E. Pengadaan Air, Pengelolaan Sampah, Limbah dan Daur Ulang',
    'F. Konstruksi','G. Perdagangan Besar dan Eceran; Reparasi Mobil dan Sepeda Motor',
    'H. Transportasi dan Pergudangan','I. Penyediaan Akomodasi dan Makan Minum','J. Informasi dan Komunikasi',
    'K. Jasa Keuangan dan Asuransi','L. Real Estate','M, N. Jasa Perusahaan',
    'O. Administrasi Pemerintahan, Pertahanan dan Jaminan Sosial Wajib','P. Jasa Pendidikan',
    'Q. Jasa Kesehatan dan Kegiatan Sosial','R, S, T, U. Jasa lainnya']

QNUM={'Triwulan I':1,'Triwulan II':2,'Triwulan III':3,'Triwulan IV':4}

def _clean_sector(s):
    s=str(s).strip()
    s=s.replace('M,N.','M, N.').replace('R,S,T,U.','R, S, T, U.')
    import re
    s=re.sub(r'^\d+\.\s*','',s)
    # Workbook kab/kota uses numbered categories; map them to canonical 17-sector labels.
    return s

def _quarter_prev(year, q):
    n=QNUM[q]
    return (year-1, 'Triwulan IV') if n==1 else (year, f'Triwulan {['I','II','III','IV'][n-2]}')

def _canonical_sector(s):
    s=_clean_sector(s)
    aliases={
        'Pertanian. Kehutanan. dan Perikanan':'A. Pertanian, Kehutanan, dan Perikanan',
        'Pertanian, Kehutanan, dan Perikanan':'A. Pertanian, Kehutanan, dan Perikanan',
        'Real Estate':'L. Real Estate',
        'Real Estat':'L. Real Estate',
    }
    if s in aliases:
        return aliases[s]
    for item in SECTOR_ORDER:
        if s == item or s == item.split('. ',1)[-1]:
            return item
    return s

def province_source_growth(prov, year, q, mode='Y-on-Y'):
    d=prov.copy()
    d['tahun']=pd.to_numeric(d['tahun'],errors='coerce')
    d['adhk']=pd.to_numeric(d['adhk'],errors='coerce')
    d['lapangan_usaha']=d['lapangan_usaha'].map(_canonical_sector)
    sectors=d[~d.lapangan_usaha.isin(['PDRB','PDRB Tanpa Migas']) & d.lapangan_usaha.str.match(r'^[A-R]',na=False)].copy()
    sectors=sectors[sectors.lapangan_usaha.isin(SECTOR_ORDER)]
    if mode=='Q-to-Q':
        py,pq=_quarter_prev(int(year),q)
        cur=sectors[(sectors.tahun==year)&(sectors.triwulan==q)][['lapangan_usaha','adhk']].rename(columns={'adhk':'cur'})
        prv=sectors[(sectors.tahun==py)&(sectors.triwulan==pq)][['lapangan_usaha','adhk']].rename(columns={'adhk':'prev'})
        total_prev=d[(d.tahun==py)&(d.triwulan==pq)&(d.lapangan_usaha=='PDRB')]['adhk']
        denom=float(total_prev.iloc[0]) if len(total_prev) and pd.notna(total_prev.iloc[0]) else np.nan
    elif mode=='Y-on-Y':
        cur=sectors[(sectors.tahun==year)&(sectors.triwulan==q)][['lapangan_usaha','adhk']].rename(columns={'adhk':'cur'})
        prv=sectors[(sectors.tahun==year-1)&(sectors.triwulan==q)][['lapangan_usaha','adhk']].rename(columns={'adhk':'prev'})
        total_prev=d[(d.tahun==year-1)&(d.triwulan==q)&(d.lapangan_usaha=='PDRB')]['adhk']
        denom=float(total_prev.iloc[0]) if len(total_prev) and pd.notna(total_prev.iloc[0]) else np.nan
    else: # C-to-C
        n=QNUM[q]
        cur=sectors[(sectors.tahun==year)&(sectors.triwulan.isin([f'Triwulan {x}' for x in ['I','II','III','IV'][:n]]))].groupby('lapangan_usaha',as_index=False)['adhk'].sum().rename(columns={'adhk':'cur'})
        prv=sectors[(sectors.tahun==year-1)&(sectors.triwulan.isin([f'Triwulan {x}' for x in ['I','II','III','IV'][:n]]))].groupby('lapangan_usaha',as_index=False)['adhk'].sum().rename(columns={'adhk':'prev'})
        total_prev=sectors[(sectors.tahun==year-1)&(sectors.triwulan.isin([f'Triwulan {x}' for x in ['I','II','III','IV'][:n]]))].groupby('triwulan')['adhk'].sum().sum()
        denom=float(total_prev) if pd.notna(total_prev) else np.nan
    out=cur.merge(prv,on='lapangan_usaha',how='left')
    out['source_growth']=(out['cur']-out['prev'])/denom*100 if denom and not np.isnan(denom) else np.nan
    out['urutan']=out.lapangan_usaha.map({s:i for i,s in enumerate(SECTOR_ORDER)})
    return out.sort_values('urutan').reset_index(drop=True)

def _find_table_start(df, title):
    for i in range(len(df)):
        val=str(df.iloc[i,0]).strip() if pd.notna(df.iloc[i,0]) else ''
        if title.lower() in val.lower():
            return i
    return None

def kab_source_growth(workbook_path, wilayah, year, q, mode='Y-on-Y'):
    if int(year)!=2026:
        return pd.DataFrame(columns=['lapangan_usaha','source_growth','urutan'])
    sh=str(wilayah).strip().upper()
    try:
        raw=pd.read_excel(workbook_path,sheet_name=sh,header=None)
    except Exception:
        return pd.DataFrame(columns=['lapangan_usaha','source_growth','urutan'])
    title={'Q-to-Q':'Sumber Pertumbuhan (Q-to-Q)','Y-on-Y':'Sumber Pertumbuhan (Y-on-Y)','C-to-C':'Sumber Pertumbuhan (C-to-C)'}[mode]
    start=_find_table_start(raw,title)
    if start is None:
        return pd.DataFrame(columns=['lapangan_usaha','source_growth','urutan'])
    header=start+1
    cols=raw.iloc[header].tolist()
    target=f'{int(year)}Q{QNUM[q]}'
    idx=None
    for j,c in enumerate(cols):
        if str(c).strip()==target:
            idx=j; break
    if idx is None:
        return pd.DataFrame(columns=['lapangan_usaha','source_growth','urutan'])
    rows=raw.iloc[header+1:header+19,[0,idx]].copy()
    rows.columns=['lapangan_usaha','source_growth']
    rows['lapangan_usaha']=rows.lapangan_usaha.map(_canonical_sector)
    rows['source_growth']=pd.to_numeric(rows.source_growth,errors='coerce')
    rows=rows[rows.lapangan_usaha.isin(SECTOR_ORDER)].copy()
    rows['urutan']=rows.lapangan_usaha.map({s:i for i,s in enumerate(SECTOR_ORDER)})
    return rows.sort_values('urutan').reset_index(drop=True)


def kab_category_metric(workbook_path, wilayah, year, q, metric):
    """Read official 2026 category-level metrics from the BPS recap workbook.
    metric: distribusi_adhb, distribusi_adhk, qoq, yoy, ctc
    """
    if int(year) != 2026:
        return pd.DataFrame(columns=['lapangan_usaha','nilai','urutan'])
    table_map = {
        'distribusi_adhb': 'Distribusi PDRB ADHB Menurut Lapangan Usaha',
        'distribusi_adhk': 'Distribusi PDRB ADHK Menurut Lapangan Usaha',
        'qoq': 'Pertumbuhan PDRB (Q-TO-Q)',
        'yoy': 'Pertumbuhan PDRB (Y-ON-Y)',
        'ctc': 'Pertumbuhan PDRB (C-TO-C)',
    }
    title = table_map.get(metric)
    if not title:
        return pd.DataFrame(columns=['lapangan_usaha','nilai','urutan'])
    try:
        raw=pd.read_excel(workbook_path,sheet_name=str(wilayah).strip().upper(),header=None)
    except Exception:
        return pd.DataFrame(columns=['lapangan_usaha','nilai','urutan'])
    start=_find_table_start(raw,title)
    if start is None:
        return pd.DataFrame(columns=['lapangan_usaha','nilai','urutan'])
    header=start+1
    cols=raw.iloc[header].tolist()
    target=f'{int(year)}Q{QNUM[q]}'
    idx=next((j for j,c in enumerate(cols) if str(c).strip()==target),None)
    if idx is None:
        return pd.DataFrame(columns=['lapangan_usaha','nilai','urutan'])
    rows=raw.iloc[header+1:header+18,[0,idx]].copy()
    rows.columns=['lapangan_usaha','nilai']
    rows['lapangan_usaha']=rows.lapangan_usaha.map(_canonical_sector)
    rows['nilai']=pd.to_numeric(rows.nilai,errors='coerce')
    rows=rows[rows.lapangan_usaha.isin(SECTOR_ORDER)].copy()
    rows['urutan']=rows.lapangan_usaha.map({x:i for i,x in enumerate(SECTOR_ORDER)})
    return rows.sort_values('urutan').reset_index(drop=True)


def kab_total_metric(workbook_path, wilayah, year, q, metric):
    """Read official total PDRB/growth for one kabupaten/kota from the BPS recap workbook.
    For 2026, use Tables 3.1–3.5 directly so comparison values match the official recap.
    """
    if int(year) != 2026:
        return np.nan
    table_map = {
        'adhb': 'Tabel 3.1. PDRB ADHB Menurut Lapangan Usaha',
        'adhk': 'Tabel 3.2. PDRB ADHK Menurut Lapangan Usaha',
        'qoq': 'Tabel 3.3. Pertumbuhan PDRB (Q-TO-Q)',
        'yoy': 'Tabel 3.4. Pertumbuhan PDRB (Y-ON-Y)',
        'ctc': 'Tabel 3.5. Pertumbuhan PDRB (C-TO-C)',
    }
    title = table_map.get(metric)
    if not title:
        return np.nan
    try:
        raw = pd.read_excel(workbook_path, sheet_name=str(wilayah).strip().upper(), header=None)
    except Exception:
        return np.nan
    start = _find_table_start(raw, title)
    if start is None:
        return np.nan
    header = start + 1
    cols = raw.iloc[header].tolist()
    target = f'{int(year)}Q{QNUM[q]}'
    idx = next((j for j, c in enumerate(cols) if str(c).strip() == target), None)
    if idx is None:
        return np.nan
    # The total row is the row labelled P D R B in Tables 3.1–3.5.
    for r in range(header + 1, min(header + 22, len(raw))):
        label = str(raw.iloc[r, 0]).strip().replace(' ', '')
        if label.upper() in ('PDRB', 'PDRB.'): 
            value = pd.to_numeric(raw.iloc[r, idx], errors='coerce')
            return float(value) if pd.notna(value) else np.nan
    return np.nan
