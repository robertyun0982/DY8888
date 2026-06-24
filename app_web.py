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

# --- 🚀 2. 戰情室專用高級 CSS 操控 (全寬無圖例、極致降雨視覺美化) ---
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
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #f8fafc;
        }
        .pingtung-title {
            font-size: 20px;
            font-weight: bold;
            color: #38bdf8;
            border-bottom: 1px solid #38bdf8;
            padding-bottom: 8px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
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

st.markdown("## ⚡ 勇式雙颱侵台概率暨動態降雨監測系統")

# --- 🎯 3. 實時雙颱與降雨圖資數據結構 ---
REAL_TIME_DATA = [
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉颱風 (強颱等級) - 注意外圍強降雨", 
        "name_en": "MEKKHALA", 
        "lat": 20.2, "lon": 124.6, 
        "base_probs": {"CWA": 5.0, "NCDR": 4.0, "ECMWF": 8.0, "JTWC": 4.5, "JMA": 8.5, "HKO": 5.0, "NMC": 6.0},
        "has_rain_threat": True, # 標記是否有外圍降雨威脅
        "rain_forecast": {
            "county": "屏東縣",
            "accumulated_5day": "180~280 mm",
            "rain_days": ["6/25 (四) 全天", "6/26 (五) 上半天"],
            "alert_level": "豪雨特報等級外圍環流衝擊",
            "timeline": [
                {"date": "6/24 (三)", "prob": "30%", "desc": "颱風外圍雲系接近，局部短暫陣雨"},
                {"date": "6/25 (四)", "prob": "85%", "desc": "外圍環流正對迎風面，強降雨高峰、山區防豪雨"},
                {"date": "6/26 (五)", "prob": "70%", "desc": "颱風加速向東北遠離，偏南風持續引進水氣，午後有大雨"},
                {"date": "6/27 (六)", "prob": "40%", "desc": "恢復為一般夏季西南風型態，午後局部雷陣雨"},
                {"date": "6/28 (日)", "prob": "25%", "desc": "多雲到晴，午後對流性陣雨機率低"}
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
                {"date": "6/24", "prob": "10%", "desc": "晴到多雲"},
                {"date": "6/25", "prob": "10%", "desc": "晴到多雲"},
                {"date": "6/26", "prob": "15%", "desc": "穩定夏季天氣"},
                {"date": "6/27", "prob": "10%", "desc": "穩定天氣"},
                {"date": "6/28", "prob": "10%", "desc": "穩定天氣"}
            ]
        },
        "circles": [
            {"time": "6/22 20:00", "lon": 146.0, "lat": 14.5, "radius": 120000, "color": [255, 255, 255, 50]}, 
            {"time": "6/23 20:00", "lon": 143.0, "lat": 17.0, "radius": 130000, "color": [255, 255, 255, 44]}
        ],
        "paths": [{"path": [[146.0, 14.5], [143.0, 17.0]], "color": [200, 200, 200]}]
    }
]

# --- 4. 空間防禦圈核心演算法 ---
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

# 颱風切換選單
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

# 🚨 強度升級：新增降雨威脅動態雙向警報機制
if current_sys["has_rain_threat"]:
    st.warning(f"⚠️ 【勇式戰情警告】侵台概率低（{avg_yong_prob}%），但受颱風外圍雲系與偏南風影響，【屏東縣】已進入外圍強降雨預警範圍，明後天防範豪雨！")
else:
    if avg_yong_prob == 0.0:
        st.success(f"🍏 【勇式戰情警告】全系統安全無虞。侵台概率為 0.0%，本島陸地天氣穩定，無降雨潛勢。")

# --- 6. 下方分欄：左側高強度半透明預報圖，右側屏東降雨數據看板 ---
map_col, info_col = st.columns([6, 4])

with map_col:
    df_circles = pd.DataFrame(current_sys["circles"])
    df_paths = pd.DataFrame(current_sys["paths"])

    map_layers = []

    # 半透明預報圓圈
    map_layers.append(pdk.Layer(
        "ScatterplotLayer", df_circles, get_position=["lon", "lat"],
        get_radius="radius", get_fill_color="color"
    ))
    # 中心發光亮點
    map_layers.append(pdk.Layer(
        "ScatterplotLayer", df_circles, get_position=["lon", "lat"],
        get_radius=15000, get_fill_color=[255, 255, 255, 255]
    ))
    # 中心導引軌跡線
    map_layers.append(pdk.Layer(
        "PathLayer", df_paths, get_path="path",
        get_color="color", width_min_pixels=3, get_width=4
    ))
    # 時間戳
    map_layers.append(pdk.Layer(
        "TextLayer", df_circles, get_position=["lon", "lat"], get_text="time",
        get_color=[255, 255, 255, 230], get_size=14, get_alignment_baseline="'bottom'"
    ))

    # 台灣本島中心與屏東防禦標記點
    poi_data = [
        {"label": "TAIWAN 防禦中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255, 255]},
        {"label": "屏東防禦點", "lon": PT_LON, "lat": PT_LAT, "size": 20000, "color": [236, 72, 153, 255]} # 桃紅亮色標記屏東
    ]
    map_layers.append(pdk.Layer(
        "ScatterplotLayer", pd.DataFrame(poi_data), get_position=["lon", "lat"],
        get_radius="size", get_fill_color="color"
    ))
    map_layers.append(pdk.Layer(
        "TextLayer", pd.DataFrame(poi_data), get_position=["lon", "lat"], get_text="label",
        get_color=[255, 255, 255, 255], get_size=14, get_alignment_baseline="'bottom'"
    ))

    view_state = pdk.ViewState(latitude=TW_LAT + 2, longitude=TW_LON + 6, zoom=4.0, pitch=0)

    st.pydeck_chart(pdk.Deck(
        map_provider=None, map_style=None,
        initial_view_state=view_state, layers=map_layers
    ), use_container_width=True)

with info_col:
    # 🔥 屏東在地大數據降雨戰情看板
    rf = current_sys["rain_forecast"]
    
    st.markdown(f"""
    <div class="pingtung-box">
        <div class="pingtung-title">📍 屏東縣即時動態降雨防汛面板</div>
        <table style="width:100%; border-collapse: collapse; font-size:15px;">
            <tr style="border-bottom: 1px solid #334155;"><td style="padding:8px 0; color:#94a3b8;">監測目標區域</td><td style="font-weight:bold; color:#f43f5e;">{rf['county']} 全區</td></tr>
            <tr style="border-bottom: 1px solid #334155;"><td style="padding:8px 0; color:#94a3b8;">5日預估累積雨量</td><td style="font-weight:bold; color:#38bdf8; font-size:18px;">{rf['accumulated_5day']}</td></tr>
            <tr style="border-bottom: 1px solid #334155;"><td style="padding:8px 0; color:#94a3b8;">核心下雨時段</td><td style="font-weight:bold; color:#fbbf24;">{', '.join(rf['rain_days'])}</td></tr>
            <tr><td style="padding:8px 0; color:#94a3b8;">防汛警告強度</td><td style="font-weight:bold; color:#ef4444;">{rf['alert_level']}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    # 逐日降雨潛勢時間軸 (一秒看懂哪幾天要下雨)
    st.markdown("##### 📅 逐日降雨概率與氣象風險趨勢")
    
    df_timeline = pd.DataFrame(rf["timeline"])
    # 轉換成戰情室表格顯示
    st.dataframe(
        df_timeline,
        column_config={
            "date": "預報日期",
            "prob": st.column_config.ProgressColumn("降雨概率", help="未來降雨潛勢百分比", min_value=0, max_value=100, format="%s"),
            "desc": "動態天氣說明"
        },
        hide_index=True,
        use_container_width=True
    )

# --- 7. 氣象專業路徑與降雨預測總結 ---
st.markdown(f"""
<div class="summary-box">
    <div class="summary-title">📊 6/24 颱風路徑與降雨衝擊全盤分析</div>
    <p><b>1. 「無颱風登陸」但「必定有降雨」之科學依據：</b><br>
    雖然 7 國機構一致認定米克拉颱風中心將採取從台灣東南方海面北轉東北的路線，不直接登陸本島，但這並不意味著沒有天氣災害。颱風在 6/25 抵達台灣東部外海時，其強大的逆時針環流會將大片水氣與迎風面偏南風直接推向台灣陸地。<b>由於屏東地處迎風面山區與沿海，首當其衝，將承受非常顯著的外圍雲系降雨影響。</b></p>
    <p><b>2. 屏東縣哪幾天要下雨？核心時段精準鎖定：</b><br>
    * <b>6/24 (三) 傍晚起</b>：外圍雨帶前緣抵達，陸續轉為有局部短暫陣雨的天氣。<br>
    * <b>6/25 (四) 全天【強降雨核心高峰】</b>：受外圍環流直接掃入，降雨機率暴增至 <b>85%</b>，不排除出現局部大雨或豪雨，尤其是恆春半島與屏東山區。<br>
    * <b>6/26 (五) 上半天</b>：颱風雖然北轉遠離，但後續引進的偏南風水氣依舊旺盛，降雨機率仍達 <b>70%</b>，午後局部地區仍有大雨勢。<br>
    * <b>6/27 (六) 之後</b>：颱風徹底遠離，天氣回歸常態的夏季西南風型態，降雨縮減至午後局部雷陣雨。</p>
</div>
""", unsafe_allow_html=True)
