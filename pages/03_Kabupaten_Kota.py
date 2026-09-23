import json
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
from modules.database import init_db, read_prov, read_kab
from modules.formatting import rupiah_juta, pct
from modules.source_growth import kab_source_growth, kab_category_metric, kab_total_metric
from modules.navigation import render_sidebar

st.set_page_config(page_title="Kabupaten/Kota - RIAU ECONOMIC ANALYTICS", page_icon="📍", layout="wide", initial_sidebar_state="expanded")
init_db()

st.markdown("""
<style>
[data-testid="stSidebar"]{background:linear-gradient(180deg,#29245f 0%,#403080 100%)}
[data-testid="stSidebar"] *{color:white!important}
.block-container{padding-top:1.1rem;padding-bottom:2rem;max-width:1500px}
.hero{background:linear-gradient(100deg,#fbfbff,#f3efff);border:1px solid #e3dcfb;border-radius:20px;padding:18px 24px;margin-bottom:14px;box-shadow:0 5px 18px rgba(50,40,120,.06)}
.hero h1{margin:0;color:#132f78;font-size:30px}.hero p{margin:5px 0 0;color:#687a94}
.filter-card,.card{background:#fff;border:1px solid #e4e8f5;border-radius:16px;padding:15px 17px;box-shadow:0 5px 18px rgba(30,40,100,.05);height:100%}
.kpi-title{font-size:12px;color:#6e7c92}.kpi-value{font-size:25px;font-weight:800;color:#132f78;margin-top:5px}.kpi-sub{font-size:11px;color:#8190a5;margin-top:4px}
.section-title{font-size:18px;font-weight:800;color:#132f78;margin:5px 0 8px}.muted{font-size:12px;color:#73839a}
.rank-card{background:linear-gradient(110deg,#fbf9ff,#f5f0ff);border:1px solid #e3dcfb;border-radius:16px;padding:16px}
.footer{border-top:1px solid #e4e8f5;padding-top:12px;margin-top:18px;color:#6f7f96;font-size:12px}
</style>
""", unsafe_allow_html=True)

render_sidebar('kabupaten')

# Workbook rekap BPS untuk data kategori dan Source of Growth kabupaten/kota.
# Diletakkan di root aplikasi/source_data agar dapat ditemukan baik saat lokal maupun deploy.
workbook_path = str(Path(__file__).resolve().parents[1] / 'source_data' / 'Rekap PDRB lapangan usaha (1).xlsx')

# Data kabupaten/kota pada workbook BPS menggunakan satuan Miliar Rupiah.
def format_pdrb_kab(x):
    try:
        x=float(x)
        if abs(x) >= 1000:
            return f'Rp {x/1000:.2f} T'
        return f'Rp {x:.2f} Miliar'
    except Exception:
        return '-'

prov=read_prov(); kab=read_kab()
for df in [prov,kab]:
    df['tahun']=pd.to_numeric(df['tahun'],errors='coerce')
    df['adhb']=pd.to_numeric(df['adhb'],errors='coerce')
    df['adhk']=pd.to_numeric(df['adhk'],errors='coerce')

qorder={'Triwulan I':1,'Triwulan II':2,'Triwulan III':3,'Triwulan IV':4}
periods=kab[kab.triwulan!='Tahunan'][['tahun','triwulan']].drop_duplicates().dropna()
periods['qnum']=periods.triwulan.map(qorder); periods=periods.sort_values(['tahun','qnum'])
years=sorted(periods.tahun.astype(int).unique(),reverse=True)

st.markdown('<div class="hero"><h1>📍 Kabupaten/Kota</h1><p>Jelajahi indikator PDRB setiap kabupaten/kota di Provinsi Riau secara lebih rinci, termasuk Source of Growth.</p></div>',unsafe_allow_html=True)

f1,f2,f3=st.columns([1.5,.8,.9],gap='small')
with f1: wilayah=st.selectbox('Kabupaten/Kota',sorted(kab.wilayah.dropna().astype(str).str.strip().unique()),index=sorted(kab.wilayah.dropna().astype(str).str.strip().unique()).index('Pekanbaru') if 'Pekanbaru' in sorted(kab.wilayah.dropna().astype(str).str.strip().unique()) else 0)
with f2: year=st.selectbox('Tahun',years,index=0)
qs=periods.loc[periods.tahun.astype(int)==year,'triwulan'].tolist()
with f3: q=st.selectbox('Triwulan',qs,index=len(qs)-1)

sel=kab[(kab.tahun==year)&(kab.triwulan==q)&(kab.wilayah.astype(str).str.strip()==wilayah)].copy()
if sel.empty:
    st.warning('Data periode/wilayah yang dipilih belum tersedia.'); st.stop()
row=sel.iloc[0]
prev=kab[(kab.tahun==year-1)&(kab.triwulan==q)&(kab.wilayah.astype(str).str.strip()==wilayah)]
yoy=((float(row.adhk)/float(prev.iloc[0].adhk))-1)*100 if not prev.empty and pd.notna(prev.iloc[0].adhk) and prev.iloc[0].adhk!=0 and pd.notna(row.adhk) else np.nan
allsel=kab[(kab.tahun==year)&(kab.triwulan==q)].copy(); allsel['wilayah']=allsel.wilayah.astype(str).str.strip()
total_adhb=allsel.adhb.sum(min_count=1); contrib=(float(row.adhb)/total_adhb*100) if pd.notna(total_adhb) and total_adhb else np.nan
ranked=allsel.sort_values('adhk',ascending=False).reset_index(drop=True); rank=(ranked.index[ranked.wilayah==wilayah][0]+1) if (ranked.wilayah==wilayah).any() else np.nan

info=st.columns(4,gap='small')
for c,label,value in [(info[0],'Kabupaten/Kota',wilayah),(info[1],'Tahun',year),(info[2],'Triwulan',q),(info[3],'Periode aktif',f'{q} {year}')]:
    with c: st.markdown(f'<div class="filter-card"><div class="muted">{label}</div><div style="font-size:18px;font-weight:800;color:#132f78;margin-top:6px">{value}</div></div>',unsafe_allow_html=True)

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
st.markdown(f'<div class="section-title">Ringkasan Ekonomi</div><div class="muted">PDRB {wilayah}, {q} {year}</div>',unsafe_allow_html=True)
k1,k2,k3,k4=st.columns(4,gap='small')
with k1: st.markdown(f'<div class="card" style="border-top:4px solid #2F80ED"><div class="kpi-title">PDRB ADHB</div><div class="kpi-value">{format_pdrb_kab(row.adhb)}</div><div class="kpi-sub">Harga berlaku</div></div>',unsafe_allow_html=True)
with k2: st.markdown(f'<div class="card" style="border-top:4px solid #16A36A"><div class="kpi-title">PDRB ADHK 2010</div><div class="kpi-value">{format_pdrb_kab(row.adhk)}</div><div class="kpi-sub">Harga konstan 2010</div></div>',unsafe_allow_html=True)
with k3: st.markdown(f'<div class="card" style="border-top:4px solid #F29B38"><div class="kpi-title">Pertumbuhan Ekonomi (YoY)</div><div class="kpi-value">{pct(yoy)}</div><div class="kpi-sub">Triwulan yang sama tahun sebelumnya</div></div>',unsafe_allow_html=True)
with k4: st.markdown(f'<div class="card" style="border-top:4px solid #7656D6"><div class="kpi-title">Kontribusi terhadap Total Kab/Kota</div><div class="kpi-value">{pct(contrib)}</div><div class="kpi-sub">PDRB ADHB terhadap total 12 kabupaten/kota</div></div>',unsafe_allow_html=True)

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
left,right=st.columns([1.25,1],gap='large')
with left:
    st.markdown(f'<div class="section-title">Perkembangan PDRB {wilayah}</div><div class="muted">Pilih indikator untuk melihat perkembangan ekonomi</div>',unsafe_allow_html=True)
    metric_tabs=st.tabs(['ADHB','ADHK','YoY','QoQ','C-to-C'])
    hist=kab[(kab.wilayah.astype(str).str.strip()==wilayah)&(kab.triwulan!='Tahunan')].copy(); hist['qnum']=hist.triwulan.map(qorder); hist=hist.sort_values(['tahun','qnum']); hist['periode']=hist.apply(lambda r:f"{int(r.tahun)} {r.triwulan.replace('Triwulan ','TW ')}",axis=1)
    hist['yoy']=hist['adhk'].pct_change(4)*100
    hist['qoq']=hist['adhk'].pct_change(1)*100
    # Untuk Q1, QoQ dibandingkan Q4 tahun sebelumnya secara eksplisit.
    hist['prev_year']=hist['tahun']-1
    hist['prev_q4_adhk']=hist.apply(lambda r: kab[(kab.wilayah.astype(str).str.strip()==wilayah)&(kab.tahun==r['prev_year'])&(kab.triwulan=='Triwulan IV')]['adhk'].iloc[0] if r['qnum']==1 and not kab[(kab.wilayah.astype(str).str.strip()==wilayah)&(kab.tahun==r['prev_year'])&(kab.triwulan=='Triwulan IV')].empty else np.nan,axis=1)
    hist.loc[hist['qnum']==1,'qoq']=((hist.loc[hist['qnum']==1,'adhk']/hist.loc[hist['qnum']==1,'prev_q4_adhk'])-1)*100
    hist['ctc']=np.nan
    for yy in sorted(hist.tahun.dropna().unique()):
        for qn in range(1,5):
            mask=(hist.tahun==yy)&(hist.qnum==qn)
            if mask.any():
                cur=hist.loc[(hist.tahun==yy)&(hist.qnum<=qn),'adhk'].sum()
                prv=hist.loc[(hist.tahun==yy-1)&(hist.qnum<=qn),'adhk'].sum()
                if pd.notna(prv) and prv!=0: hist.loc[mask,'ctc']=(cur/prv-1)*100
    metric_defs=[('ADHB','adhb','Triliun Rupiah'),('ADHK','adhk','Triliun Rupiah'),('YoY','yoy','Persen'),('QoQ','qoq','Persen'),('C-to-C','ctc','Persen')]
    for tab,(label,col,ytitle) in zip(metric_tabs,metric_defs):
        with tab:
            plot=hist[['periode',col]].dropna().copy()
            if col in ['adhb','adhk']:
                plot[col]=plot[col]/1000.0  # Miliar Rp -> Triliun Rp
            fig=px.line(plot,x='periode',y=col,markers=True)
            fig.update_layout(height=350,margin=dict(l=10,r=10,t=10,b=50),paper_bgcolor='white',plot_bgcolor='white',xaxis_title=None,yaxis_title=ytitle,showlegend=False)
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
with right:
    st.markdown(f'<div class="section-title">Pertumbuhan Ekonomi (YoY)</div><div class="muted">{wilayah} vs Provinsi Riau</div>',unsafe_allow_html=True)
    h=hist.copy()
    p=prov[(prov.lapangan_usaha=='PDRB')&(prov.triwulan!='Tahunan')].copy(); p['qnum']=p.triwulan.map(qorder); p=p.sort_values(['tahun','qnum']); p['yoy_prov']=p.adhk.pct_change(4)*100
    h=h.merge(p[['tahun','triwulan','yoy_prov']],on=['tahun','triwulan'],how='left')
    long=pd.concat([h[['periode','yoy']].assign(seri=wilayah).rename(columns={'yoy':'nilai'}),h[['periode','yoy_prov']].assign(seri='Provinsi Riau').rename(columns={'yoy_prov':'nilai'})])
    fig2=px.line(long,x='periode',y='nilai',color='seri',markers=True); fig2.update_layout(height=350,margin=dict(l=10,r=10,t=10,b=50),paper_bgcolor='white',plot_bgcolor='white',xaxis_title=None,yaxis_title='Persen')
    st.plotly_chart(fig2,use_container_width=True,config={'displayModeBar':False})

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)

# Analisis lapangan usaha: Distribusi → Pertumbuhan → Source of Growth dalam satu baris.
# Data kategori 2026 dibaca langsung dari workbook rekap BPS.
cat1, cat2, cat3 = st.columns(3, gap='large')
with cat1:
    st.markdown('<div class="section-title">Distribusi Menurut Lapangan Usaha</div><div class="muted">Kontribusi kategori terhadap PDRB · 2026</div>', unsafe_allow_html=True)
    dist_tabs = st.tabs(['ADHB','ADHK'])
    for tab, metric, label in zip(dist_tabs, ['distribusi_adhb','distribusi_adhk'], ['Distribusi ADHB','Distribusi ADHK']):
        with tab:
            dcat = kab_category_metric(workbook_path, wilayah, int(year), q, metric)
            if dcat.empty:
                st.info(f'{label} belum tersedia untuk {wilayah} pada {q} {year}.')
            else:
                figd = px.bar(dcat, x='nilai', y='lapangan_usaha', orientation='h', text='nilai')
                figd.update_traces(texttemplate='%{text:.2f}%', textposition='outside', cliponaxis=False)
                figd.update_layout(height=520, margin=dict(l=5,r=45,t=8,b=28), xaxis_title='Persen', yaxis_title=None, showlegend=False); figd.update_yaxes(categoryorder='array', categoryarray=list(reversed(dcat['lapangan_usaha'].tolist())))
                st.plotly_chart(figd, use_container_width=True, config={'displayModeBar':False})

with cat2:
    st.markdown('<div class="section-title">Pertumbuhan Lapangan Usaha</div><div class="muted">Pertumbuhan kategori · 2026</div>', unsafe_allow_html=True)
    growth_tabs = st.tabs(['YoY','QoQ','C-to-C'])
    for tab, metric, label in zip(growth_tabs, ['yoy','qoq','ctc'], ['YoY','QoQ','C-to-C']):
        with tab:
            gcat = kab_category_metric(workbook_path, wilayah, int(year), q, metric)
            if gcat.empty:
                st.info(f'Pertumbuhan {label} belum tersedia untuk {wilayah} pada {q} {year}.')
            else:
                figg = px.bar(gcat, x='nilai', y='lapangan_usaha', orientation='h', text='nilai')
                figg.update_traces(texttemplate='%{text:.2f}%', textposition='outside', cliponaxis=False)
                figg.update_layout(height=520, margin=dict(l=5,r=45,t=8,b=28), xaxis_title='Persen', yaxis_title=None, showlegend=False); figg.update_yaxes(categoryorder='array', categoryarray=list(reversed(gcat['lapangan_usaha'].tolist())))
                st.plotly_chart(figg, use_container_width=True, config={'displayModeBar':False})

with cat3:
    st.markdown('<div class="section-title">Source of Growth</div><div class="muted">Kontribusi kategori terhadap pertumbuhan · 2026</div>', unsafe_allow_html=True)
    sog_tabs = st.tabs(['Y-on-Y','Q-to-Q','C-to-C'])
    for tab, mode in zip(sog_tabs, ['Y-on-Y','Q-to-Q','C-to-C']):
        with tab:
            sog = kab_source_growth(workbook_path, wilayah, int(year), q, mode)
            if sog.empty:
                st.info(f'Source of Growth {mode} belum tersedia untuk {wilayah} pada {q} {year}.')
            else:
                figs = sog.copy()
                figs['source_growth']=pd.to_numeric(figs['source_growth'],errors='coerce')
                figs=figs.dropna(subset=['source_growth'])
                figs['lapangan_usaha']=figs['lapangan_usaha'].replace({'M, N. Jasa Perusahaan':'M, N. Jasa Perusahaan'})
                figsog=px.bar(figs,x='source_growth',y='lapangan_usaha',orientation='h',text='source_growth')
                figsog.update_traces(texttemplate='%{text:.2f}',textposition='outside',cliponaxis=False)
                figsog.update_layout(height=520,margin=dict(l=5,r=45,t=8,b=28),xaxis_title='Percentage point',yaxis_title=None,showlegend=False); figsog.update_yaxes(categoryorder='array', categoryarray=list(reversed(figs['lapangan_usaha'].tolist())))
                st.plotly_chart(figsog,use_container_width=True,config={'displayModeBar':False})
                st.caption(f'Total source of growth: {figs.source_growth.sum(skipna=True):.2f} percentage point.')

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
st.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
left,right=st.columns([1,1],gap='large')
with left:
    st.markdown(f'<div class="section-title">Posisi {wilayah} di Provinsi Riau</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a: st.markdown(f'<div class="rank-card"><div class="muted">Peringkat PDRB ADHK</div><div style="font-size:30px;font-weight:850;color:#132f78">{rank}</div><div class="muted">dari {len(allsel)} kabupaten/kota</div></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="rank-card"><div class="muted">Kontribusi PDRB</div><div style="font-size:30px;font-weight:850;color:#16A36A">{pct(contrib)}</div><div class="muted">terhadap total kabupaten/kota</div></div>',unsafe_allow_html=True)
with right:
    st.markdown(f'<div class="section-title">Perbandingan Kabupaten/Kota</div><div class="muted">Seluruh kabupaten/kota — {q} {year}</div>',unsafe_allow_html=True)
    comp_tabs=st.tabs(['ADHB','ADHK','YoY','QoQ','C-to-C'])
    comp_base=kab[kab.wilayah.astype(str).str.strip().isin(allsel.wilayah.astype(str).str.strip())].copy()
    comp_base['wilayah']=comp_base.wilayah.astype(str).str.strip()
    comp_base['qnum']=comp_base.triwulan.map(qorder)
    comp_base=comp_base.sort_values(['wilayah','tahun','qnum'])
    comp_base['yoy']=comp_base.groupby('wilayah')['adhk'].pct_change(4)*100
    comp_base['qoq']=comp_base.groupby('wilayah')['adhk'].pct_change(1)*100
    comp_base['prev_year']=comp_base['tahun']-1
    def _qoq_fix(r):
        if r['qnum']!=1: return r['qoq']
        z=comp_base[(comp_base.wilayah==r['wilayah'])&(comp_base.tahun==r['prev_year'])&(comp_base.triwulan=='Triwulan IV')]
        if z.empty or pd.isna(z.iloc[0].adhk) or z.iloc[0].adhk==0 or pd.isna(r.adhk): return np.nan
        return (r.adhk/z.iloc[0].adhk-1)*100
    comp_base['qoq']=comp_base.apply(_qoq_fix,axis=1)
    comp_base['ctc']=np.nan
    for w in comp_base.wilayah.dropna().unique():
        for yy in sorted(comp_base.loc[comp_base.wilayah==w,'tahun'].dropna().unique()):
            for qn in range(1,5):
                mask=(comp_base.wilayah==w)&(comp_base.tahun==yy)&(comp_base.qnum==qn)
                if mask.any():
                    cur=comp_base[(comp_base.wilayah==w)&(comp_base.tahun==yy)&(comp_base.qnum<=qn)].adhk.sum()
                    prv=comp_base[(comp_base.wilayah==w)&(comp_base.tahun==yy-1)&(comp_base.qnum<=qn)].adhk.sum()
                    if pd.notna(prv) and prv!=0: comp_base.loc[mask,'ctc']=(cur/prv-1)*100
    for tab, metric, unit, divisor in zip(comp_tabs,['adhb','adhk','yoy','qoq','ctc'],['Triliun Rupiah','Triliun Rupiah','Persen','Persen','Persen'],[1000,1000,1,1,1]):
        with tab:
            c=comp_base[(comp_base.tahun==year)&(comp_base.triwulan==q)][['wilayah',metric]].dropna().copy()
            # Untuk 2026, gunakan angka resmi total dari workbook BPS (Tabel 3.1–3.5),
            # bukan menghitung ulang YoY/QoQ/C-to-C dari seri database.
            if int(year) == 2026 and metric in ['adhb','adhk','yoy','qoq','ctc']:
                official=[]
                for w in c['wilayah'].tolist():
                    official.append(kab_total_metric(workbook_path, w, int(year), q, metric))
                c['nilai_resmi']=official
                c['nilai']=c['nilai_resmi']
                c=c.dropna(subset=['nilai'])
            if c.empty:
                st.info('Data perbandingan belum tersedia.')
            else:
                c['nilai']=c['nilai']/divisor
                c=c.sort_values('nilai',ascending=True)
                fig3=px.bar(c,x='nilai',y='wilayah',orientation='h',text='nilai')
                fmt='.2f'
                fig3.update_traces(texttemplate='%{text:'+fmt+'}',textposition='outside',cliponaxis=False)
                fig3.update_layout(height=350,margin=dict(l=10,r=45,t=10,b=20),xaxis_title=unit,yaxis_title=None,showlegend=False)
                st.plotly_chart(fig3,use_container_width=True,config={'displayModeBar':False})

st.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
st.markdown('<div class="section-title">Peta Posisi Kabupaten/Kota</div>',unsafe_allow_html=True)
try:
    geo_path=Path(__file__).resolve().parent/'assets'/'riau_kabkot.geojson'; geo=json.loads(geo_path.read_text(encoding='utf-8'))
    def sty(f):
        n=str(f.get('properties',{}).get('wilayah','')).strip(); return {'fillColor':'#7656D6' if n==wilayah else '#CFE0F0','color':'#FFFFFF','weight':1.4,'fillOpacity':0.88 if n==wilayah else 0.62}
    m=folium.Map(location=[0.5,101.5],zoom_start=6,tiles=None,control_scale=False)
    gj=folium.GeoJson(geo,style_function=sty,highlight_function=lambda f:{'weight':2.5,'color':'#132F78','fillOpacity':0.95},tooltip=folium.GeoJsonTooltip(fields=['wilayah'],aliases=['Kabupaten/Kota']))
    gj.add_to(m); m.fit_bounds(gj.get_bounds(),padding=(12,12)); st_folium(m,use_container_width=True,height=380,returned_objects=[])
except Exception as e: st.info('Peta wilayah tidak tersedia: '+str(e))

st.markdown('<div class="footer"><b>Riau Economic Analytics</b> · Analitik PDRB Kabupaten/Kota · Badan Pusat Statistik Provinsi Riau</div>',unsafe_allow_html=True)
