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

# 強力修正暗黑模式下的字體顏色，確保絕對看得見
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
        /* 強制將各國機構名稱（Label）改為純白色 */
        div[data-testid="stMetricLabel"] > div { 
            color: #ffffff !important; 
            font-weight: bold !important;
            font-size: 14px !important;
        }
        /* 強制將機率數值（Value）改為亮眼綠色 */
        div[data-testid="stMetricValue"] > div { 
            color: #34d399 !important; 
        }
        iframe {border-radius: 8px;}
        .stPydeckChart {height: 420px !important; border-radius: 8px; overflow: hidden; background-color: #0f172a;}
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式颱風侵台概率動態監測系統")

# --- 2. 側邊欄：實時多源數據輸入面板 (徹底杜絕 AI 瞎編數據) ---
st.sidebar.header("📥 各國實時觀測數據輸入")
sys_name = st.sidebar.text_input("🌀 熱帶系統名稱/代號：", value="熱帶擾動 94W")
current_lat = st.sidebar.number_input("📍 當前中心北緯 (Lat)：", min_value=0.0, max_value=50.0, value=12.5, step=0.1)
current_lon = st.sidebar.number_input("📍 當前中心東經 (Lon)：", min_value=100.0, max_value=160.0, value=132.0, step=0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("🔮 各國初始預報侵台率 (%)")
p_cwa = st.sidebar.slider("CWA 台灣", 0, 100, 45)
p_ncdr = st.sidebar.slider("NCDR 災害中心", 0, 100, 38)
p_ec = st.sidebar.slider("ECMWF 歐洲", 0, 100, 52)
p_jt = st.sidebar.slider("JTWC 美軍", 0, 100, 40)
p_jm = st.sidebar.slider("JMA 日本", 0, 100, 42)
p_hk = st.sidebar.slider("HKO 香港", 0, 100, 39)
p_nm = st.sidebar.slider("NMC 中國", 0, 100, 43)

# --- 3. 核心空間計算與動態概率衰減演算法 ---
dist = calc_haversine(TW_LAT, TW_LON, current_lat, current_lon)

# 依據與台灣的真實距離，即時動態計算「衰減權重」，距離超過 1000 公里概率自動歸零或暴跌
if dist > 1000.0:
    st.sidebar.error(f"⚠️ 該系統距離台灣 {dist} KM，已超過 1000KM 安全防禦圍欄！")
    decay_factor = max(0.0, 1.0 - ((dist - 1000) / 300)) # 超過千公里快速衰減
else:
    st.sidebar.success(f"🎯 該系統距離台灣 {dist} KM，納入 1000KM 核心防禦圈。")
    decay_factor = 1.0

# 應用動態衰減到各國數據上
dynamic_probs = {
    "CWA": round(p_cwa * decay_factor, 1),
    "NCDR": round(p_ncdr * decay_factor, 1),
    "ECMWF": round(p_ec * decay_factor, 1),
    "JTWC": round(p_jt * decay_factor, 1),
    "JMA": round(p_jm * decay_factor, 1),
    "HKO": round(p_hk * decay_factor, 1),
    "NMC": round(p_nm * decay_factor, 1)
}

avg_yong_prob = round(sum(dynamic_probs.values()) / len(dynamic_probs), 1)

# --- 🌍 橫幅橫跨頂部 (Top Banner Metrics) ---
m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7 = st.columns(7)
with m_col1: st.metric("CWA 台灣", f"{dynamic_probs['CWA']}%")
with m_col2: st.metric("NCDR 災害", f"{dynamic_probs['NCDR']}%")
with m_col3: st.metric("ECMWF 歐洲", f"{dynamic_probs['ECMWF']}%")
with m_col4: st.metric("JTWC 美軍", f"{dynamic_probs['JTWC']}%")
with m_col5: st.metric("JMA 日本", f"{dynamic_probs['JMA']}%")
with m_col6: st.metric("HKO 香港", f"{dynamic_probs['HKO']}%")
with m_col7: st.metric("NMC 中國", f"{dynamic_probs['NMC']}%")

# 根據動態概率進行科學判定
if avg_yong_prob > 50:
    st.error(f"🚨 【勇式總體侵台綜合概率】危險級： {avg_yong_prob} % （系統偵測：{sys_name} 距台 {dist} 公里，高度戒備！）")
elif avg_yong_prob > 15:
    st.warning(f"⚠️ 【勇式總體侵台綜合概率】關注級： {avg_yong_prob} % （系統偵測：{sys_name} 距台 {dist} 公里，密切監控發展。）")
else:
    st.success(f"🍏 【勇式總體侵台綜合概率】安全級： {avg_yong_prob} % （系統判定：{sys_name} 距台 {dist} 公里，無直接威脅。）")

# --- 4. 下方分欄 ---
map_col, radar_col = st.columns([5, 5])

with map_col:
    # 依據輸入座標自動生成模擬趨勢線
    lines_data = [
        {"name": "預報趨勢趨向線", "color": [0, 254, 204], "path": [[current_lon, current_lat], [TW_LON, TW_LAT]]}
    ]
    
    poi_data = [
        {"label": "TAIWAN 台灣中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255]},
        {"label": f"中心實時定位: {sys_name}", "lon": current_lon, "lat": current_lat, "size": 45000, "color": [255, 59, 48]}
    ]
    
    df_poi = pd.DataFrame(poi_data)
    df_lines = pd.DataFrame(lines_data)
    
    # 視野自動鎖定在台灣與氣旋的中間點
    view_state = pdk.ViewState(
        latitude=(TW_LAT + current_lat) / 2, 
        longitude=(TW_LON + current_lon) / 2, 
        zoom=3.5, pitch=0
    )
    
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
    # Windy 嵌入組件（會隨著您在左側輸入的真實座標自動跟隨、定位！）
    windy_url = f"https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=default&metricWind=default&zoom=4&overlay=wind&product=ecmwf&level=surface&lat={current_lat}&lon={current_lon}"
    st.components.v1.iframe(windy_url, width=None, height=420, scrolling=False)
