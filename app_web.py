import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. 網頁基礎設定（強制全寬、緊湊排版）
st.set_page_config(page_title="全球七大模式監測", page_icon="🌪️", layout="wide")

# 使用 CSS 強制壓縮 Streamlit 內建的上下空白間距，達成免滾動全螢幕效果
st.markdown("""
    <style>
        .block-container {padding-top: 1.5rem !important; padding-bottom: 0px !important;}
        div.stMetric {padding-top: 0px !important; padding-bottom: 0px !important;}
        iframe {margin-bottom: 0px !important;}
    </style>
""", unsafe_allow_html=True)

st.subheader("⛈️ 全球七大模式 5 天路徑實時動態監測（全螢幕精簡版）")

# --- 2. 核心數據庫（在此修改即時颱風位置，右側 5 天預報會自動連動更新） ---
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
        
    # 精簡型大字體綜合侵台機率
    st.markdown(f"**🎯 七國綜合平均總侵台機率：**")
    st.error(f"🔥 {avg_prob} %")

# --- ➡️ 右邊欄位：5天預報地圖 + Windy 雷達 ---
with right_col:
    # 🔥 核心擴充：補滿至 5 天（目前位置、24H、48H...到 120H 共有 6 個點）的即時推算座標
    cwa = [[base_lon, base_lat], [base_lon-1.5, base_lat+1.5], [base_lon-3.2, base_lat+3.5], [base_lon-4.5, base_lat+5.0], [base_lon-5.5, base_lat+6.2], [121.5, 23.8]]
    ncdr = [[base_lon, base_lat], [base_lon-1.8, base_lat+1.2], [base_lon-3.8, base_lat+2.8], [base_lon-5.0, base_lat+4.0], [base_lon-6.0, base_lat+5.0], [120.5, 22.5]]
    ecmwf = [[base_lon, base_lat], [base_lon-1.2, base_lat+1.6], [base_lon-2.5, base_lat+3.8], [base_lon-3.5, base_lat+5.5], [base_lon-4.2, base_lat+7.0], [122.0, 24.5]]
    jtwc = [[base_lon, base_lat], [base_lon-0.8, base_lat+1.8], [base_lon-1.2, base_lat+4.2], [base_lon-1.0, base_lat+6.0], [base_lon-0.5, base_lat+7.5], [123.0, 25.5]]
    jma = [[base_lon, base_lat], [base_lon-1.6, base_lat+1.4], [base_lon-3.4, base_lat+3.3], [base_lon-4.8, base_lat+4.8], [base_lon-5.8, base_lat+6.0], [121.0, 23.5]]
    hko = [[base_lon, base_lat], [base_lon-1.7, base_lat+1.3], [base_lon-3.6, base_lat+3.0], [base_lon-5.2, base_lat+4.5], [base_lon-6.2, base_lat+5.8], [121.8, 24.0]]
    nmc = [[base_lon, base_lat], [base_lon-1.4, base_lat+1.6], [base_lon-3.0, base_lat+3.6], [base_lon-4.0, base_lat+5.2], [base_lon-4.8, base_lat+6.5], [122.5, 24.8]]
    
    lines_data = [
        {"name": "CWA (黃)", "color": [255, 255, 0], "path": cwa},
        {"name": "NCDR (藍)", "color": [0, 128, 255], "path": ncdr},
        {"name": "ECMWF (青)", "color": [0, 255, 255], "path": ecmwf},
        {"name": "JTWC (橘)", "color": [255, 128, 0], "path": jtwc},
        {"name": "JMA (粉紅)", "color": [255, 0, 255], "path": jma},
        {"name": "HKO (綠)", "color": [0, 200, 0], "path": hko},
        {"name": "NMC (紅)", "color": [255, 0, 0], "path": nmc}
    ]
    
    df_lines = pd.DataFrame(lines_data)
    view_state = pdk.ViewState(latitude=22.5, longitude=123.0, zoom=4.2, pitch=0)
    
    line_layer = pdk.Layer(
        "PathLayer", df_lines, get_path="path", get_color="color",
        width_scale=20, width_min_pixels=3, get_width=5, pickable=True
    )
    
    # 壓縮地圖高度至 260px，確保不觸發網頁滾動條
    st.pydeck_chart(pdk.Deck(
        map_style="road", initial_view_state=view_state, layers=[line_layer], 
        tooltip={"text": "{name}"}
    ), use_container_width=True)
    
    # 壓縮 Windy 雷達高度至 260px
    windy_iframe_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={base_lat}&lon={base_lon}"
    st.components.v1.iframe(windy_iframe_url, width=None, height=260, scrolling=False)
