from modules.parser import load_sources
from modules.database import init_db,replace_all
p='source_data/provinsi riau.xlsx'; k='source_data/data per kab kot.xlsx'
prov,kab=load_sources(p,k)
print('prov',prov.shape,prov.tahun.min(),prov.tahun.max(),prov.triwulan.unique())
print('kab',kab.shape,kab.tahun.min(),kab.tahun.max(),kab.wilayah.nunique())
init_db(); replace_all(prov,kab,'provinsi riau.xlsx + data per kab kot.xlsx')
