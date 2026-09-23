import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import requests
import json
import os
import folium
from streamlit_folium import st_folium

from modules.database import init_db, read_prov, read_kab
from modules.calculation import add_metrics, latest_quarter, QORDER
from modules.formatting import rupiah_juta, miliar, pct, compact
from modules.insight import build_insight
from modules.source_growth import province_source_growth, kab_source_growth, SECTOR_ORDER
from modules.navigation import render_sidebar

st.set_page_config(page_title='RIAU ECONOMIC ANALYTICS', page_icon='📊', layout='wide', initial_sidebar_state='expanded')
init_db()

st.markdown('''<style>
:root{--navy:#082b55;--blue:#0b63ce;--light:#f4f8fc;--purple:#7656d6;--green:#16a36a;--orange:#f29b38;--text:#18324f;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#06264b 0%,#0a376a 100%);}
[data-testid="stSidebar"] *{color:white!important;}
.block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1500px;}
.hero{background:linear-gradient(100deg,#f7fbff,#eef5ff);border:1px solid #dce8f5;border-radius:20px;padding:20px 24px;margin-bottom:18px;box-shadow:0 5px 18px rgba(8,43,85,.06)}
.hero h1{margin:0;color:#082b55;font-size:30px;letter-spacing:.2px}.hero p{margin:5px 0 0;color:#6a7d91}
.card{background:#fff;border:1px solid #e3ebf4;border-radius:17px;padding:17px 18px;box-shadow:0 5px 18px rgba(24,50,79,.06);height:100%}
.kpi-title{font-size:13px;color:#6d7f91;margin-bottom:6px}.kpi-value{font-size:25px;font-weight:750;color:#12385e}.kpi-sub{font-size:12px;color:#8796a6;margin-top:5px}.accent-blue{border-top:4px solid #0b63ce}.accent-purple{border-top:4px solid #7656d6}.accent-green{border-top:4px solid #16a36a}.accent-orange{border-top:4px solid #f29b38}
.section-title{font-size:19px;font-weight:750;color:#12385e;margin:4px 0 10px}.muted{color:#74869a;font-size:13px}.pill{display:inline-block;background:#edf5ff;color:#0b63ce;border-radius:999px;padding:6px 12px;font-weight:650;font-size:12px}
.insight{background:linear-gradient(110deg,#f5f0ff,#f7fbff);border:1px solid #e1d9fb;border-radius:17px;padding:18px 20px;color:#304764}

.insight-wrap{padding:18px 18px 20px;}
.insight-main-title{font-size:17px;font-weight:800;color:#123B63;margin-bottom:2px;}
.insight-subtitle{font-size:11px;color:#74869A;margin-bottom:14px;}
.insight-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;}
.insight-col{border:1px solid;border-radius:14px;padding:14px 14px 12px;min-height:250px;}
.insight-head{display:flex;align-items:center;gap:10px;}
.insight-icon{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:20px;font-weight:800;flex:0 0 32px;}
.insight-title{font-size:15px;font-weight:800;}
.insight-desc{font-size:10.5px;line-height:1.45;color:#61758A;margin:8px 0 11px;padding-bottom:10px;border-bottom:1px solid rgba(80,100,120,.12);}
.insight-list{display:flex;flex-direction:column;gap:6px;}
.insight-row{display:flex;align-items:flex-start;justify-content:space-between;gap:8px;background:rgba(255,255,255,.72);border:1px solid rgba(210,220,230,.55);border-radius:9px;padding:7px 8px;font-size:10.5px;line-height:1.35;color:#17324D;}
.insight-row span{flex:1;}
.insight-row b{white-space:nowrap;font-size:11px;}
.insight-empty{font-size:11px;color:#7A8A99;padding:8px 2px;}
@media(max-width:900px){.insight-grid{grid-template-columns:1fr;}.insight-col{min-height:auto;}}
.small-note{font-size:11px;color:#7d8c9b}
</style>''', unsafe_allow_html=True)

# Consistent custom sidebar navigation
render_sidebar('provinsi')

prov=read_prov(); kab=read_kab()
prov=add_metrics(prov)
# Backward-compatible fallback for existing data caches.
if 'distribusi_adhk' not in prov.columns:
    _tot_adhk = prov[prov.lapangan_usaha=='PDRB'][['tahun','triwulan','adhk']].rename(columns={'adhk':'_total_adhk'})
    prov = prov.merge(_tot_adhk,on=['tahun','triwulan'],how='left')
    prov['distribusi_adhk'] = np.where((prov['_total_adhk'].notna())&(prov['_total_adhk']!=0),prov['adhk']/prov['_total_adhk']*100,np.nan)
    prov = prov.drop(columns=['_total_adhk'],errors='ignore')

latest=latest_quarter(prov)
if latest is None:
    st.error('Belum ada data triwulanan. Silakan gunakan menu Upload Data.')
    st.stop()

# Pemilihan periode utama dashboard. Seluruh KPI, peta, distribusi,
# pertumbuhan, insight, dan tabel kabupaten/kota mengikuti periode ini.
available_periods = (
    prov.loc[prov['triwulan'] != 'Tahunan', ['tahun','triwulan']]
    .dropna()
    .drop_duplicates()
)
available_periods['qnum'] = available_periods['triwulan'].map(QORDER)
available_periods = available_periods.sort_values(['tahun','qnum'])
years = sorted(available_periods['tahun'].astype(int).unique(), reverse=True)

def _periods_for_year(y):
    z=available_periods[available_periods['tahun'].astype(int)==int(y)].sort_values('qnum')
    return z['triwulan'].tolist()

latest_year, latest_q = latest
with st.container():
    st.markdown('''<div class="hero"><h1>DASHBOARD PDRB PROVINSI RIAU</h1><p>Ringkasan perkembangan Produk Domestik Regional Bruto berdasarkan data yang diunggah ke sistem.</p></div>''',unsafe_allow_html=True)
    pc1,pc2,pc3=st.columns([0.8,1.0,2.2],gap='small')
    with pc1:
        year=st.selectbox('Tahun', years, index=years.index(latest_year), key='period_year')
    periods=_periods_for_year(year)
    default_q = latest_q if year == latest_year and latest_q in periods else periods[-1]
    with pc2:
        q=st.selectbox('Periode', periods, index=periods.index(default_q), key='period_quarter')
    latest_label=f'{q} {year}'
    with pc3:
        st.markdown(f'''<div style="margin-top:28px;text-align:right;"><span class="pill">📅 Periode aktif: {latest_label}</span></div>''',unsafe_allow_html=True)

# Pastikan periode terpilih memang memiliki total PDRB.
selected_total=prov[(prov.tahun==year)&(prov.triwulan==q)&(prov.lapangan_usaha=='PDRB')]
if selected_total.empty or selected_total['adhb'].isna().all():
    st.warning(f'Data PDRB untuk {latest_label} belum tersedia. Silakan pilih periode lain atau gunakan menu Upload Data.')
    st.stop()

k1,k2,k3,k4=st.columns(4,gap='small')
with k1:
    v=prov[(prov.tahun==year)&(prov.triwulan==q)&(prov.lapangan_usaha=='PDRB')]['adhb']
    st.markdown(f'<div class="card accent-blue"><div class="kpi-title">PDRB ADHB</div><div class="kpi-value">{rupiah_juta(v.iloc[0] if len(v) else None)}</div><div class="kpi-sub">{latest_label} • Harga Berlaku</div></div>',unsafe_allow_html=True)
with k2:
    v=prov[(prov.tahun==year)&(prov.triwulan==q)&(prov.lapangan_usaha=='PDRB')]['adhk']
    st.markdown(f'<div class="card accent-purple"><div class="kpi-title">PDRB ADHK</div><div class="kpi-value">{rupiah_juta(v.iloc[0] if len(v) else None)}</div><div class="kpi-sub">{latest_label} • Harga Konstan 2010</div></div>',unsafe_allow_html=True)
with k3:
    v=prov[(prov.tahun==year)&(prov.triwulan==q)&(prov.lapangan_usaha=='PDRB')]['yoy']
    st.markdown(f'<div class="card accent-green"><div class="kpi-title">PERTUMBUHAN YOY</div><div class="kpi-value">{pct(v.iloc[0] if len(v) else None)}</div><div class="kpi-sub">dibandingkan triwulan yang sama tahun sebelumnya</div></div>',unsafe_allow_html=True)
with k4:
    v=prov[(prov.tahun==year)&(prov.triwulan==q)&(prov.lapangan_usaha=='PDRB')]['qoq']
    st.markdown(f'<div class="card accent-orange"><div class="kpi-title">PERTUMBUHAN QOQ</div><div class="kpi-value">{pct(v.iloc[0] if len(v) else None)}</div><div class="kpi-sub">dibandingkan triwulan sebelumnya</div></div>',unsafe_allow_html=True)

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)
left,right=st.columns([1.45,1.1],gap='large')
with left:
    st.markdown('<div class="section-title">Perkembangan PDRB Provinsi Riau</div>',unsafe_allow_html=True)
    metric=st.radio('Indikator perkembangan', ['ADHK','ADHB','YoY','QoQ','C-to-C'], horizontal=True, label_visibility='collapsed')
    t=prov[(prov.lapangan_usaha=='PDRB')&(prov.triwulan!='Tahunan')].copy(); t['tanggal']=pd.to_datetime(t.tahun.astype(str)+'-'+t.triwulan.map({'Triwulan I':'03','Triwulan II':'06','Triwulan III':'09','Triwulan IV':'12'})+'-01')
    col={'ADHK':'adhk','ADHB':'adhb','YoY':'yoy','QoQ':'qoq','C-to-C':'ctc'}[metric]
    fig=px.line(t,x='tanggal',y=col,markers=True)
    selected_date=pd.Timestamp(year=int(year), month={'Triwulan I':3,'Triwulan II':6,'Triwulan III':9,'Triwulan IV':12}[q], day=1)
    fig.add_vline(x=selected_date, line_width=1.5, line_dash='dash')
    fig.update_layout(height=360,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor='white',plot_bgcolor='white',hovermode='x unified',xaxis_title=None,yaxis_title=('Juta Rupiah' if metric in ['ADHK','ADHB'] else '%'))
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

with right:
    st.markdown('<div class="section-title">Peta PDRB Kabupaten/Kota</div>',unsafe_allow_html=True)
    map_metric=st.selectbox('Variabel peta',['ADHB','ADHK','YoY','Kontribusi'],key='map_metric',label_visibility='collapsed')
    kk=kab[(kab.tahun==year)&(kab.triwulan==q)].copy()

    # YoY = triwulan berjalan dibanding triwulan yang sama tahun sebelumnya.
    prev=kab[(kab.tahun==year-1)&(kab.triwulan==q)][['wilayah','adhk']].copy()
    prev=prev.rename(columns={'adhk':'adhk_prev'})
    kk=kk.merge(prev,on='wilayah',how='left')
    kk['yoy']=((kk['adhk']/kk['adhk_prev'])-1)*100

    vals=kk[['wilayah','adhb','adhk','yoy']].copy()
    for c in ['adhb','adhk','yoy']:
        vals[c]=pd.to_numeric(vals[c],errors='coerce')
    vals['wilayah']=vals['wilayah'].astype(str).str.strip()

    # Kontribusi kabupaten/kota = PDRB ADHB kabupaten/kota dibagi total PDRB ADHB seluruh kabupaten/kota pada periode aktif.
    # Satuan ditampilkan dalam persen dan total 12 kabupaten/kota menjadi 100%.
    total_kabkot = vals['adhb'].sum(min_count=1)
    vals['kontribusi'] = (vals['adhb'] / total_kabkot * 100) if pd.notna(total_kabkot) and total_kabkot != 0 else np.nan

    try:
        geo_path=os.path.join(os.path.dirname(__file__),'assets','riau_kabkot.geojson')
        with open(geo_path,'r',encoding='utf-8') as fh:
            geo_local=json.load(fh)

        features=geo_local.get('features',[])
        if len(features)!=12:
            raise ValueError(f'GeoJSON harus berisi 12 kab/kota, ditemukan {len(features)} feature.')

        # Gabungkan nilai PDRB ke properties GeoJSON agar tooltip langsung
        # menampilkan nilai ketika kursor berada di wilayah.
        by_name=vals.set_index('wilayah').to_dict('index')
        active_values=[]

        def fmt(x, suffix=''):
            if x is None or pd.isna(x):
                return '-'
            return f'{float(x):,.2f}{suffix}'

        for f in features:
            p=f.setdefault('properties',{})
            name=str(p.get('wilayah','')).strip()
            row=by_name.get(name,{})
            adhb=row.get('adhb')
            adhk=row.get('adhk')
            yoy=row.get('yoy')
            active=row.get({'ADHB':'adhb','ADHK':'adhk','YoY':'yoy','Kontribusi':'kontribusi'}[map_metric])
            p['PDRB_ADHB']=fmt(adhb)
            p['PDRB_ADHK']=fmt(adhk)
            p['PERTUMBUHAN_YOY']=fmt(yoy,'%')
            p['KONTRIBUSI']=fmt(row.get('kontribusi'),'%')
            p['INDIKATOR_AKTIF']=fmt(active,'% ' if map_metric in ['YoY','Kontribusi'] else '')
            if active is not None and not pd.isna(active):
                active_values.append(float(active))

        vmin=min(active_values) if active_values else 0
        vmax=max(active_values) if active_values else 1

        def color_for(v):
            if v is None or pd.isna(v):
                return '#E8EEF5'
            if vmax==vmin:
                return '#4A90C2'
            t=max(0,min(1,(float(v)-vmin)/(vmax-vmin)))
            colors=['#EAF3FA','#C7E0F2','#8FC0DF','#4A90C2','#1769A6']
            return colors[min(4,int(t*5))]

        def style_function(feature):
            name=str(feature.get('properties',{}).get('wilayah','')).strip()
            row=by_name.get(name,{})
            active=row.get({'ADHB':'adhb','ADHK':'adhk','YoY':'yoy','Kontribusi':'kontribusi'}[map_metric])
            return {'fillColor':color_for(active),'color':'#FFFFFF','weight':1.5,'fillOpacity':0.80}

        def highlight_function(feature):
            return {'weight':3,'color':'#123B63','fillOpacity':0.95}

        # PUTIH: tidak ada basemap eksternal sama sekali.
        m=folium.Map(
            location=[0.5,101.5],
            zoom_start=6,
            tiles=None,
            control_scale=False,
            zoom_control=True,
            prefer_canvas=True
        )

        layer=folium.GeoJson(
            {'type':'FeatureCollection','features':features},
            name='Kabupaten/Kota Riau',
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
                fields=['wilayah','PDRB_ADHB','PDRB_ADHK','PERTUMBUHAN_YOY','KONTRIBUSI'],
                aliases=['Kabupaten/Kota','PDRB ADHB','PDRB ADHK','Pertumbuhan YoY','Kontribusi terhadap Total PDRB Kabupaten/Kota'],
                localize=False,
                sticky=True,
                labels=True,
                style=(
                    "background-color: white; color: #17324D; "
                    "font-family: Arial; font-size: 12px; padding: 7px; "
                    "border: 1px solid #D8E2EC; border-radius: 5px;"
                )
            )
        )
        layer.add_to(m)

        bounds=layer.get_bounds()
        if bounds and bounds[0] and bounds[1]:
            m.fit_bounds(bounds,padding=(15,15))

        st_folium(m,use_container_width=True,height=420,returned_objects=[])
        st.caption('Kontribusi menunjukkan persentase PDRB kabupaten/kota terhadap total PDRB seluruh kabupaten/kota pada periode aktif (total = 100%).')
    except Exception as e:
        st.error(f'Peta gagal dimuat: {e}')
        st.dataframe(vals.rename(columns={'adhb':'ADHB','adhk':'ADHK','yoy':'YoY'}),hide_index=True,use_container_width=True,height=300)




st.markdown('<div style="height:8px"></div>',unsafe_allow_html=True)
left,right=st.columns([1,1],gap='large')

sector_order = [
    'A. Pertanian, Kehutanan, dan Perikanan',
    'B. Pertambangan dan Penggalian',
    'C. Industri Pengolahan',
    'D. Pengadaan Listrik dan Gas',
    'E. Pengadaan Air, Pengelolaan Sampah, Limbah dan Daur Ulang',
    'F. Konstruksi',
    'G. Perdagangan Besar dan Eceran; Reparasi Mobil dan Sepeda Motor',
    'H. Transportasi dan Pergudangan',
    'I. Penyediaan Akomodasi dan Makan Minum',
    'J. Informasi dan Komunikasi',
    'K. Jasa Keuangan dan Asuransi',
    'L. Real Estat',
    'M, N. Jasa Perusahaan',
    'O. Administrasi Pemerintahan, Pertahanan dan Jaminan Sosial Wajib',
    'P. Jasa Pendidikan',
    'Q. Jasa Kesehatan dan Kegiatan Sosial',
    'R, S, T, U. Jasa lainnya'
]

def sector_order_no(name):
    s=str(name).strip().replace('M,N.','M, N.').replace('R,S,T,U.','R, S, T, U.')
    for i,prefix in enumerate(sector_order):
        if s.startswith(prefix):
            return i
    return 999

# =========================================================
# Analisis Lapangan Usaha — 3 panel dalam satu baris
# =========================================================
col_dist, col_growth, col_sog = st.columns(3, gap='medium')

with col_dist:
    st.markdown('<div class="section-title">Distribusi PDRB</div>',unsafe_allow_html=True)
    st.markdown('<div class="small-note">Menurut 17 lapangan usaha</div>',unsafe_allow_html=True)
    dtab1,dtab2=st.tabs(['ADHB','ADHK'])
    for tab,field in [(dtab1,'distribusi'),(dtab2,'distribusi_adhk')]:
        with tab:
            s=prov[(prov.tahun==year)&(prov.triwulan==q)].copy()
            s=s[~s.lapangan_usaha.isin(['PDRB','PDRB Tanpa Migas'])].dropna(subset=[field])
            s['urutan']=s['lapangan_usaha'].map(sector_order_no)
            s=s[s['urutan']<17].sort_values('urutan')
            fig=px.bar(s,x=field,y='lapangan_usaha',orientation='h',text=field)
            fig.update_traces(texttemplate='%{text:.2f}%',textposition='outside',cliponaxis=False,textfont_size=8)
            fig.update_layout(height=475,margin=dict(l=0,r=38,t=5,b=30),xaxis_title='Persen',yaxis_title=None,showlegend=False,
                              yaxis=dict(categoryorder='array',categoryarray=s['lapangan_usaha'].tolist()[::-1],tickfont=dict(size=8)))
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

with col_growth:
    st.markdown('<div class="section-title">Pertumbuhan Lapangan Usaha</div>',unsafe_allow_html=True)
    st.markdown('<div class="small-note">Perubahan menurut lapangan usaha</div>',unsafe_allow_html=True)
    gtab1,gtab2,gtab3=st.tabs(['YoY','QoQ','C-to-C'])
    for tab,field in [(gtab1,'yoy'),(gtab2,'qoq'),(gtab3,'ctc')]:
        with tab:
            s=prov[(prov.tahun==year)&(prov.triwulan==q)].copy()
            s=s[~s.lapangan_usaha.isin(['PDRB','PDRB Tanpa Migas'])].dropna(subset=[field])
            s['urutan']=s['lapangan_usaha'].map(sector_order_no)
            s=s[s['urutan']<17].sort_values('urutan')
            fig=px.bar(s,x=field,y='lapangan_usaha',orientation='h',text=field)
            fig.update_traces(texttemplate='%{text:.2f}%',textposition='outside',cliponaxis=False,textfont_size=8)
            fig.update_layout(height=475,margin=dict(l=0,r=38,t=5,b=30),xaxis_title='Persen',yaxis_title=None,showlegend=False,
                              yaxis=dict(categoryorder='array',categoryarray=s['lapangan_usaha'].tolist()[::-1],tickfont=dict(size=8)))
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

with col_sog:
    st.markdown('<div class="section-title">Source of Growth</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="small-note">Kontribusi terhadap pertumbuhan {latest_label}. Satuan: percentage point.</div>',unsafe_allow_html=True)
    sogtab1,sogtab2,sogtab3=st.tabs(['Y-on-Y','Q-to-Q','C-to-C'])
    for tab,mode in [(sogtab1,'Y-on-Y'),(sogtab2,'Q-to-Q'),(sogtab3,'C-to-C')]:
        with tab:
            sog=province_source_growth(prov, int(year), q, mode)
            if sog.empty:
                st.info('Belum tersedia.')
            else:
                total_sog=sog.source_growth.sum(skipna=True)
                chart=sog.sort_values('source_growth',ascending=True).copy()
                fig=px.bar(chart,x='source_growth',y='lapangan_usaha',orientation='h',text='source_growth')
                fig.update_traces(texttemplate='%{text:.2f}',textposition='outside',cliponaxis=False,textfont_size=8)
                fig.update_layout(height=475,margin=dict(l=0,r=38,t=5,b=30),xaxis_title='pp',yaxis_title=None,showlegend=False,
                                  yaxis=dict(tickfont=dict(size=8)))
                st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
                st.caption(f'Total: {total_sog:.2f} pp')

st.markdown('<div style="height:18px"></div>',unsafe_allow_html=True)

st.markdown('<div class="section-title">Angka Kunci</div>',unsafe_allow_html=True)
key_sec=prov[(prov.tahun==year)&(prov.triwulan==q)].copy()
key_sec=key_sec[~key_sec.lapangan_usaha.isin(['PDRB','PDRB Tanpa Migas'])].copy()
key_sec['urutan']=key_sec['lapangan_usaha'].map(sector_order_no)
key_sec=key_sec[key_sec['urutan']<17]
# Bandingkan dengan tahun sebelumnya pada triwulan yang sama (YoY).
# Contoh: Triwulan II 2026 dibandingkan dengan Triwulan II 2025.
prev_year = int(year) - 1
prev_q = q
prev_sec = prov[(prov.tahun==prev_year)&(prov.triwulan==prev_q)&(~prov.lapangan_usaha.isin(['PDRB','PDRB Tanpa Migas']))][['lapangan_usaha','yoy']].copy()
prev_sec=prev_sec.rename(columns={'yoy':'yoy_sebelumnya'})
key_sec=key_sec.merge(prev_sec,on='lapangan_usaha',how='left')
growth_top=key_sec.dropna(subset=['yoy']).sort_values('yoy',ascending=False).head(3)
dist_top=key_sec.dropna(subset=['distribusi']).sort_values('distribusi',ascending=False).head(3)

k1,k2=st.columns(2,gap='large')
with k1:
    st.markdown('<div class="card" style="border-top:4px solid #2F80ED;padding:16px 18px;"><div style="font-size:15px;font-weight:750;color:#123B63;">Top 3 Pertumbuhan YoY</div><div style="font-size:11px;color:#74869A;margin:4px 0 12px;">Lapangan usaha dengan pertumbuhan tertinggi pada periode terbaru.</div>',unsafe_allow_html=True)
    for i,(_,row) in enumerate(growth_top.iterrows(),1):
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid #E5ECF3;"><div style="min-width:27px;height:27px;border-radius:50%;background:#EAF3FA;color:#1769A6;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:12px;">{i}</div><div style="flex:1;font-size:12px;font-weight:650;color:#17324D;">{row["lapangan_usaha"]}</div><div style="font-size:14px;font-weight:800;color:#1769A6;">{float(row["yoy"]):.2f}%</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
with k2:
    st.markdown('<div class="card" style="border-top:4px solid #7656D6;padding:16px 18px;"><div style="font-size:15px;font-weight:750;color:#123B63;">Top 3 Distribusi</div><div style="font-size:11px;color:#74869A;margin:4px 0 12px;">Lapangan usaha dengan kontribusi terbesar terhadap PDRB.</div>',unsafe_allow_html=True)
    for i,(_,row) in enumerate(dist_top.iterrows(),1):
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;padding:9px 0;border-top:1px solid #E5ECF3;"><div style="min-width:27px;height:27px;border-radius:50%;background:#F0ECFF;color:#6242D9;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:12px;">{i}</div><div style="flex:1;font-size:12px;font-weight:650;color:#17324D;">{row["lapangan_usaha"]}</div><div style="font-size:14px;font-weight:800;color:#6242D9;">{float(row["distribusi"]):.2f}%</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

st.markdown('<div style="height:14px"></div>',unsafe_allow_html=True)

# Insight otomatis dalam 3 kolom agar ringkas dan mudah dibaca.
def _insight_groups(sectors):
    s=sectors.copy()
    naik, melambat, kontraksi = [], [], []
    for _, r in s.iterrows():
        name=str(r.get('lapangan_usaha','')).strip()
        if not name or name in ['PDRB','PDRB Tanpa Migas']:
            continue
        try:
            yoy=float(r.get('yoy'))
        except (TypeError,ValueError):
            continue
        prev=r.get('yoy_sebelumnya',np.nan)
        try: prev=float(prev)
        except (TypeError,ValueError): prev=np.nan
        if yoy < 0:
            kontraksi.append((name,yoy))
        elif pd.notna(prev) and yoy <= prev:
            melambat.append((name,yoy))
        else:
            naik.append((name,yoy))
    return naik, melambat, kontraksi

def _insight_items(items, title, tone, icon, bg, border):
    rows=''.join(
        f'<div class="insight-row"><span>{name}</span><b>{value:.2f}%</b></div>'
        for name,value in items
    )
    if not rows:
        rows='<div class="insight-empty">Tidak ada lapangan usaha.</div>'
    return f'''<div class="insight-col" style="background:{bg};border-color:{border};">
        <div class="insight-head"><span class="insight-icon" style="background:{tone};">{icon}</span>
        <div><div class="insight-title" style="color:{tone};">{title}</div></div></div>
        <div class="insight-desc">{"Pertumbuhan lebih tinggi dibanding periode yang sama tahun sebelumnya." if title=="Tumbuh Naik" else "Masih tumbuh, tetapi lebih rendah dibanding periode yang sama tahun sebelumnya." if title=="Tumbuh Melambat" else "Pertumbuhan negatif dibanding periode yang sama tahun sebelumnya."}</div>
        <div class="insight-list">{rows}</div>
    </div>'''

naik, melambat, kontraksi = _insight_groups(key_sec)
st.markdown(f'''<div class="insight insight-wrap">
    <div class="insight-main-title">💡 Insight Otomatis</div>
    <div class="insight-subtitle">Perbandingan dengan periode yang sama tahun sebelumnya (YoY) • {latest_label}</div>
    <div class="insight-grid">
        {_insight_items(naik,'Tumbuh Naik','#138A45','↑','#F0FBF5','#B9E8CE')}
        {_insight_items(melambat,'Tumbuh Melambat','#C27A00','−','#FFFBEF','#F1D98C')}
        {_insight_items(kontraksi,'Kontraksi','#D72626','↓','#FFF3F3','#F2C4C4')}
    </div>
</div>''',unsafe_allow_html=True)

st.markdown('<div class="small-note">Sumber data: workbook yang dimuat ke sistem. Data provinsi menggunakan satuan juta rupiah; data kabupaten/kota menggunakan miliar rupiah sesuai sumber.</div>',unsafe_allow_html=True)
