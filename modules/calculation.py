import pandas as pd
import numpy as np

QORDER={'Triwulan I':1,'Triwulan II':2,'Triwulan III':3,'Triwulan IV':4,'Tahunan':5}

def add_metrics(df):
    d=df.copy()
    d['qnum']=d['triwulan'].map(QORDER)
    d=d.sort_values(['tahun','qnum'])
    d['yoy']=np.nan
    d['qoq']=np.nan
    for (w,l),g in d.groupby(['wilayah','lapangan_usaha'],sort=False):
        qg=g[g.qnum<=4].copy().sort_values(['tahun','qnum'])
        d.loc[qg.index,'yoy']=qg['adhk'].pct_change(4)*100
        d.loc[qg.index,'qoq']=qg['adhk'].pct_change()*100
    # C-to-C: cumulative Q1..current quarter versus same cumulative period previous year.
    d['ctc']=np.nan
    for (w,l),g in d.groupby(['wilayah','lapangan_usaha'],sort=False):
        idx=g.index
        qs=g[g.qnum<=4].copy().sort_values(['tahun','qnum'])
        for _,r in qs.iterrows():
            y=int(r.tahun); q=int(r.qnum)
            cur=qs[(qs.tahun==y)&(qs.qnum<=q)].adhk.sum()
            prev=qs[(qs.tahun==y-1)&(qs.qnum<=q)].adhk.sum()
            if prev!=0 and pd.notna(prev): d.loc[r.name,'ctc']=(cur/prev-1)*100
    # Distribution: sector ADHB / PDRB total for province.
    if 'lapangan_usaha' in d:
        total=d[d.lapangan_usaha=='PDRB'][['tahun','triwulan','adhb']].rename(columns={'adhb':'total_adhb'})
        d=d.merge(total,on=['tahun','triwulan'],how='left')
        d['distribusi']=np.where((d.total_adhb.notna())&(d.total_adhb!=0),d.adhb/d.total_adhb*100,np.nan)
        # Distribution at constant 2010 prices: sector ADHK / total PDRB ADHK.
        total_k=d[d.lapangan_usaha=='PDRB'][['tahun','triwulan','adhk']].rename(columns={'adhk':'total_adhk'})
        d=d.merge(total_k,on=['tahun','triwulan'],how='left')
        d['distribusi_adhk']=np.where((d.total_adhk.notna())&(d.total_adhk!=0),d.adhk/d.total_adhk*100,np.nan)
        d=d.drop(columns=['total_adhb','total_adhk'],errors='ignore')
    return d

def latest_quarter(df):
    x=df[(df['triwulan']!='Tahunan') & df['adhk'].notna()].copy()
    if x.empty: return None
    q=x.assign(qnum=x.triwulan.map(QORDER)).sort_values(['tahun','qnum']).iloc[-1]
    return int(q.tahun), q.triwulan

def quarter_value(df,year,q,field='adhb',sector='PDRB'):
    x=df[(df.tahun==year)&(df.triwulan==q)&(df.lapangan_usaha==sector)]
    return float(x.iloc[0][field]) if not x.empty and pd.notna(x.iloc[0][field]) else np.nan
