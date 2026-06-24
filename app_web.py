import streamlit as st
import pandas as pd
import pydeck as pdk
import math

# 1. 網頁基礎設定（強制全寬、戰情室高強度排版）
st.set_page_config(page_title="勇式颱風侵台概率監測系統", page_icon="⚡", layout="wide")

# 台灣地理中心點基準座標
TW_LAT, TW_LON = 23.97, 120.97

def calc_haversine(lat1, lon1, lat2, lon2):
    """ 地球大圓距離空間圍欄核心演算法 (單位: 公里) """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# --- 🚀 2. 戰情室專用高級 CSS 操控 ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 0px !important; 
            max-width: 1400px !important; 
            margin: 0 auto;
        }
        /* 頂部橫幅 HTML 方格樣式 */
        .dashboard-banner {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 15px;
        }
        .metric-card {
            background-color: #1e293b !important;
            border: 1px solid #475569 !important;
            padding: 12px 10px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        /* 鎖定純白色（#FFFFFF）各國機構成稱 */
        .metric-label {
            color: #FFFFFF !important;
            font-size: 14px !important;
            font-weight: bold !important;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }
        .metric-value {
            color: #00FFCC !important;
            font-size: 22px !important;
            font-weight: bold !important;
        }
        /* 🗺️ 地圖區自訂右側 7 國顏色圖例面板 */
        .map-container {
            position: relative;
        }
        .legend-panel {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(15, 23, 42, 0.85);
            border: 1px solid #475569;
            padding: 12px;
            border-radius: 6px;
            z-index: 999;
            color: #ffffff;
            font-size: 12px;
            font-family: monospace;
            box-shadow: 0 4px 6px rgba(0,0,0,0.5);
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 4px;
        }
        .legend-color {
            width: 30px;
            height: 4px;
            margin-right: 8px;
            border-radius: 2px;
        }
        iframe {border-radius: 8px;}
        .stPydeckChart {height: 450px !important; border-radius: 8px; overflow: hidden; background-color: #0f172a;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式颱風侵台概率動態監測系統")

# --- 🎯 3. 7 國機構 × 5 天完整預報軌跡資料庫 ---
# 座標點依序為：[0天當前, 1天預報, 2天預報, 3天預報, 4天預報, 5天預報]
REAL_TIME_DATA = [
    {
        "id": "WP082026", 
        "name_zh": "第08號 無花果颱風", 
        "name_en": "HIGOS", 
        "lat": 15.8, "lon": 142.0, 
        "probs": {"CWA": 10.0, "NCDR": 8.0, "ECMWF": 15.0, "JTWC": 12.0, "JMA": 14.5, "HKO": 9.0, "NMC": 11.0},
        "paths": [
            {"name": "CWA 台灣 (鮮紅)", "color": [255, 59, 48], "path": [[142.0, 15.8], [139.5, 16.5], [137.0, 18.0], [134.2, 20.1], [131.5, 22.5], [128.0, 25.0]]},
            {"name": "NCDR 災害中心 (鮮橙)", "color": [255, 149, 0], "path": [[142.0, 15.8], [139.8, 16.2], [137.5, 17.5], [135.0, 19.5], [132.8, 21.8], [129.5, 24.2]]},
            {"name": "ECMWF 歐洲 (發光黃)", "color": [255, 214, 10], "path": [[142.0, 15.8], [139.2, 16.8], [136.2, 18.5], [133.0, 21.0], [129.8, 24.0], [126.5, 27.2]]},
            {"name": "JTWC 美軍 (發光綠)", "color": [52, 211, 153], "path": [[142.0, 15.8], [140.0, 16.0], [138.0, 17.0], [135.8, 18.8], [133.5, 21.0], [131.0, 23.5]]},
            {"name": "JMA 日本 (正青色)", "color": [0, 199, 190], "path": [[142.0, 15.8], [139.6, 16.4], [136.8, 17.8], [133.8, 19.8], [130.5, 22.0], [127.2, 24.5]]},
            {"name": "HKO 香港 (螢光藍)", "color": [0, 122, 255], "path": [[142.0, 15.8], [139.4, 16.3], [136.9, 17.7], [134.0, 19.6], [131.0, 21.8], [127.8, 24.0]]},
            {"name": "NMC 中國 (霓虹紫)", "color": [175, 82, 222], "path": [[142.0, 15.8], [139.7, 16.6], [137.2, 18.2], [134.5, 20.5], [132.0, 23.2], [128.8, 26.0]]}
        ]
    },
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉颱風", 
        "name_en": "MEKKHALA", 
        "lat": 22.5, "lon": 126.8, 
        "probs": {"CWA": 5.0, "NCDR": 4.1, "ECMWF": 8.0, "JTWC": 4.5, "JMA": 9.2, "HKO": 5.0, "NMC": 6.1},
        "paths": [
            {"name": "CWA 台灣 (鮮紅)", "color": [255, 59, 48], "path": [[126.8, 22.5], [125.8, 24.0], [125.0, 25.8], [124.5, 27.5], [124.2, 29.5], [124.0, 31.5]]},
            {"name": "NCDR 災害中心 (鮮橙)", "color": [255, 149, 0], "path": [[126.8, 22.5], [125.5, 23.8], [124.6, 25.2], [124.0, 26.8], [123.6, 28.5], [123.5, 30.2]]},
            {"name": "ECMWF 歐洲 (發光黃)", "color": [255, 214, 10], "path": [[126.8, 22.5], [126.0, 24.2], [125.5, 26.2], [125.2, 28.5], [125.0, 31.0], [125.1, 33.5]]},
            {"name": "JTWC 美軍 (發光綠)", "color": [52, 211, 153], "path": [[126.8, 22.5], [125.2, 23.6], [123.9, 24.8], [122.8, 26.2], [121.8, 27.8], [121.0, 29.5]]},
            {"name": "JMA 日本 (正青色)", "color": [0, 199, 190], "path": [[126.8, 22.5], [125.6, 23.9], [124.8, 25.5], [124.2, 27.2], [123.9, 29.0], [123.8, 30.8]]},
            {"name": "HKO 香港 (螢光藍)", "color": [0, 122, 255], "path": [[126.8, 22.5], [125.4, 23.7], [124.4, 25.0], [123.7, 26.5], [123.2, 28.2], [123.0, 30.0]]},
            {"name": "NMC 中國 (霓虹紫)", "color": [175, 82, 222], "path": [[126.8, 22.5], [125.7, 24.1], [124.9, 25.9], [124.4, 27.8], [124.1, 29.8], [124.0, 31.8]]}
        ]
    }
]

# --- 4. 空間距離計算與選單聯動 ---
active_systems = []
for sys in REAL_TIME_DATA:
    dist = calc_haversine(TW_LAT, TW_LON, sys["lat"], sys["lon"])
    sys["distance"] = dist
    active_systems.append(sys)

options = [f"🌀 {s['name_zh']} ({s['name_en']}) - 距台 {s['distance']} KM" for s in active_systems]
selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
selected_idx = options.index(selected_option)
current_sys = active_systems[selected_idx]

p_dict = current_sys["probs"]
avg_yong_prob = round(sum(p_dict.values()) / len(p_dict), 1)

# --- 🌍 5. 頂部高強度 HTML 橫幅（各國字體全白粗體） ---
banner_html = f"""
<div class="dashboard-banner">
    <div class="metric-card"><div class="metric-label">CWA 台灣</div><div class="metric-value">{p_dict['CWA']}%</div></div>
    <div class="metric-card"><div class="metric-label">NCDR 災害</div><div class="metric-value">{p_dict['NCDR']}%</div></div>
    <div class="metric-card"><div class="metric-label">ECMWF 歐洲</div><div class="metric-value">{p_dict['ECMWF']}%</div></div>
    <div class="metric-card"><div class="metric-label">JTWC 美軍</div><div class="metric-value">{p_dict['JTWC']}%</div></div>
    <div class="metric-card"><div class="metric-label">JMA 日本</div><div class="metric-value">{p_dict['JMA']}%</div></div>
    <div class="metric-card"><div class="metric-label">HKO 香港</div><div class="metric-value">{p_dict['HKO']}%</div></div>
    <div class="metric-card"><div class="metric-label">NMC 中國</div><div class="metric-value">{p_dict['NMC']}%</div></div>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

# 勇式綜合戰情警告燈號
if avg_yong_prob > 40:
    st.error(f"🚨 【勇式總體侵台綜合概率】危險級： {avg_yong_prob} % （系統監測：{current_sys['name_zh']} 距台 {current_sys['distance']} 公里，高度戒備！）")
elif avg_yong_prob > 15:
    st.warning(f"⚠️ 【勇式總體侵台綜合概率】關注級： {avg_yong_prob} % （系統監測：{current_sys['name_zh']} 距台 {current_sys['distance']} 公里，監控發展。）")
else:
    st.success(f"🍏 【勇式總體侵台綜合概率】安全級： {avg_yong_prob} % （系統判定：{current_sys['name_zh']} 距台 {current_sys['distance']} 公里，無直接威脅。）")

# --- 6. 下方分欄 ---
map_col, radar_col = st.columns([5, 5])

with map_col:
    # 使用容器包裝地圖，以便插入絕對定位的 7 國圖例
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    
    # 打造 7 國獨立的預報線路圖層
    layers = []
    df_paths = pd.DataFrame(current_sys["paths"])
    
    for _, row in df_paths.iterrows():
        layers.append(pdk.Layer(
            "PathLayer",
            pd.DataFrame([row.to_dict()]),
            get_path="path",
            get_color="color",
            width_scale=6,
            width_min_pixels=3,
            get_width=5
        ))
    
    # 基準點與定位點圖層
    poi_data = [
        {"label": "TAIWAN 台灣中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255]},
        {"label": f"中心定位: {current_sys['name_zh']}", "lon": current_sys["lon"], "lat": current_sys["lat"], "size": 45000, "color": [255, 255, 255]}
    ]
    df_poi = pd.DataFrame(poi_data)
    
    layers.append(pdk.Layer(
        "ScatterplotLayer", df_poi, get_position=["lon", "lat"],
        get_radius="size", get_fill_color="color"
    ))
    layers.append(pdk.Layer(
        "TextLayer", df_poi, get_position=["lon", "lat"], get_text="label",
        get_color=[248, 250, 252], get_size=15, get_alignment_baseline="'bottom'"
    ))
    
    # 視野高度最佳化（容納 5 天後的長距離路徑）
    view_state = pdk.ViewState(latitude=TW_LAT - 4, longitude=TW_LON + 6, zoom=3.3, pitch=0)
    
    # 渲染 Pydeck 地圖
    st.pydeck_chart(pdk.Deck(
        map_provider=None, map_style=None,
        initial_view_state=view_state, layers=layers
    ), use_container_width=True)
    
    # 🔑 戰情室核心：直接用網頁 CSS 灌入 7 國專屬顏色圖例，杜絕標記不清！
    legend_html = """
    <div class="legend-panel">
        <div style="font-weight:bold; margin-bottom:6px; border-bottom:1px solid #475569; padding-bottom:2px;">7國路徑圖例 (5天預報)</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(255,59,48);"></div>CWA 台灣</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(255,149,0);"></div>NCDR 災害中心</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(255,214,10);"></div>ECMWF 歐洲</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(52,211,153);"></div>JTWC 美軍</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(0,199,190);"></div>JMA 日本</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(0,122,255);"></div>HKO 香港</div>
        <div class="legend-item"><div class="legend-color" style="background-color:rgb(175,82,222);"></div>NMC 中國</div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with radar_col:
    # Windy 嵌入組件高度同步對齊
    windy_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={current_sys['lat']}&lon={current_sys['lon']}"
    st.components.v1.iframe(windy_url, width=None, height=450, scrolling=False)
