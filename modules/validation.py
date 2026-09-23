import pandas as pd

def validate_upload(df, required):
    errors=[]
    missing=[c for c in required if c not in df.columns]
    if missing: errors.append('Kolom wajib belum tersedia: '+', '.join(missing))
    return errors
