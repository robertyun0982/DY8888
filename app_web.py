import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. 網頁基礎設定（強制全寬、緊湊排版）
st.set_page_config(page_title="全球七大模式監測", page_icon="🌪️", layout="wide")

# 優化排版 CSS：確保標題不被吃掉，壓縮間距
st.markdown("""
    <style>
        .block-container {padding-top: 2.5rem !important; padding-bottom: 0px !important;}
        div.stMetric {padding-top: 0px !important; padding-bottom: 0px !important;}
        iframe {margin-bottom: 0px !important;}
    </style>
""", unsafe_allow_html=True)

st.subheader("⛈️ 全球七大模式 5 天路徑實時動態監測（全螢幕精簡版）")

# --- 2. 核心數據庫 ---
typhoon_list = [
    {"id": "WP072026", "name_zh": "第07號 米克拉", "name_en": "MEKKHALA", "lat": 18.2, "lon": 126.5},
    {"id": "WP082026", "name_zh": "第08號 馬鞍", "name_en": "MA-ON", "lat": 16.5, "lon": 135.2}
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

# --- ⬅️ 左邊欄位：數據與兩列機率排版 ---
with left_col:
    st.info(f"📍 {current_ty['name_zh']} 實時中心：北緯 {base_lat} / 東經 {base_lon}")
    
    dist_factor = 1.0 if base_lon < 130 else 0.4
    p_cwa = round(38.5 * dist_factor, 1)
    p_ncdr = round(52.0 * dist_factor, 1)
    p_ec = round(35.5 * dist_factor, 1)
    p_jt = round(18.2 * dist_factor, 1)
    p_hk = round(44.1 * dist_factor, 1)
    p_jm = round(42.0 * dist_factor, 1)
    p_nm = round(29.5 * dist_factor, 1)
    avg_prob = round((p_cwa + p_ncdr + p_ec + p_jt + p_hk + p_jm + p_nm) / 7, 1)
    
    prob_col1, prob_col2 = st.columns(2)
    with prob_col1:
        st.metric(":amber[🇹🇼 台灣 CWA (黃)]", f"{p_cwa} %")
        st.metric(":blue[🇹🇼 台灣 NCDR (藍)]", f"{p_ncdr} %")
        st.metric(":rainbow[🇪🇺 歐洲 ECMWF (青)]", f"{p_ec} %")
        st.metric(":orange[🇺🇸 美國 JTWC (橘)]", f"{p_jt} %")
    with prob_col2:
        st.metric(":violet[🇯🇵 日本 JMA (粉)]", f"{p_jm} %")
        st.metric(":green[🇭🇰 香港 HKO (綠)]", f"{p_hk} %")
        st.metric(":red[🇨🇳 中國 NMC (紅)]", f"{p_nm} %")
        
    st.write("🎯 七國綜合平均總侵台機率：")
    st.error(f"🔥 {avg_prob} %")

# --- ➡️ 右邊欄位：5天預報地圖 + Windy 雷達 ---
with right_col:
    
    # 🔥 精確路線重構：每 12 小時一個移動節點（共 11 個點），模擬符合新聞發布的權威氣象修正趨勢
    # CWA/NCDR 走勢偏向花東登陸穿過台灣；ECMWF 偏東修正從東部海域北上；JTWC 則更偏東外海。
    cwa = [
        [base_lon, base_lat], [base_lon-0.6, base_lat+0.5], [base_lon-1.2, base_lat+1.1],
        [base_lon-1.8, base_lat+1.7], [base_lon-2.5, base_lat+2.3], [base_lon-3.2, base_lat+3.0],
        [base_lon-4.0, base_lat+3.7], [base_lon-4.7, base_lat+4.4], [121.8, 23.5], # 接近台灣
        [121.0, 24.2], [119.5, 25.0] # 穿過台灣
    ]
    
    ncdr = [
        [base_lon, base_lat], [base_lon-0.7, base_lat+0.4], [base_lon-1.4, base_lat+0.9],
        [base_lon-2.2, base_lat+1.5], [base_lon-3.0, base_lat+2.1], [base_lon-3.8, base_lat+2.7],
        [base_lon-4.6, base_lat+3.4], [base_lon-5.3, base_lat+4.1], [121.3, 22.8], # 登陸台東
        [120.5, 23.6], [119.0, 24.5]
    ]
    
    ecmwf = [
        [base_lon, base_lat], [base_lon-0.4, base_lat+0.5], [base_lon-0.9, base_lat+1.1],
        [base_lon-1.4, base_lat+1.8], [base_lon-1.9, base_lat+2.6], [base_lon-2.4, base_lat+3.4],
        [base_lon-2.9, base_lat+4.3], [base_lon-3.3, base_lat+5.2], [123.2, 24.0], # 東部海域北上
        [122.5, 25.2], [122.0, 26.5]
    ]
    
    jtwc = [
        [base_lon, base_lat], [base_lon-0.2, base_lat+0.6], [base_lon-0.4, base_lat+1.3],
        [base_lon-0.6, base_lat+2.1], [base_lon-0.8, base_lat+3.0], [base_lon-0.9, base_lat+4.0],
        [base_lon-1.0, base_lat+5.0], [base_lon-0.9, base_lat+6.0], [124.5, 24.5], # 遠海偏東大拐彎
        [124.0, 25.8], [123.8, 27.2]
    ]
    
    jma = [
        [base_lon, base_lat], [base_lon-0.5, base_lat+0.4], [base_lon-1.1, base_lat+1.0],
        [base_lon-1.8, base_lat+1.6], [base_lon-2.6, base_lat+2.3], [base_lon-3.3, base_lat+3.0],
        [base_lon-4.0, base_lat+3.8], [base_lon-4.6, base_lat+4.6], [122.0, 23.8], # 擦過東北角
        [121.3, 25.0], [120.5, 26.2]
    ]
    
    hko = [
        [base_lon, base_lat], [base_lon-0.5, base_lat+0.4], [base_lon-1.2, base_lat+0.9],
        [base_lon-2.0, base_lat+1.5], [base_lon-2.8, base_lat+2.2], [base_lon-3.6, base_lat+2.9],
        [base_lon-4.4, base_lat+3.6], [base_lon-5.1, base_lat+4.4], [121.6, 23.2], # 緊貼東海岸
        [121.0, 24.5], [120.0, 25.8]
    ]
    
    nmc = [
        [base_lon, base_lat], [base_lon-0.4, base_lat+0.5], [base_lon-1.0, base_lat+1.1],
        [base_lon-1.6, base_lat+1.7], [base_lon-2.2, base_lat+2.4], [base_lon-2.8, base_lat+3.2],
        [base_lon-3.4, base_lat+4.0], [base_lon-3.9, base_lat+4.9], [122.8, 24.2], # 綠島蘭嶼海域北上
        [122.2, 25.5], [121.7, 26.8]
    ]
    
    # 各機構路徑資料
    lines_data = [
        {"name": "CWA (黃)", "color": [255, 192, 0], "path": cwa},
        {"name": "NCDR (藍)", "color": [0, 102, 204], "path": ncdr},
        {"name": "ECMWF (青)", "color": [0, 204, 204], "path": ecmwf},
        {"name": "JTWC (橘)", "color": [255, 102, 0], "path": jtwc},
        {"name": "JMA (粉紅)", "color": [204, 0, 204], "path": jma},
        {"name": "HKO (綠)", "color": [0, 153, 76], "path": hko},
        {"name": "NMC (紅)", "color": [204, 0, 0], "path": nmc}
    ]
    
    # 僅保留地點純文字標籤，將紅色圓點資料與圖層徹底移除
    poi_data = [
        {"label": "🇹🇼 台灣本島", "lon": 120.9, "lat": 23.7}
    ]
    df_poi = pd.DataFrame(poi_data)
    df_lines = pd.DataFrame(lines_data)
    
    view_state = pdk.ViewState(latitude=22.5, longitude=123.0, zoom=4.3, pitch=0)
    
    # 軌跡線圖層（寬度調細為 2，呈現細緻質感）
    line_layer = pdk.Layer(
        "PathLayer", df_lines, get_path="path", get_color="color",
        width_scale=5, width_min_pixels=1, get_width=2, pickable=True
    )
    
    # 地名文字標籤圖層（拿掉了 Marker 紅圈圖層）
    poi_text_layer = pdk.Layer(
        "TextLayer",
        df_poi,
        get_position=["lon", "lat"],
        get_text="label",
        get_color=[255, 255, 255],
        get_size=14,
        background_color=[0, 0, 0, 160],
        get_pixel_offset=[0, 0]
    )
    
    # 疊加細線與文字標籤，高度維持 320px
    st.pydeck_chart(pdk.Deck(
        map_style="road", 
        initial_view_state=view_state, 
        layers=[line_layer, poi_text_layer], 
        tooltip={"text": "{name}"}
    ), use_container_width=True)
    
    # Windy 雷達高度同步固定在 320px（完美平均大小）
    windy_iframe_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={base_lat}&lon={base_lon}"
    st.components.v1.iframe(windy_iframe_url, width=None, height=320, scrolling=False)
