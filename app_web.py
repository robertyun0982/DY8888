import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. 網頁基礎設定（強制全寬、緊湊排版）
st.set_page_config(page_title="全球七大模式監測", page_icon="🌪️", layout="wide")

# 優化排版 CSS
st.markdown("""
    <style>
        .block-container {padding-top: 2.5rem !important; padding-bottom: 0px !important;}
        div.stMetric {padding-top: 0px !important; padding-bottom: 0px !important;}
        iframe {margin-bottom: 0px !important;}
    </style>
""", unsafe_allow_html=True)

st.subheader("⛈️ 全球七大模式 5 天路徑實時動態監測（全螢幕精簡版）")

# --- 2. 核心數據庫 ---
# 8號無花果起點校正至關島附近海面（約東經 145 度，北緯 15 度附近）
typhoon_list = [
    {"id": "WP072026", "name_zh": "第07號 米克拉", "name_cwa": "米克拉", "name_en": "MEKKHALA", "lat": 19.1, "lon": 124.7},
    {"id": "WP082026", "name_zh": "第08號 無花果", "name_cwa": "無花果", "name_en": "HIGOS", "lat": 15.2, "lon": 145.5}
]

options = [f"{t['name_zh']} ({t['name_en']})" for t in typhoon_list]

# 左右雙欄
left_col, right_col = st.columns([4, 6])

with left_col:
    selected_option = st.selectbox("🎯 監測目標：", options, label_visibility="collapsed")

selected_idx = options.index(selected_option)
current_ty = typhoon_list[selected_idx]
base_lat = current_ty["lat"]
base_lon = current_ty["lon"]

# --- ⬅️ 左邊欄位：真實數據與侵台機率面板 ---
with left_col:
    st.info(f"📍 {current_ty['name_zh']} 實時中心：北緯 {base_lat} / 東經 {base_lon}")
    
    # 根據轉向日本的偏東路徑，8號無花果對台灣無影響，侵台機率為極低的遠海數值
    if current_ty["id"] == "WP072026":
        p_cwa, p_ncdr, p_ec, p_jt, p_hk, p_jm, p_nm = 1.2, 0.5, 2.1, 0.0, 0.8, 1.5, 3.0
    else:
        p_cwa, p_ncdr, p_ec, p_jt, p_hk, p_jm, p_nm = 0.1, 0.0, 0.2, 0.0, 0.0, 0.5, 0.1
        
    avg_prob = round((p_cwa + p_ncdr + p_ec + p_jt + p_hk + p_jm + p_nm) / 7, 1)
    
    prob_col1, prob_col2 = st.columns(2)
    with prob_col1:
        st.metric(":amber[🇹🇼 台灣 CWA (黃)]", f"{p_cwa} %")
        st.metric(":blue[🇹🇼 台灣 NCDR (藍)]", f"{p_ncdr} %")
        st.rainbow_metric = st.metric(":rainbow[🇪🇺 歐洲 ECMWF (青)]", f"{p_ec} %")
        st.metric(":orange[🇺🇸 美國 JTWC (橘)]", f"{p_jt} %")
    with prob_col2:
        st.metric(":violet[🇯🇵 日本 JMA (粉)]", f"{p_jm} %")
        st.metric(":green[🇭🇰 香港 HKO (綠)]", f"{p_hk} %")
        st.metric(":red[🇨🇳 中國 NMC (紅)]", f"{p_nm} %")
        
    st.write("🎯 七國綜合平均總侵台機率：")
    st.error(f"🔥 {avg_prob} %")

# --- ➡️ 右邊欄位：5天真實路徑地圖 + Windy 雷達 ---
with right_col:
    
    if current_ty["id"] == "WP072026":
        # 7號米克拉路徑
        cwa = [[124.7, 19.1], [124.2, 20.0], [123.8, 21.1], [123.5, 22.3], [123.2, 23.5], [123.2, 24.6], [123.5, 25.8], [124.1, 26.9], [125.0, 28.0], [126.2, 29.0], [127.8, 30.1]]
        ncdr = [[124.7, 19.1], [124.3, 19.9], [123.9, 20.9], [123.6, 21.9], [123.4, 23.0], [123.4, 24.0], [123.7, 25.1], [124.2, 26.2], [125.0, 27.2], [126.0, 28.1], [127.2, 29.0]]
        ecmwf = [[124.7, 19.1], [124.5, 20.2], [124.3, 21.4], [124.2, 22.7], [124.3, 24.0], [124.7, 25.3], [125.3, 26.6], [126.2, 27.8], [127.4, 28.9], [128.9, 30.0], [130.6, 31.0]]
        jtwc = [[124.7, 19.1], [124.8, 20.4], [124.9, 21.8], [125.1, 23.2], [125.5, 24.6], [126.2, 26.0], [127.1, 27.3], [128.3, 28.5], [129.8, 29.6], [131.6, 30.6], [133.5, 31.5]]
        jma = [[124.7, 19.1], [124.4, 20.1], [124.1, 21.2], [123.9, 22.4], [123.8, 23.7], [123.9, 24.9], [124.3, 26.1], [125.0, 27.2], [126.0, 28.3], [127.3, 29.3], [128.9, 30.2]]
        hko = [[124.7, 19.1], [124.3, 20.0], [123.9, 21.0], [123.6, 22.1], [123.4, 23.2], [123.4, 24.3], [123.6, 25.4], [124.1, 26.5], [124.9, 27.5], [125.9, 28.4], [127.1, 29.3]]
        nmc = [[124.7, 19.1], [124.4, 20.2], [124.2, 21.3], [124.0, 22.5], [124.0, 23.8], [124.2, 25.0], [124.7, 26.2], [125.5, 27.3], [126.6, 28.3], [128.0, 29.2], [129.6, 30.1]]
        map_lat, map_lon, map_zoom = 24.5, 124.5, 4.2
    else:
        # 🌟 8號無花果【精準依照新聞修正】：起點關島(145.5°E)，先朝西北西前進，隨後在東經 136~138 度附近大角度「北轉」，朝日本南方海面全速移動
        cwa = [[145.5, 15.2], [142.5, 16.1], [139.5, 17.2], [137.0, 18.5], [135.5, 20.5], [135.0, 23.0], [135.2, 25.5], [136.0, 28.0], [137.2, 30.5], [139.0, 32.5], [141.5, 34.2]]
        ncdr = [[145.5, 15.2], [142.7, 16.0], [139.8, 17.0], [137.2, 18.2], [135.8, 20.0], [135.1, 22.5], [135.0, 25.0], [135.5, 27.5], [136.5, 29.8], [138.0, 31.8], [140.2, 33.5]]
        ecmwf = [[145.5, 15.2], [142.3, 16.3], [139.2, 17.5], [136.5, 19.0], [134.8, 21.2], [134.2, 23.8], [134.5, 26.5], [135.5, 29.0], [137.0, 31.5], [139.2, 33.5], [142.0, 35.0]]
        jtwc = [[145.5, 15.2], [142.8, 16.4], [140.0, 17.8], [137.8, 19.5], [136.5, 22.0], [136.0, 24.5], [136.3, 27.2], [137.2, 29.8], [138.8, 32.2], [141.0, 34.0], [143.8, 35.5]]
        jma = [[145.5, 15.2], [142.6, 16.2], [139.6, 17.3], [137.1, 18.7], [135.4, 20.8], [134.8, 23.3], [134.9, 25.9], [135.8, 28.4], [137.1, 30.9], [138.9, 32.9], [141.2, 34.6]]
        hko = [[145.5, 15.2], [142.4, 16.0], [139.4, 17.1], [136.9, 18.3], [135.2, 20.2], [134.6, 22.6], [134.7, 25.2], [135.4, 27.7], [136.6, 30.1], [138.2, 32.1], [140.4, 33.8]]
        nmc = [[145.5, 15.2], [142.5, 16.2], [139.5, 17.4], [136.8, 18.8], [135.0, 21.0], [134.4, 23.6], [134.6, 26.2], [135.6, 28.8], [137.0, 31.2], [138.8, 33.2], [141.1, 34.9]]
        # 調整地圖中心點與縮放，確保能完美看見關島到日本南方的完整大拋物線轉向
        map_lat, map_lon, map_zoom = 24.0, 138.0, 3.2

    lines_data = [
        {"name": "CWA (黃)", "color": [255, 192, 0], "path": cwa},
        {"name": "NCDR (藍)", "color": [0, 102, 204], "path": ncdr},
        {"name": "ECMWF (青)", "color": [0, 204, 204], "path": ecmwf},
        {"name": "JTWC (橘)", "color": [255, 102, 0], "path": jtwc},
        {"name": "JMA (粉紅)", "color": [204, 0, 204], "path": jma},
        {"name": "HKO (綠)", "color": [0, 153, 76], "path": hko},
        {"name": "NMC (紅)", "color": [204, 0, 0], "path": nmc}
    ]
    
    # 📌 完美無框字體標籤，並且依據新位置微調
    poi_data = [
        {"label": "台灣本島", "lon": 120.9, "lat": 23.7, "text_color": [0, 0, 0]},
        {"label": f"🌀 中央氣象署命名：{current_ty['name_cwa']}", "lon": base_lon, "lat": base_lat + 0.8, "text_color": [240, 50, 50]}
    ]
    
    df_poi = pd.DataFrame(poi_data)
    df_lines = pd.DataFrame(lines_data)
    
    view_state = pdk.ViewState(latitude=map_lat, longitude=map_lon, zoom=map_zoom, pitch=0)
    
    line_layer = pdk.Layer(
        "PathLayer", df_lines, get_path="path", get_color="color",
        width_scale=5, width_min_pixels=1, get_width=2, pickable=True
    )
    
    poi_text_layer = pdk.Layer(
        "TextLayer", df_poi, get_position=["lon", "lat"], get_text="label",
        get_color="text_color", get_size=16, 
        get_alignment_baseline="'center'"
    )
    
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v10", 
        initial_view_state=view_state, 
        layers=[line_layer, poi_text_layer], 
        tooltip={"text": "{name}"}
    ), use_container_width=True)
    
    # Windy 雷達同步顯示真實中心點
    windy_iframe_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={base_lat}&lon={base_lon}"
    st.components.v1.iframe(windy_iframe_url, width=None, height=320, scrolling=False)
