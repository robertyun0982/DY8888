import streamlit as st
import pandas as pd
import pydeck as pdk
import math

# 1. 網頁基礎設定（強制全寬、戰情室高強度排版）
st.set_page_config(page_title="勇式雙颱侵台概率暨全台降雨監測戰情室", page_icon="⚡", layout="wide")

# 台灣地理中心點與屏東縣基準座標
TW_LAT, TW_LON = 23.97, 120.97
PT_LAT, PT_LON = 22.67, 120.49 # 屏東縣核心防禦點

def calc_haversine(lat1, lon1, lat2, lon2):
    """ 地球大圓距離空間圍欄核心演算法 (單位: 公里) """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# --- 🚀 2. 戰情室專用高級 CSS 操控 (精準控制左右版面高度與間距) ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.0rem !important; 
            padding-bottom: 0px !important; 
            max-width: 1480px !important; 
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
            padding: 10px 8px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .metric-label {
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: bold !important;
            margin-bottom: 4px;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 22px !important;
            font-weight: bold !important;
        }
        
        /* 🎨 7國色彩美學定義 */
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

        /* 地圖高度微調，確保與右側齊平 */
        .stPydeckChart {
            height: 520px !important; 
            border-radius: 8px; 
            overflow: hidden; 
            background-color: #0f172a;
        }
        
        /* 屏東在地災情專用看板 */
        .pingtung-box {
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
            border: 2px solid #38bdf8;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            color: #f8fafc;
        }
        .pingtung-title {
            font-size: 18px;
            font-weight: bold;
            color: #38bdf8;
            border-bottom: 1px solid #38bdf8;
            padding-bottom: 6px;
            margin-bottom: 10px;
        }
        
        /* 右側專業戰情文字區塊 - 高度自適應填滿 */
        .summary-box {
            background-color: #111827;
            border-left: 5px solid #00FFCC;
            padding: 18px;
            border-radius: 4px;
            color: #e5e7eb;
            height: 100%;
        }
        .summary-title {
            font-size: 18px;
            font-weight: bold;
            color: #00FFCC;
            margin-bottom: 12px;
        }
        .summary-box p {
            margin-bottom: 10px;
            line-height: 1.5;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式雙颱侵台概率暨動態降雨監測系統")

# --- 🎯 3. 實時雙颱與降雨圖資數據結構 ---
REAL_TIME_DATA = [
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉颱風 (強颱等級) - 注意外圍強降雨", 
        "name_en": "MEKKHALA", 
        "lat": 20.2, "lon": 124.6, 
        "base_probs": {"CWA": 3.2, "NCDR": 2.6, "ECMWF": 5.1, "JTWC": 2.9, "JMA": 5.4, "HKO": 3.2, "NMC": 3.8},
        "has_rain_threat": True,
        "rain_forecast": {
            "county": "屏東縣",
            "accumulated_5day": "180~280 mm",
            "rain_days": ["6/25 (四) 全天", "6/26 (五) 上半天"],
            "alert_level": "豪雨特報等級外圍環流衝擊",
            "timeline": [
                {"date": "6/24 (三)", "prob": 30, "desc": "外圍雲系接近，局部短暫陣雨"},
                {"date": "6/25 (四)", "prob": 85, "desc": "環流迎風面，強降雨高峰、防豪雨"},
                {"date": "6/26 (五)", "prob": 70, "desc": "偏南風持續引進水氣，午後大雨"},
                {"date": "6/27 (六)", "prob": 40, "desc": "恢復夏季西南風，午後局部雷陣雨"},
                {"date": "6/28 (日)", "prob": 25, "desc": "多雲到晴，午後陣雨機率低"}
            ]
        },
        "circles": [
            {"time": "6/24 02:00", "lon": 124.6, "lat": 20.2, "radius": 180000, "color": [255, 149, 0, 80]}, 
            {"time": "6/24 20:00", "lon": 125.0, "lat": 22.0, "radius": 170000, "color": [255, 149, 0, 75]},
            {"time": "6/25 20:00", "lon": 125.8, "lat": 24.6, "radius": 160000, "color": [255, 149, 0, 70]}, 
            {"time": "6/26 20:00", "lon": 127.5, "lat": 28.0, "radius": 190000, "color": [255, 59, 48, 60]},  
            {"time": "6/27 20:00", "lon": 131.0, "lat": 31.5, "radius": 220000, "color": [255, 59, 48, 50]}
        ],
        "paths": [{"path": [[124.6, 20.2], [125.0, 22.0], [125.8, 24.6], [127.5, 28.0], [131.0, 31.5]], "color": [0, 255, 200]}]
    },
    {
        "id": "TD082026", 
        "name_zh": "熱帶性低氣壓 TD08 (遠海系統) - 無威脅無降雨", 
        "name_en": "TD08", 
        "lat": 14.5, "lon": 146.0, 
        "base_probs": {"CWA": 0.0, "NCDR": 0.0, "ECMWF": 0.0, "JTWC": 0.0, "JMA": 0.0, "HKO": 0.0, "NMC": 0.0},
        "has_rain_threat": False,
        "rain_forecast": {
            "county": "屏東縣",
            "accumulated_5day": "0~10 mm",
            "rain_days": ["無特定降雨時段"],
            "alert_level": "無威脅",
            "timeline": [
                {"date": "6/24", "prob": 10, "desc": "晴到多雲"},
                {"date": "6/25", "prob": 10, "desc": "晴到多雲"},
                {"date": "6/26", "prob": 15, "desc": "穩定夏季天氣"},
                {"date": "6/27", "prob": 10, "desc": "穩定天氣"},
                {"date": "6/28", "prob": 10, "desc": "穩定天氣"}
            ]
        },
        "circles": [
            {"time": "6/22 20:00", "lon": 146.0, "lat": 14.5, "radius": 120000, "color": [255, 255, 255, 50]}
        ],
        "paths": [{"path": [[146.0, 14.5], [143.0, 17.0]], "color": [200, 200, 200]}]
    }
]

# --- 4. 空間防禦圈核心演算法 ---
active_systems = []
for sys in REAL_TIME_DATA:
    dist = calc_haversine(TW_LAT, TW_LON, sys["lat"], sys["lon"])
    sys["distance"] = dist
    active_systems.append(sys)

# 颱風切換選單
options = [f"🌀 {s['name_zh']} - 距台 {s['distance']} KM" for s in active_systems]
selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
selected_idx = options.index(selected_option)
current_sys = active_systems[selected_idx]

p_dict = current_sys["base_probs"] # 直接採用圖資實時概率
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

# 警報燈號
if current_sys["has_rain_threat"]:
    st.warning(f"⚠️ 【勇式戰情警告】侵台綜合概率低（{avg_yong_prob}%），但受外圍環流影響，【屏東縣】已進入強降雨預警範圍！")
else:
    st.success(f"🍏 【勇式戰情警告】全系統安全無虞。侵台概率為 0.0%，天氣穩定。")

# --- 🚀 6. 核心排版重構：左邊放地圖與數據，右邊放總結 (免滾動一目了然) ---
left_main_col, right_summary_col = st.columns([65, 35], gap="medium")

with left_main_col:
    # 再次切分：地圖靠左，屏東面板靠右
    map_sub_col, data_sub_col = st.columns([55, 45], gap="small")
    
    with map_sub_col:
        df_circles = pd.DataFrame(current_sys["circles"])
        df_paths = pd.DataFrame(current_sys["paths"])
        map_layers = []

        # 半透明預報圓圈與軌跡線
        map_layers.append(pdk.Layer("ScatterplotLayer", df_circles, get_position=["lon", "lat"], get_radius="radius", get_fill_color="color"))
        map_layers.append(pdk.Layer("ScatterplotLayer", df_circles, get_position=["lon", "lat"], get_radius=15000, get_fill_color=[255, 255, 255, 255]))
        map_layers.append(pdk.Layer("PathLayer", df_paths, get_path="path", get_color="color", width_min_pixels=3, get_width=4))
        map_layers.append(pdk.Layer("TextLayer", df_circles, get_position=["lon", "lat"], get_text="time", get_color=[255, 255, 255, 230], get_size=13, get_alignment_baseline="'bottom'"))

        # 地標
        poi_data = [
            {"label": "TAIWAN 防禦中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255, 255]},
            {"label": "屏東防禦點", "lon": PT_LON, "lat": PT_LAT, "size": 20000, "color": [236, 72, 153, 255]}
        ]
        map_layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame(poi_data), get_position=["lon", "lat"], get_radius="size", get_fill_color="color"))
        
        view_state = pdk.ViewState(latitude=TW_LAT + 2, longitude=TW_LON + 5, zoom=4.2, pitch=0)
        st.pydeck_chart(pdk.Deck(map_provider=None, map_style=None, initial_view_state=view_state, layers=map_layers), use_container_width=True)

    with data_sub_col:
        # 屏東防汛面板
        rf = current_sys["rain_forecast"]
        st.markdown(f"""
        <div class="pingtung-box">
            <div class="pingtung-title">📍 屏東縣即時動態降雨防汛面板</div>
            <table style="width:100%; border-collapse: collapse; font-size:13px;">
                <tr style="border-bottom: 1px solid #334155;"><td style="padding:6px 0; color:#94a3b8;">監測區域</td><td style="font-weight:bold; color:#f43f5e;">{rf['county']} 全區</td></tr>
                <tr style="border-bottom: 1px solid #334155;"><td style="padding:6px 0; color:#94a3b8;">5日預估累積雨量</td><td style="font-weight:bold; color:#38bdf8; font-size:16px;">{rf['accumulated_5day']}</td></tr>
                <tr style="border-bottom: 1px solid #334155;"><td style="padding:6px 0; color:#94a3b8;">核心下雨時段</td><td style="font-weight:bold; color:#fbbf24;">{', '.join(rf['rain_days'])}</td></tr>
                <tr><td style="padding:6px 0; color:#94a3b8;">防汛警告強度</td><td style="font-weight:bold; color:#ef4444;">{rf['alert_level']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # 逐日降雨趨勢
        st.markdown("<p style='font-size:14px; font-weight:bold; margin-bottom:5px;'>📅 逐日降雨概率與風險趨勢</p>", unsafe_allow_html=True)
        df_timeline = pd.DataFrame(rf["timeline"])
        st.dataframe(
            df_timeline,
            column_config={
                "date": "預報日期",
                "prob": st.column_config.ProgressColumn("降雨概率", min_value=0, max_value=100, format="%d%%"),
                "desc": "天氣說明"
            },
            hide_index=True,
            use_container_width=True,
            height=230
        )

with right_summary_col:
    # 🔥 完美右移：氣象專業路徑與降雨預測總結
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">📊 6/24 雙颱戰情與降雨全盤總結</div>
        <p><b>① 強颱米克拉實況：</b><br>
        目前中心位於北緯 20.2度、東經 124.6度，中心氣壓 925~945 百帕。七級風暴風半徑達 180 公里，屬於結構非常紮實的成熟系統。</p>
        <p><b>② 預報圈大角度北轉：</b><br>
        左側地圖的半透明圓圈直觀呈現了各國最新預報。颱風將採取「擦過台灣東部海面」路線，於 <b>25日20:00 最接近台灣東北部外海</b>，隨後大角度向東北拉開直撲日本，中心不登陸本島。</p>
        <p><b>③ 屏東縣核心下雨時段提醒：</b><br>
        雖然中心不登陸，但由於暴風圈寬廣，迎風面的偏南風會將肥厚的外圍雲系直接掃入南台灣。<b>屏東縣防汛警報強度已拉高。</b>核心下雨天數如下：<br>
        • <b>6/24 (三) 晚間</b>：外圍雨帶接近，開始有局部短暫陣雨。<br>
        • <b>6/25 (四) 【強降雨高峰】</b>：降雨機率高達 <b>85%</b>，迎風面山區與恆春半島嚴防豪雨。<br>
        • <b>6/26 (五) 上半天</b>：風向轉偏南風持續引進水氣，降雨機率 <b>70%</b>，仍有較大雨勢。<br>
        • <b>6/27 (六) 起</b>：颱風遠離，回歸夏季午後雷陣雨型態。</p>
        <p><b>④ 遠海 TD08 動態：</b><br>
        遠方關島海面的熱低壓對台灣<b>精確判定無威脅（0%）</b>，不帶來任何降雨。</p>
    </div>
    """, unsafe_allow_html=True)
