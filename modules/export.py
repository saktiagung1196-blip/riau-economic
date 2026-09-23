import io

def to_excel(df):
    out=io.BytesIO()
    with __import__('pandas').ExcelWriter(out,engine='openpyxl') as w: df.to_excel(w,index=False,sheet_name='Data')
    return out.getvalue()
