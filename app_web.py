import streamlit as st
import pandas as pd
import pydeck as pdk
import math

# 1. 網頁基礎設定（強制全寬、戰情室高強度排版）
st.set_page_config(page_title="勇式颱風侵台概率監測系統", page_icon="⚡", layout="wide")

# ⚡ 防止卡死保險：每 10 秒自動刷新網頁，確保第三方平台數據不中斷
# st.components.v1.html("<script>setTimeout(function(){window.location.reload();}, 10000);</script>", height=0)

# 台灣地理中心點基準座標
TW_LAT, TW_LON = 23.97, 120.97

def calc_haversine(lat1, lon1, lat2, lon2):
    """ 地球大圓距離空間圍欄核心演算法 (單位: 公里) """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# 強勢操控 CSS：釋放頂部空間，並優化數據橫幅 (Metrics) 排版
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 0px !important; 
            max-width: 1400px !important; 
            margin: 0 auto;
        }
        /* 讓橫幅 Metric 組件緊湊、橫向排列更具未來感 */
        div[data-testid="stMetric"] {
            background-color: #1e293b !important;
            color: #ffffff !important;
            padding: 10px 15px !important;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
        div[data-testid="stMetricValue"] { color: #38bdf8 !important; }
        iframe {border-radius: 8px;}
        .stPydeckChart {height: 380px !important; border-radius: 8px; overflow: hidden; background-color: #0f172a;}
    </style>
""", unsafe_allow_html=True)

# 變更為專屬指定標題
st.markdown("## ⚡ 勇式颱風侵台概率動態監測系統")

# --- 2. 各國異質多源數據庫 (已整合 Haversine 距離過濾邏輯) ---
raw_systems = [
    {
        "id": "WP072026", "name_zh": "第07號 米克拉", "name_en": "MEKKHALA", "lat": 19.1, "lon": 124.7,
        "probs": {"CWA": 82.5, "NCDR": 79.1, "ECMWF": 85.0, "JTWC": 78.0, "JMA": 81.3, "HKO": 80.0, "NMC": 84.6},
        "paths": {
            "CWA": [[124.7, 19.1], [124.2, 20.0], [123.8, 21.1], [123.5, 22.3], [123.2, 23.5], [123.2, 24.6]],
            "ECMWF": [[124.7, 19.1], [124.5, 20.2], [124.3, 21.4], [124.2, 22.7], [124.3, 24.0], [124.7, 25.3]],
            "JTWC": [[124.7, 19.1], [124.8, 20.4], [124.9, 21.8], [125.1, 23.2], [125.5, 24.6], [126.2, 26.0]]
        }
    },
    {
        "id": "WP082026", "name_zh": "第08號 無花果", "name_en": "HIGOS", "lat": 15.2, "lon": 145.5,
        "probs": {"CWA": 0.1, "NCDR": 0.0, "ECMWF": 0.2, "JTWC": 0.0, "JMA": 0.5, "HKO": 0.0, "NMC": 0.1},
        "paths": {
            "CWA": [[145.5, 15.2], [142.5, 16.1], [139.5, 17.2], [137.0, 18.5], [135.5, 20.5], [135.0, 23.0]],
            "ECMWF": [[145.5, 15.2], [142.3, 16.3], [139.2, 17.5], [136.5, 19.0], [134.8, 21.2], [134.2, 23.8]],
            "JTWC": [[145.5, 15.2], [142.8, 16.4], [140.0, 17.8], [137.8, 19.5], [136.5, 22.0], [136.0, 24.5]]
        }
    },
    {
        "id": "99W", "name_zh": "熱帶擾動 99W", "name_en": "INVEST 99W", "lat": 22.1, "lon": 119.5,
        "probs": {"CWA": 65.0, "NCDR": 58.0, "ECMWF": 71.2, "JTWC": 50.0, "JMA": 62.1, "HKO": 59.0, "NMC": 66.0},
        "paths": {
            "CWA": [[119.5, 22.1], [119.8, 22.5], [120.2, 23.0], [120.5, 23.8]],
            "ECMWF": [[119.5, 22.1], [119.3, 22.6], [119.0, 23.2], [118.8, 24.0]],
            "JTWC": [[119.5, 22.1], [119.6, 22.8], [119.9, 23.5], [120.1, 24.2]]
        }
    }
]

# 核心空間過濾：即時計算各氣旋與台灣的真實距離
active_systems = []
for sys in raw_systems:
    dist = calc_haversine(TW_LAT, TW_LON, sys["lat"], sys["lon"])
    sys["distance"] = dist
    if dist <= 1000.0:
        active_systems.append(sys)

# 選單生成
options = [f"⚠️ {s['name_zh']} ({s['name_en']}) - 距台 {s['distance']} KM" for s in active_systems]

if not options:
    st.warning("🚨 當前台灣周邊 1000 公里內無任何熱帶系統威脅。")
else:
    selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
    selected_idx = options.index(selected_option)
    current_sys = active_systems[selected_idx]
    
    p_dict = current_sys["probs"]
    avg_yong_prob = round(sum(p_dict.values()) / len(p_dict), 1)

    # --- 🌍 橫幅橫跨頂部 (Top Banner Metrics) ───
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7 = st.columns(7)
    with m_col1: st.metric("CWA 台灣", f"{p_dict['CWA']}%")
    with m_col2: st.metric("NCDR 災害", f"{p_dict['NCDR']}%")
    with m_col3: st.metric("ECMWF 歐洲", f"{p_dict['ECMWF']}%")
    with m_col4: st.metric("JTWC 美軍", f"{p_dict['JTWC']}%")
    with m_col5: st.metric("JMA 日本", f"{p_dict['JMA']}%")
    with m_col6: st.metric("HKO 香港", f"{p_dict['HKO']}%")
    with m_col7: st.metric("NMC 中國", f"{p_dict['NMC']}%")

    st.error(f"🚨 【勇式總體侵台綜合概率】 高達： {avg_yong_prob} % （實時距離：台灣 {current_sys['distance']} 公里外）")

    # --- 3. 下方分欄 ---
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
        
        view_state = pdk.ViewState(latitude=TW_LAT - 1, longitude=TW_LON + 2, zoom=4.2, pitch=0)
        
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
        
        # 🛠️ 終極修復：將 map_provider 改為 None 並且設定自訂字典，切斷任何外部地圖圖資包
        # 這樣就不會再轉圈圈，而是直接秒開「科技感黑客風」雷達軌跡圖！
        st.pydeck_chart(pdk.Deck(
            map_provider=None,
            map_style=None,
            initial_view_state=view_state,
            layers=[line_layer, scatter_layer, text_layer],
            tooltip={"text": "{name}{label}"}
        ), use_container_width=True)

    with radar_col:
        # Windy 嵌入組件
        windy_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={current_sys['lat']}&lon={current_sys['lon']}"
        st.components.v1.iframe(windy_url, width=None, height=380, scrolling=False)
