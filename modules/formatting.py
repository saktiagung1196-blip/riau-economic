def rupiah_juta(x):
    if x is None: return '-'
    try:
        if abs(x)>=1_000_000: return f'Rp {x/1_000_000:.2f} T'
        if abs(x)>=1_000: return f'Rp {x/1_000:.2f} M'
        return f'Rp {x:,.0f} Juta'
    except: return '-'

def miliar(x):
    if x is None: return '-'
    try: return f'{x:,.2f} Miliar'.replace(',','X').replace('.',',').replace('X','.')
    except: return '-'

def pct(x):
    try: return f'{x:.2f}%'.replace('.',',')
    except: return '-'

def compact(x):
    if x is None: return '-'
    try: return f'{x:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
    except: return '-'


def rupiah_miliar(x):
    if x is None: return '-'
    try:
        x=float(x)
        if abs(x)>=1000: return f'Rp {x/1000:.2f} T'
        return f'Rp {x:.2f} Miliar'
    except: return '-'
