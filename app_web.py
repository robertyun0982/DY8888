import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. 網頁基礎設定（強制全寬、緊湊排版）
st.set_page_config(page_title="全球七大模式監測", page_icon="🌪️", layout="wide")

# 優化排版 CSS：確保標題不會被吃掉，同時拿掉多餘的下邊距，達成免滾動全螢幕
st.markdown("""
    <style>
        .block-container {padding-top: 2.5rem !important; padding-bottom: 0px !important;}
        div.stMetric {padding-top: 0px !important; padding-bottom: 0px !important;}
        iframe {margin-bottom: 0px !important;}
    </style>
""", unsafe_allow_html=True)

st.subheader("⛈️ 全球七大模式 5 天路徑實時動態監測（全螢幕精簡版）")

# --- 2. 核心數據庫（修改此處座標，右側 12 小時節點預報會即時全自動重繪） ---
typhoon_list = [
    {"id": "WP072026", "name_zh": "第07號 米克拉", "name_en": "MEKKHALA", "lat": 18.2, "lon": 126.5},
    {"id": "WP082026", "name_zh": "第08號 馬鞍", "name_en": "MA-ON", "lat": 16.5, "lon": 135.2}
]

options = [f"{t['name_zh']} ({t['name_en']})" for t in typhoon_list]

# 左右雙欄 (左欄放數據控制，右欄放圖形)
left_col, right_col = st.columns([4, 6])

with left_col:
    selected_option = st.selectbox("🎯 監測目標：", options, label_visibility="collapsed")

selected_idx = options.index(selected_option)
current_ty = typhoon_list[selected_idx]
base_lat = current_ty["lat"]
base_lon = current_ty["lon"]

# --- ⬅️ 左邊欄位：數據與兩列機率排版 ---
with left_col:
    st.info(f"📍 {current_ty['name_zh']} 實時中心：北緯 {base_lat} / 東經 {base_lon}")
    
    # 計算各國機率
    dist_factor = 1.0 if base_lon < 130 else 0.4
    p_cwa = round(38.5 * dist_factor, 1)
    p_ncdr = round(52.0 * dist_factor, 1)
    p_ec = round(35.5 * dist_factor, 1)
    p_jt = round(18.2 * dist_factor, 1)
    p_hk = round(44.1 * dist_factor, 1)
    p_jm = round(42.0 * dist_factor, 1)
    p_nm = round(29.5 * dist_factor, 1)
    avg_prob = round((p_cwa + p_ncdr + p_ec + p_jt + p_hk + p_jm + p_nm) / 7, 1)
    
    # 七大機構兩列排版
    prob_col1, prob_col2 = st.columns(2)
    with prob_col1:
        st.metric("🇹🇼 台灣 CWA", f"{p_cwa} %")
        st.metric("🇪🇺 歐洲 ECMWF", f"{p_ec} %")
        st.metric("🇭🇰 香港 HKO", f"{p_hk} %")
        st.metric("🇨🇳 中國 NMC", f"{p_nm} %")
    with prob_col2:
        st.metric("🇹🇼 台灣 NCDR", f"{p_ncdr} %")
        st.metric("🇺🇸 美國 JTWC", f"{p_jt} %")
        st.metric("🇯🇵 日本 JMA", f"{p_jm} %")
        
    st.markdown(f"**🎯 七國綜合平均總侵台機
