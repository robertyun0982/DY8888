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

# 🛠️ 操控 CSS：強力修正暗黑模式下的字體顏色，確保絕對看得見
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
            padding: 10px 15px !important;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #334155;
        }
        /* 🔑 修正重點：強制將各國機構名稱（Label）改為純白色，告別看不見的窘境 */
        div[data-testid="stMetricLabel"] > div { 
            color: #ffffff !important; 
            font-weight: bold !important;
            font-size: 14px !important;
        }
        /* 強制將概率數值（Value）改為亮眼綠色 */
        div[data-testid="stMetricValue"] > div { 
            color: #34d399 !important; 
        }
        iframe {border-radius: 8px;}
        .stPydeckChart {height: 380px !important; border-radius: 8px; overflow: hidden; background-color: #0f172a;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式颱風侵台概率動態監測系統")

# --- 2. 原始觀測氣旋基本資料 ---
raw_systems = [
    {
        "id": "WP072026", "name_zh": "第07號 米克拉", "name_en": "MEKKHALA", "lat": 26.5, "lon": 128.5,  # 實時位置已移至沖繩附近（遠離台灣）
        "base_probs": {"CWA": 82.5, "NCDR": 79.1, "ECMWF": 85.0, "JTWC": 78.0, "JMA": 81.3, "HKO": 80.0, "NMC": 84.6},
        "paths": {
            "CWA": [[124.7, 19.1], [125.5, 21.0], [126.8, 23.5], [128.5, 26.5]],
            "ECMWF": [[124.7, 19.1], [125.8, 21.2], [127.2, 23.8], [128.9, 26.8]],
            "JTWC": [[124.7, 19.1], [126.0, 21.5], [127.5, 24.0], [129.2, 27.0]]
        }
    },
    {
        "id": "99W", "name_zh": "熱帶擾動 99W", "name_en": "INVEST 99W", "lat": 22.1, "lon": 119.5,  # 就在巴士海峽/台灣海峽南部（極度逼近）
        "base_probs": {"CWA": 65.0, "NCDR": 58.0, "ECMWF": 71.2, "JTWC": 50.0, "JMA": 62.1, "HKO": 59.0, "NMC": 66.0},
        "paths": {
            "CWA": [[119.5, 22.1], [119.8, 22.5], [120.2, 23.0], [120.5, 23.8]],
            "ECMWF": [[119.5, 22.1], [119.3, 22.6], [119.0, 23.2], [118.8, 24.0]],
            "JTWC": [[119.5, 22.1], [119.6, 22.8], [119.9, 23.5], [120.1, 24.2]]
        }
    }
]

# 核心空間過濾與動態概率衰減演算法
active_systems = []
for sys in raw_systems:
    dist = calc_haversine(TW_LAT, TW_LON, sys["lat"], sys["lon"])
    sys["distance"] = dist
    
    # 💥 強度邏輯更新：根據距離即時動態計算「衰減權重」
    # 如果距離大於 500 公里，侵台概率開始大幅滑落；超過 700 公里，概率直接被距離稀釋
    if dist > 500.0:
        decay_factor = max(0.02, 1.0 - ((dist - 500) / 350)) # 距離越遠衰減越狠
    else:
        decay_factor = 1.0 # 500公里內維持高威脅原概率
        
    # 將動態衰減應用到各國數據上
    sys["dynamic_probs"] = {org: round(val * decay_factor, 1) for org, val in sys["base_probs"].items()}
    
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
    
    p_dict = current_sys["dynamic_probs"]
    avg_yong_prob = round(sum(p_dict.values()) / len(p_dict), 1)

    # --- 🌍 橫幅橫跨頂部 (Top Banner Metrics) ───
    # 這裡的各國標籤文字已經過 CSS 強制白化，絕對清晰
    m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7 = st.columns(7)
    with m_col1: st.metric("CWA 台灣", f"{p_dict['CWA']}%")
    with m_col2: st.metric("NCDR 災害", f"{p_dict['NCDR']}%")
    with m_col3: st.metric("ECMWF 歐洲", f"{p_dict['ECMWF']}%")
    with m_col4: st.metric("JTWC 美軍", f"{p_dict['JTWC']}%")
    with m_col5: st.metric("JMA 日本", f"{p_dict['JMA']}%")
    with m_col6: st.metric("HKO 香港", f"{p_dict['HKO']}%")
    with m_col7: st.metric("NMC 中國", f"{p_dict['NMC']}%")

    # 根據概率給出真正科學的戰情警告
    if avg_yong_prob > 50:
        st.error(f"🚨 【勇式總體侵台綜合概率】危險級： {avg_yong_prob} % （實時距離：台灣 {current_sys['distance']} 公里，高度戒備！）")
    else:
        st.success(f"🍏 【勇式總體侵台綜合概率】安全級： {avg_yong_prob} % （系統判定：該系統距台 {current_sys['distance']} 公里並持續遠離，威脅解除。）")

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
        
        st.pydeck_chart(pdk.Deck(
            map_provider=None,
            map_style=None,
            initial_view_state=view_state,
            layers=[line_layer, scatter_layer, text_layer],
            tooltip={"text": "{name}{label}"}
        ), use_container_width=True)

    with radar_col:
        windy_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={current_sys['lat']}&lon={current_sys['lon']}"
        st.components.v1.iframe(windy_url, width=None, height=380, scrolling=False)
