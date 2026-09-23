import pandas as pd
import numpy as np
import re

QUARTERS = ['Triwulan I','Triwulan II','Triwulan III','Triwulan IV','Tahunan']

def clean_num(x):
    if x is None or (isinstance(x,float) and np.isnan(x)):
        return np.nan
    if isinstance(x,str):
        s=x.strip().replace(',','')
        if s in {'','-','–','—','na','n/a','NA'}: return np.nan
        try: return float(s)
        except: return np.nan
    try: return float(x)
    except: return np.nan

def parse_wide_sheet(path, sheet_name, kind):
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    years=[]
    current_year=None
    for j in range(1, raw.shape[1]):
        v=raw.iat[1,j]
        if pd.notna(v):
            try: current_year=int(v)
            except: pass
        years.append(current_year)
    periods=[]
    for j in range(1, raw.shape[1]):
        q=raw.iat[2,j]
        if pd.notna(q) and str(q).strip() in QUARTERS:
            periods.append((j,years[j-1],str(q).strip()))
    if kind=='province':
        rows=[]
        for i in range(3, raw.shape[0]):
            name=raw.iat[i,0]
            if pd.isna(name) or str(name).strip() in {'Catatan'}: continue
            name=str(name).strip()
            for j,year,q in periods:
                if year is None: continue
                val=clean_num(raw.iat[i,j])
                if pd.isna(val): continue
                rows.append({'wilayah':'Provinsi Riau','kode_wilayah':'1400','tahun':year,'triwulan':q,'lapangan_usaha':name,'nilai':val})
        return pd.DataFrame(rows)
    else:
        rows=[]
        for i in range(3, raw.shape[0]):
            name=raw.iat[i,0]
            if pd.isna(name) or str(name).strip() in {'Catatan'}: continue
            name=str(name).strip()
            for j,year,q in periods:
                if year is None: continue
                val=clean_num(raw.iat[i,j])
                if pd.isna(val): continue
                rows.append({'wilayah':name,'tahun':year,'triwulan':q,'nilai':val})
        return pd.DataFrame(rows)

def load_sources(province_path, kab_path):
    adhb_p=parse_wide_sheet(province_path,'Data 1','province').rename(columns={'nilai':'adhb'})
    adhk_p=parse_wide_sheet(province_path,'Data 2','province').rename(columns={'nilai':'adhk'})
    p=adhb_p.merge(adhk_p,on=['wilayah','kode_wilayah','tahun','triwulan','lapangan_usaha'],how='outer')
    # Keep official rows including totals. Sector rows are identified by letter prefix.
    p['level']='Provinsi'

    adhk_k=parse_wide_sheet(kab_path,'Data 1','kab').rename(columns={'nilai':'adhk'})
    adhb_k=parse_wide_sheet(kab_path,'Data 2','kab').rename(columns={'nilai':'adhb'})
    k=adhk_k.merge(adhb_k,on=['wilayah','tahun','triwulan'],how='outer')
    k['kode_wilayah']=k['wilayah'].map({
        'Kuantan Singingi':'1401','Indragiri Hulu':'1402','Indragiri Hilir':'1403','Pelalawan':'1404','Siak':'1405','Kampar':'1406','Rokan Hulu':'1407','Bengkalis':'1408','Rokan Hilir':'1409','Kepulauan Meranti':'1410','Pekanbaru':'1471','Dumai':'1473'})
    k['level']='Kabupaten/Kota'
    k['lapangan_usaha']='PDRB'
    return p,k

def long_to_metrics(df, value_col='adhb'):
    d=df.copy()
    d['date']=pd.to_datetime(d['tahun'].astype(str)+'-'+d['triwulan'].str.extract(r'(I|II|III|IV)')[0].map({'I':'03','II':'06','III':'09','IV':'12'}).fillna('12')+'-01')
    return d
