import pandas as pd

def build_insight(sectors, latest_label):
    """Generate concise sector-status insight for the selected period.

    Categories are based on YoY growth in the selected period versus the
    preceding period's YoY growth:
      - Tumbuh Naik: current YoY > 0 and higher than previous period
      - Tumbuh Melambat: current YoY > 0 and lower/equal to previous period
      - Kontraksi: current YoY < 0
    If the comparison value is unavailable, positive growth is treated as
    Tumbuh Naik and negative growth as Kontraksi.
    """
    s = sectors.copy()
    if 'yoy' not in s.columns:
        return f'Data {latest_label} tersedia, namun indikator pertumbuhan sektor belum lengkap.'
    s = s[~s['lapangan_usaha'].isin(['PDRB', 'PDRB Tanpa Migas'])].dropna(subset=['yoy']).copy()
    if s.empty:
        return f'Data {latest_label} tersedia, namun indikator pertumbuhan sektor belum lengkap.'

    naik, melambat, kontraksi = [], [], []
    for _, r in s.iterrows():
        name = str(r['lapangan_usaha'])
        yoy = float(r['yoy'])
        prev = r.get('yoy_sebelumnya', pd.NA)
        try:
            prev = float(prev)
        except (TypeError, ValueError):
            prev = None

        if yoy < 0:
            kontraksi.append((name, yoy))
        elif prev is not None and yoy <= prev:
            melambat.append((name, yoy))
        else:
            naik.append((name, yoy))

    def lines(items):
        if not items:
            return '<div style="color:#7A8A99;font-size:12px;">Tidak ada lapangan usaha.</div>'
        return ''.join(
            f'<div style="padding:4px 0;font-size:12px;color:#17324D;">• {name} <b>{value:.2f}%</b></div>'
            for name, value in items
        )

    return (
        f'<div style="margin-bottom:10px;"><b style="color:#1B8A5A;">🟢 Tumbuh Naik</b>{lines(naik)}</div>'
        f'<div style="margin-bottom:10px;"><b style="color:#B7791F;">🟡 Tumbuh Melambat</b>{lines(melambat)}</div>'
        f'<div><b style="color:#C0392B;">🔴 Kontraksi</b>{lines(kontraksi)}</div>'
    )
