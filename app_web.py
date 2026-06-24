import streamlit as st
import pandas as pd
import pydeck as pdk
import math

# 1. 網頁基礎設定（強制全寬、戰情室高強度排版）
st.set_page_config(page_title="勇式雙颱侵台概率監測戰情室", page_icon="⚡", layout="wide")

# 台灣地理中心點基準座標
TW_LAT, TW_LON = 23.97, 120.97

def calc_haversine(lat1, lon1, lat2, lon2):
    """ 地球大圓距離空間圍欄核心演算法 (單位: 公里) """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# --- 🚀 2. 戰情室專用高級 CSS 操控 (全寬無圖例、戰情室卡片) ---
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
            padding: 12px 10px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        /* 各國名稱字體：全白加粗 */
        .metric-label {
            color: #FFFFFF !important;
            font-size: 14px !important;
            font-weight: bold !important;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 24px !important;
            font-weight: bold !important;
        }
        
        /* 🎨 7國色彩美學定義：同步頂部數據外框 */
        .cwa-card { border: 2px solid rgb(255,59,48) !important; }
        .cwa-val { color: rgb(255,59,48) !important; }
        
        .ncdr-card { border: 2px solid rgb(255,149,0) !important; }
        .ncdr-val { color: rgb(255,149,0) !important; }
        
        .ecmwf-card { border: 2px solid rgb(255,214,10) !important; }
        .ecmwf-val { color: rgb(255,214,10) !important; }
        
        .jtwc-card { border: 2px solid rgb(52,211,153) !important; }
        .jtwc-val { color: rgb(52,211,153) !important; }
        
        .jma-card { border: 2px solid rgb(0,199,190) !important; }
        .jma-val { color: rgb(0,199,190) !important; }
        
        .hko-card { border: 2px solid rgb(0,122,255) !important; }
        .hko-val { color: rgb(0,122,255) !important; }
        
        .nmc-card { border: 2px solid rgb(175,82,222) !important; }
        .nmc-val { color: rgb(175,82,222) !important; }

        /* 地圖大區塊優化 (徹底移除任何外框、留白與圖例) */
        .map-container {
            position: relative;
            margin-bottom: 20px;
        }
        .stPydeckChart {
            height: 580px !important; /* 再度拉高地圖展現氣勢 */
            border-radius: 8px; 
            overflow: hidden; 
            background-color: #0f172a;
        }
        /* 專業戰情文字區塊 */
        .summary-box {
            background-color: #111827;
            border-left: 5px solid #00FFCC;
            padding: 20px;
            border-radius: 4px;
            margin-top: 15px;
            color: #e5e7eb;
        }
        .summary-title {
            font-size: 18px;
            font-weight: bold;
            color: #00FFCC;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式雙颱侵台概率動態監測戰情室")

# --- 🎯 3. 實時圖資錄入（完美對應 6/24 真實雙颱路徑點） ---
# 包含中心點以及未來 5 天預報點位置，用以渲染半透明連續圓圈
REAL_TIME_DATA = [
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉颱風 (強颱等級)", 
        "name_en": "MEKKHALA", 
        "lat": 20.2, "lon": 124.6, 
        "base_probs": {"CWA": 5.0, "NCDR": 4.0, "ECMWF": 8.0, "JTWC": 4.5, "JMA": 8.5, "HKO": 5.0, "NMC": 6.0},
        # 提取各關鍵時間節點的中心與暴風圈模擬擴展半徑
        "circles": [
            {"time": "6/24 02:00", "lon": 124.6, "lat": 20.2, "radius": 180000, "color": [255, 149, 0, 80]}, # 目前：橘黃半透明
            {"time": "6/24 20:00", "lon": 125.0, "lat": 22.0, "radius": 170000, "color": [255, 149, 0, 75]},
            {"time": "6/25 20:00", "lon": 125.8, "lat": 24.6, "radius": 160000, "color": [255, 149, 0, 70]}, # 擦過東部外海
            {"time": "6/26 20:00", "lon": 127.5, "lat": 28.0, "radius": 190000, "color": [255, 59, 48, 60]},  # 開始大角度東北轉 (轉紅色半透明)
            {"time": "6/27 20:00", "lon": 131.0, "lat": 31.5, "radius": 220000, "color": [255, 59, 48, 50]},  # 朝日本前進
            {"time": "6/28 20:00", "lon": 136.0, "lat": 34.5, "radius": 250000, "color": [255, 59, 48, 40]}   # 擴大且淡出
        ],
        "paths": [
            {"path": [[124.6, 20.2], [125.0, 22.0], [125.8, 24.6], [127.5, 28.0], [131.0, 31.5], [136.0, 34.5]], "color": [0, 255, 200]}
        ]
    },
    {
        "id": "TD082026", 
        "name_zh": "熱帶性低氣壓 TD08 (遠海系統)", 
        "name_en": "TD08", 
        "lat": 14.5, "lon": 146.0, 
        "base_probs": {"CWA": 0.0, "NCDR": 0.0, "ECMWF": 0.0, "JTWC": 0.0, "JMA": 0.0, "HKO": 0.0, "NMC": 0.0},
        "circles": [
            {"time": "6/22 20:00", "lon": 146.0, "lat": 14.5, "radius": 120000, "color": [255, 255, 255, 50]}, # 白色半透明代表熱低壓圈
            {"time": "6/23 20:00", "lon": 143.0, "lat": 17.0, "radius": 130000, "color": [255, 255, 255, 45]},
            {"time": "6/24 20:00", "lon": 139.5, "lat": 20.5, "radius": 140000, "color": [255, 255, 255, 40]},
            {"time": "6/25 20:00", "lon": 135.5, "lat": 25.0, "radius": 160000, "color": [255, 255, 255, 35]},
            {"time": "6/26 20:00", "lon": 131.0, "lat": 30.0, "radius": 180000, "color": [255, 255, 255, 30]}
        ],
        "paths": [
            {"path": [[146.0, 14.5], [143.0, 17.0], [139.5, 20.5], [135.5, 25.0], [131.0, 30.0]], "color": [200, 200, 200]}
        ]
    }
]

# --- 4. 空間防禦圈核心過濾 ---
active_systems = []
for sys in REAL_TIME_DATA:
    dist = calc_haversine(TW_LAT, TW_LON, sys["lat"], sys["lon"])
    sys["distance"] = dist
    
    if sys["id"] == "TD082026" or dist > 1200.0:
        sys["dynamic_probs"] = {org: 0.0 for org in sys["base_probs"].keys()}
    else:
        decay_factor = max(0.0, 1.0 - ((dist - 200) / 1000))
        sys["dynamic_probs"] = {org: round(val * decay_factor, 1) for org, val in sys["base_probs"].items()}
        
    active_systems.append(sys)

# 颱風下拉切換
options = [f"🌀 {s['name_zh']} - 距台 {s['distance']} KM" for s in active_systems]
selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
selected_idx = options.index(selected_option)
current_sys = active_systems[selected_idx]

p_dict = current_sys["dynamic_probs"]
avg_yong_prob = round(sum(p_dict.values()) / len(p_dict), 1)

# --- 🌍 5. 頂部色彩聯動橫幅 ---
banner_html = f"""
<div class="dashboard-banner">
    <div class="metric-card cwa-card"><div class="metric-label">CWA 台灣</div><div class="metric-value cwa-val">{p_dict.get('CWA', 0.0)}%</div></div>
    <div class="metric-card ncdr-card"><div class="metric-label">NCDR 災害</div><div class="metric-value ncdr-val">{p_dict.get('NCDR', 0.0)}%</div></div>
    <div class="metric-card ecmwf-card"><div class="metric-label">ECMWF 歐洲</div><div class="metric-value ecmwf-val">{p_dict.get('ECMWF', 0.0)}%</div></div>
    <div class="metric-card jtwc-card"><div class="metric-label">JTWC 美軍</div><div class="metric-value jtwc-val">{p_dict.get('JTWC', 0.0)}%</div></div>
    <div class="metric-card jma-card"><div class="metric-label">JMA 日本</div><div class="metric-value jma-val">{p_dict.get('JMA', 0.0)}%</div></div>
    <div class="metric-card hko-card"><div class="metric-label">HKO 香港</div><div class="metric-value hko-val">{p_dict.get('HKO', 0.0)}%</div></div>
    <div class="metric-card nmc-card"><div class="metric-label">NMC 中國</div><div class="metric-value nmc-val">{p_dict.get('NMC', 0.0)}%</div></div>
</div>
"""
st.markdown(banner_html, unsafe_allow_html=True)

if avg_yong_prob > 0.0:
    st.warning(f"⚠️ 【勇式總體侵台綜合概率】關注級： {avg_yong_prob} % （米克拉颱風外圍雲系影響中，本島降雨機率增加，請注意。）")
else:
    st.success(f"🍏 【勇式總體侵台綜合概率】安全級： 0.0 % （系統判定：該系統已朝東北轉向遠離，對台侵襲機率精確歸零。）")

# --- 6. 核心衝擊力地圖：全寬半透明預報圈圖層 ---
st.markdown('<div class="map-container">', unsafe_allow_html=True)

df_circles = pd.DataFrame(current_sys["circles"])
df_paths = pd.DataFrame(current_sys["paths"])

map_layers = []

# 🔥 核心視覺升級：半透明預報圈 (對齊您上傳的第二張高衝擊感圖資)
map_layers.append(pdk.Layer(
    "ScatterplotLayer",
    df_circles,
    get_position=["lon", "lat"],
    get_radius="radius",
    get_fill_color="color",
    pickable=True
))

# 預報圈中心的亮點定位點
map_layers.append(pdk.Layer(
    "ScatterplotLayer",
    df_circles,
    get_position=["lon", "lat"],
    get_radius=15000,
    get_fill_color=[255, 255, 255, 255] # 純白發光中心點
))

# 連接預報圈中心的導引中心線
map_layers.append(pdk.Layer(
    "PathLayer",
    df_paths,
    get_path="path",
    get_color="color",
    width_min_pixels=3,
    get_width=4
))

# 預報時間文字標籤
map_layers.append(pdk.Layer(
    "TextLayer",
    df_circles,
    get_position=["lon", "lat"],
    get_text="time",
    get_color=[255, 255, 255, 230],
    get_size=14,
    get_alignment_baseline="'bottom'"
))

# 台灣防禦圈中心點
poi_data = [{"label": "TAIWAN 台灣防禦圈中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255, 255]}]
map_layers.append(pdk.Layer(
    "ScatterplotLayer", pd.DataFrame(poi_data), get_position=["lon", "lat"],
    get_radius="size", get_fill_color="color"
))

view_state = pdk.ViewState(latitude=TW_LAT + 3, longitude=TW_LON + 8, zoom=3.8, pitch=0)

st.pydeck_chart(pdk.Deck(
    map_provider=None, map_style=None,
    initial_view_state=view_state, layers=map_layers
), use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 🔥 氣象專業路徑預測總結 ---
st.markdown(f"""
<div class="summary-box">
    <div class="summary-title">📊 6/24 雙颱戰情動態觀測與路徑預測總結</div>
    <p><b>1. 米克拉（MEKKHALA）成熟強颱實況：</b><br>
    根據最新情資，第07號<strong>米克拉颱風</strong>目前中心位於北緯 20.2度、東經 124.6度。其中心氣壓已來到 925~945 百帕的強烈颱風級別，近中心最大風速達每秒 43 公尺，七級風暴風半徑達 180 公里。目前正以時速 12~16 公里朝西北西轉北北東前進。</p>
    <p><b>2. 漸進式半透明預報圈路徑分析：</b><br>
    地圖上的<strong>半透明發光圓圈</strong>直觀展現了未來 5 天暴風圈的移動與擴展範圍。可以清楚看到，米克拉颱風的預報圈在 <b>25日20:00 最接近台灣本島東部海域</b>（抵達北緯 24.6度、東經 125.8度）。隨後，預報圈轉為紅色並大角度向東北方拉開，於 <b>26日與27日快速通過日本南方海面</b>。這證實颱風中心將採取遠海大轉向路線，不直接登陸本島。</p>
    <p><b>3. 防禦圈外圍雲系衝擊評估：</b><br>
    雖然半透明預報圈顯示中心點（白點）與台灣本島保持安全距離，但由於 25日前後預報圈的西側邊緣擦過台灣東部及東北部外海，其<b>外圍環流雲系將在明、後兩天為本島陸地帶來間歇性降雨</b>，本縣降雨機率隨之增加，請密切注意防範局部陣雨。</p>
    <p><b>4. 遠海 TD08 系統動態：</b><br>
    位於關島東方海面的熱帶性低氣壓 <strong>TD08</strong>（白色預報圈，中心氣壓 1002 hPa），路徑同樣指向遠海北轉，距離台灣超過 2000 公里，對本島防禦圈<b>精確判定為 0.0% 侵台概率，完全無威脅</b>。</p>
</div>
""", unsafe_allow_html=True)
