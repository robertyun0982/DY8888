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

# --- 🎯 2. 實時動態數據庫 (開放式架構：您可隨時依據網上最新數據修改此處) ---
REAL_TIME_DATA = [
    {
        "id": "94W", 
        "name_zh": "熱帶擾動 94W", 
        "name_en": "INVEST 94W", 
        "lat": 12.5, "lon": 132.0,  # 👈 網上查到最新經緯度可直接改這裡
        # 👇 網上查到各國最新的真實侵台機率，直接改這裡
        "probs": {"CWA": 45.0, "NCDR": 38.0, "ECMWF": 52.0, "JTWC": 40.0, "JMA": 41.5, "HKO": 39.0, "NMC": 43.0},
        "paths": {
            "CWA": [[132.0, 12.5], [130.5, 14.2], [128.8, 16.5], [127.0, 19.0]],
            "ECMWF": [[132.0, 12.5], [130.0, 14.5], [128.0, 17.0], [125.8, 19.8]],
            "JTWC": [[132.0, 12.5], [130.8, 14.0], [129.2, 16.0], [127.8, 18.2]]
        }
    },
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉", 
        "name_en": "MEKKHALA", 
        "lat": 26.5, "lon": 128.5,  # 👈 已移至沖繩附近
        "probs": {"CWA": 2.5, "NCDR": 1.1, "ECMWF": 4.0, "JTWC": 1.5, "JMA": 5.2, "HKO": 2.0, "NMC": 3.1},
        "paths": {
            "CWA": [[124.7, 19.1], [125.5, 21.0], [126.8, 23.5], [128.5, 26.5]],
            "ECMWF": [[124.7, 19.1], [125.8, 21.2], [127.2, 23.8], [128.9, 26.8]],
            "JTWC": [[124.7, 19.1], [126.0, 21.5], [127.5, 24.0], [129.2, 27.0]]
        }
    }
]

# --- 🚀 3. 戰情室專用高級 CSS 操控 ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 0px !important; 
            max-width: 1400px !important; 
            margin: 0 auto;
        }
        /* 🛠️ 終極修復：自訂網頁頂部橫幅 HTML 方格樣式，徹底亮白字體 */
        .dashboard-banner {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 15px;
        }
        .metric-card {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            padding: 12px 10px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        /* 🔑 機構名稱：強制鎖定純白色，解決顏色相近看不清的問題 */
        .metric-label {
            color: #FFFFFF !important;
            font-size: 14px !important;
            font-weight: 200 !important;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }
        /* 機率數值：發光亮綠色 */
        .metric-value {
            color: #00ffaa !important;
            font-size: 22px !important;
            font-weight: bold !important;
        }
        iframe {border-radius: 8px;}
        .stPydeckChart {height: 380px !important; border-radius: 8px; overflow: hidden; background-color: #0f172a;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式颱風侵台概率動態監測系統")

# --- 4. 空間過欄計算與選單生成 ---
active_systems = []
for sys in REAL_TIME_DATA:
    dist = calc_haversine(TW_LAT, TW_LON, sys["lat"], sys["lon"])
    sys["distance"] = dist
    active_systems.append(sys)

# 颱風/擾動切換選單
options = [f"🌀 {s['name_zh']} ({s['name_en']}) - 距台 {s['distance']} KM" for s in active_systems]
selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
selected_idx = options.index(selected_option)
current_sys = active_systems[selected_idx]

p_dict = current_sys["probs"]
avg_yong_prob = round(sum(p_dict.values()) / len(p_dict), 1)

# --- 🌍 5. 自訂純 HTML 橫幅（解決原生組件字體看不清的硬傷） ---
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
    st.error(f"🚨 【勇式總體侵台綜合概率】危險級： {avg_yong_prob} % （系統偵測：{current_sys['name_zh']} 距台 {current_sys['distance']} 公里，高度戒備！）")
elif avg_yong_prob > 10:
    st.warning(f"⚠️ 【勇式總體侵台綜合概率】關注級： {avg_yong_prob} % （系統偵測：{current_sys['name_zh']} 距台 {current_sys['distance']} 公里，監控發展。）")
else:
    st.success(f"🍏 【勇式總體侵台綜合概率】安全級： {avg_yong_prob} % （系統判定：{current_sys['name_zh']} 距台 {current_sys['distance']} 公里，無直接威脅。）")

# --- 6. 下方分欄：左側暗黑雷達軌跡，右側 Windy 實時流場 ---
map_col, radar_col = st.columns([5, 5])

with map_col:
    lines_data = [
        {"name": "CWA (黃)", "color": [255, 192, 0], "path": current_sys["paths"]["CWA"]},
        {"name": "ECMWF (青)", "color": [0, 204, 204], "path": current_sys["paths"]["ECMWF"]},
        {"name": "JTWC (橘)", "color": [255, 102, 0], "path": current_sys["paths"]["JTWC"]}
    ]
    
    poi_data = [
        {"label": "TAIWAN 台灣中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255]},
        {"label": f"中心定位: {current_sys['name_zh']}", "lon": current_sys["lon"], "lat": current_sys["lat"], "size": 45000, "color": [255, 59, 48]}
    ]
    
    df_poi = pd.DataFrame(poi_data)
    df_lines = pd.DataFrame(lines_data)
    
    # 視野動態縮放
    view_state = pdk.ViewState(latitude=TW_LAT - 3, longitude=TW_LON + 4, zoom=3.8, pitch=0)
    
    line_layer = pdk.Layer(
        "PathLayer", df_lines, get_path="path", get_color="color",
        width_scale=6, width_min_pixels=2, get_width=4
    )
    
    scatter_layer = pdk.Layer(
        "ScatterplotLayer", df_poi, get_position=["lon", "lat"],
        get_radius="size", get_fill_color="color"
    )
    
    text_layer = pdk.Layer(
        "TextLayer", df_poi, get_position=["lon", "lat"], get_text="label",
        get_color=[248, 250, 252], get_size=16, get_alignment_baseline="'bottom'"
    )
    
    st.pydeck_chart(pdk.Deck(
        map_provider=None,
        map_style=None,
        initial_view_state=view_state,
        layers=[line_layer, scatter_layer, text_layer]
    ), use_container_width=True)

with radar_col:
    # Windy 雷達會隨著選單切換（7號或94W）自動定位到對應的經緯度中心
    windy_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={current_sys['lat']}&lon={current_sys['lon']}"
    st.components.v1.iframe(windy_url, width=None, height=380, scrolling=False)
