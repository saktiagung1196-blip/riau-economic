import streamlit as st


def render_sidebar(active='provinsi'):
    """Render one consistent custom sidebar on every page."""
    with st.sidebar:
        st.markdown(
            '<div style="font-size:23px;font-weight:800;line-height:1.02;margin:10px 0 6px">'
            'RIAU ECONOMIC<br>ANALYTICS</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size:11px;opacity:.88;margin-bottom:24px">'
            'Data untuk Kebijakan, Ekonomi untuk Masa Depan</div>',
            unsafe_allow_html=True,
        )
        st.markdown('---')
        st.markdown('<div style="font-size:12px;opacity:.7;margin-bottom:7px">DASHBOARD</div>', unsafe_allow_html=True)

        # Keep exactly the same order on every page.
        st.page_link('app.py', label='📊 Provinsi')
        st.page_link('pages/03_Kabupaten_Kota.py', label='📍 Kabupaten/Kota')
        st.page_link('pages/01_Upload_Data.py', label='🔄 Upload Data')
        st.page_link('pages/02_Tentang.py', label='ℹ️ Tentang')

        st.markdown(
            '<div style="position:fixed;bottom:18px;font-size:11px;opacity:.8;max-width:230px">'
            'Statistik Berkualitas untuk Riau Maju<br><br><b>BPS PROVINSI RIAU</b></div>',
            unsafe_allow_html=True,
        )
