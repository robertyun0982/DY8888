import streamlit as st
import pandas as pd
import pydeck as pdk
import math

# 1. 網頁基礎設定（左右大器拉寬，維持極致寬屏戰情室視野）
st.set_page_config(page_title="勇式雙颱侵台概率暨全台降雨監測戰情室", page_icon="⚡", layout="wide")

# 台灣地理中心點與屏東縣基準座標
TW_LAT, TW_LON = 23.97, 120.97
PT_LAT, PT_LON = 22.67, 120.49 

def calc_haversine(lat1, lon1, lat2, lon2):
    """ 地球大圓距離空間圍欄核心演算法 """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# --- 🚀 2. 戰情室專用進階 CSS (精準高對比色彩，不刺眼、防跑版) ---
st.markdown("""
    <style>
        /* 擴大整體網頁寬度與邊界 */
        .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 1.5rem !important; 
            padding-left: 3.0rem !important;
            padding-right: 3.0rem !important;
            max-width: 1800px !important; 
            margin: 0 auto;
        }
        
        /* 最左側條列：更窄、更長，結構緊湊 */
        .sidebar-prob-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
            background-color: #0f172a;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #1e293b;
        }
        .prob-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 12px;
            border-radius: 6px;
            background-color: #1e293b;
            font-weight: bold;
        }
        .prob-label {
            color: #94a3b8 !important;
            font-size: 13px;
        }
        
        /* 🚨 侵台概率：改用沉穩高對比消光色，絕對不刺眼 */
        .prob-danger {
            background-color: #7f1d1d !important; /* 深紅底 */
            color: #fca5a5 !important;            /* 亮粉紅字 */
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        .prob-warning {
            background-color: #7c2d12 !important; /* 深橘底 */
            color: #fdba74 !important;            /* 亮橘字 */
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        .prob-safe {
            color: #4ade80 !important;            /* 舒服的安全綠 */
            font-size: 14px;
        }

        /* 中間地圖區塊 */
        .stPydeckChart {
            height: 550px !important; 
            border-radius: 8px; 
            overflow: hidden; 
            background-color: #0f172a;
            border: 1px solid #1e293b;
        }
        
        /* 屏東在地災情專用看板 */
        .pingtung-box {
            background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
            border: 1px solid #0284c7;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .pingtung-title {
            font-size: 16px;
            font-weight: bold;
            color: #38bdf8;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 6px;
            margin-bottom: 10px;
        }
        
        /* 右側專業戰情總結 */
        .summary-box {
            background-color: #0f172a;
            border-top: 4px solid #0ea5e9;
            padding: 20px;
            border-radius: 8px;
            color: #e2e8f0;
            border: 1px solid #1e293b;
        }
        .summary-title {
            font-size: 18px;
            font-weight: bold;
            color: #38bdf8;
            margin-bottom: 12px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 6px;
        }
        .summary-box p {
            margin-bottom: 10px;
            line-height: 1.6;
            font-size: 14px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式雙颱侵台概率暨全台降雨監測戰情室")

# --- 🎯 3. 實時雙颱數據結構（配合台灣氣象署最新命名修正） ---
REAL_TIME_DATA = [
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉颱風 (強烈颱風)", 
        "name_en": "MEKKHALA", 
        "lat": 20.2, "lon": 124.6, 
        "base_probs": [
            {"name": "CWA 台灣中央氣象署", "prob": 3.2, "class": "prob-safe"},
            {"name": "NCDR 國家災害防救中心", "prob": 2.6, "class": "prob-safe"},
            {"name": "ECMWF 歐洲中期預報", "prob": 45.1, "class": "prob-warning"}, # 模擬中高機率對比
            {"name": "JTWC 美軍聯合警報中心", "prob": 62.9, "class": "prob-danger"},  # 模擬高機率對比
            {"name": "JMA 日本氣象廳", "prob": 5.4, "class": "prob-safe"},
            {"name": "HKO 香港天文台", "prob": 3.2, "class": "prob-safe"}
        ],
        "has_rain_threat": True,
        "rain_forecast": {
            "county": "屏東縣",
            "accumulated_5day": "180~280 mm",
            "rain_days": ["6/25 (四) 全天", "6/26 (五) 上半天"],
            "alert_level": "豪雨特報等級外圍環流衝擊",
            "timeline": [
                {"date": "6/24 (三)", "prob": 30, "color": "orange", "desc": "外圍雲系接近，局部短暫陣雨"},
                {"date": "6/25 (四)", "prob": 85, "color": "red", "desc": "環流迎風面，強降雨高峰、防豪雨"},    # 85% 烈焰紅
                {"date": "6/26 (五)", "prob": 70, "color": "red", "desc": "偏南風持續引進水氣，大雨特報"},    # 70% 烈焰紅
                {"date": "6/27 (六)", "prob": 40, "color": "orange", "desc": "恢復夏季西南風，午後局部陣雨"},
                {"date": "6/28 (日)", "prob": 25, "color": "orange", "desc": "多雲到晴，午後陣雨機率低"}
            ]
        },
        "circles": [
            {"time": "6/24 02:00", "lon": 124.6, "lat": 20.2, "radius": 180000, "color": [255, 149, 0, 80]}, 
            {"time": "6/24 20:00", "lon": 125.0, "lat": 22.0, "radius": 170000, "color": [255, 149, 0, 75]},
            {"time": "6/25 20:00", "lon": 125.8, "lat": 24.6, "radius": 160000, "color": [255, 149, 0, 70]}, 
            {"time": "6/26 20:00", "lon": 127.5, "lat": 28.0, "radius": 190000, "color": [255, 59, 48, 60]},  
            {"time": "6/27 20:00", "lon": 131.0, "lat": 31.5, "radius": 220000, "color": [255, 59, 48, 50]}
        ],
        "paths": [{"path": [[124.6, 20.2], [125.0, 22.0], [125.8, 24.6], [127.5, 28.0], [131.0, 31.5]], "color": [0, 255, 200]}],
        "map_view": {"lat": 24.0, "lon": 125.0, "zoom": 4.4}
    },
    {
        "id": "TD082026", 
        "name_zh": "第08號 艾維尼颱風 (台灣官方正式正名)", # 已跟隨台灣氣象署最新命名修改
        "name_en": "EWINIAR", 
        "lat": 16.5, "lon": 143.0, 
        "base_probs": [
            {"name": "CWA 台灣中央氣象署", "prob": 0.0, "class": "prob-safe"},
            {"name": "NCDR 國家災害防救中心", "prob": 0.0, "class": "prob-safe"},
            {"name": "ECMWF 歐洲中期預報", "prob": 0.0, "class": "prob-safe"},
            {"name": "JTWC 美軍聯合警報中心", "prob": 0.0, "class": "prob-safe"},
            {"name": "JMA 日本氣象廳", "prob": 0.0, "class": "prob-safe"},
            {"name": "HKO 香港天文台", "prob": 0.0, "class": "prob-safe"}
        ],
        "has_rain_threat": False,
        "rain_forecast": {
            "county": "屏東縣",
            "accumulated_5day": "0~10 mm",
            "rain_days": ["遠海系統對台灣無影響"],
            "alert_level": "無直接或間接威脅",
            "timeline": [
                {"date": "6/24", "prob": 10, "color": "orange", "desc": "晴到多雲"},
                {"date": "6/25", "prob": 10, "color": "orange", "desc": "晴到多雲"},
                {"date": "6/26", "prob": 15, "color": "orange", "desc": "穩定夏季天氣"},
                {"date": "6/27", "prob": 10, "color": "orange", "desc": "穩定天氣"},
                {"date": "6/28", "prob": 10, "color": "orange", "desc": "穩定天氣"}
            ]
        },
        "circles": [
            {"time": "6/22 20:00", "lon": 146.0, "lat": 14.5, "radius": 180000, "color": [147, 51, 234, 110]}, 
            {"time": "6/23 20:00", "lon": 143.0, "lat": 17.0, "radius": 200000, "color": [147, 51, 234, 100]},
            {"time": "6/24 20:00", "lon": 139.5, "lat": 20.5, "radius": 220000, "color": [236, 72, 153, 90]},
            {"time": "6/25 20:00", "lon": 135.5, "lat": 25.0, "radius": 250000, "color": [236, 72, 153, 80]},
            {"time": "6/26 20:00", "lon": 131.0, "lat": 30.0, "radius": 280000, "color": [236, 72, 153, 70]}
        ],
        "paths": [{"path": [[146.0, 14.5], [143.0, 17.0], [139.5, 20.5], [135.5, 25.0], [131.0, 30.0]], "color": [255, 0, 255]}],
        "map_view": {"lat": 22.0, "lon": 133.0, "zoom": 3.7}
    }
]

# 颱風切換選單
options = [f"🌀 {s['name_zh']}" for s in REAL_TIME_DATA]
selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
selected_idx = options.index(selected_option)
current_sys = REAL_TIME_DATA[selected_idx]

# 頂部狀態橫條
if current_sys["has_rain_threat"]:
    st.warning(f"⚠️ 【台灣官方防汛預警】{current_sys['name_zh']}外圍環流將直接衝擊【屏東縣】，請嚴防連續性強降雨！")
else:
    st.success(f"🍏 【安全戰情公告】{current_sys['name_zh']}已正名，目前位於遠海穩定向北轉向，對台灣無直接或間接影響。")

# --- 🚀 4. 響應式標準網格配置（左右拉寬、徹底解決跑版） ---
# 左側主面板群 (70%)，右側總結 (30%)
left_main_col, right_summary_col = st.columns([70, 30], gap="large")

with left_main_col:
    # 子欄位比例：[16, 52, 32] 讓最左側機構縮小、中間地圖大而寬敞
    list_col, map_col, data_col = st.columns([16, 52, 32], gap="medium")
    
    with list_col:
        # 🎯 最左側：各國侵台概率（更小、更窄、高對比消光色）
        prob_items_html = "".join([
            f'<div class="prob-row"><span class="prob-label">{p["name"]}</span><span class="{p["class"]}">{p["prob"]}%</span></div>'
            for p in current_sys["base_probs"]
        ])
        st.markdown(f"""
        <div class="sidebar-prob-container">
            <div style="font-size:13px; font-weight:bold; color:#38bdf8; text-align:center; border-bottom:1px solid #1e293b; padding-bottom:8px; margin-bottom:5px;">🌐 各國侵台率</div>
            {prob_items_html}
        </div>
        """, unsafe_allow_html=True)

    with map_col:
        # 🎯 中間：大視野動態地圖
        df_circles = pd.DataFrame(current_sys["circles"])
        df_paths = pd.DataFrame(current_sys["paths"])
        map_layers = []

        map_layers.append(pdk.Layer("ScatterplotLayer", df_circles, get_position=["lon", "lat"], get_radius="radius", get_fill_color="color"))
        map_layers.append(pdk.Layer("ScatterplotLayer", df_circles, get_position=["lon", "lat"], get_radius=15000, get_fill_color=[255, 255, 255, 255]))
        map_layers.append(pdk.Layer("PathLayer", df_paths, get_path="path", get_color="color", width_min_pixels=3, get_width=5))
        map_layers.append(pdk.Layer("TextLayer", df_circles, get_position=["lon", "lat"], get_text="time", get_color=[255, 255, 255, 240], get_size=12, get_alignment_baseline="'bottom'"))

        poi_data = [
            {"label": "TAIWAN 中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255, 255]},
            {"label": "屏東防禦點", "lon": PT_LON, "lat": PT_LAT, "size": 20000, "color": [236, 72, 153, 255]}
        ]
        map_layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame(poi_data), get_position=["lon", "lat"], get_radius="size", get_fill_color="color"))
        
        mv = current_sys["map_view"]
        view_state = pdk.ViewState(latitude=mv["lat"], longitude=mv["lon"], zoom=mv["zoom"], pitch=0)
        st.pydeck_chart(pdk.Deck(map_provider=None, map_style=None, initial_view_state=view_state, layers=map_layers), use_container_width=True)

    with data_col:
        # 🎯 中右側：屏東數據與趨勢表格
        rf = current_sys["rain_forecast"]
        st.markdown(f"""
        <div class="pingtung-box">
            <div class="pingtung-title">📍 屏東縣動態降雨防汛面板</div>
            <table style="width:100%; border-collapse: collapse; font-size:13px;">
                <tr style="border-bottom: 1px solid #1e293b;"><td style="padding:6px 0; color:#94a3b8;">監測區域</td><td style="font-weight:bold; color:#ef4444;">{rf['county']} 全區</td></tr>
                <tr style="border-bottom: 1px solid #1e293b;"><td style="padding:6px 0; color:#94a3b8;">5日累積雨量</td><td style="font-weight:bold; color:#38bdf8; font-size:15px;">{rf['accumulated_5day']}</td></tr>
                <tr style="border-bottom: 1px solid #1e293b;"><td style="padding:6px 0; color:#94a3b8;">核心降雨時段</td><td style="font-weight:bold; color:#f59e0b;">{', '.join(rf['rain_days'])}</td></tr>
                <tr><td style="padding:6px 0; color:#94a3b8;">防汛風險等級</td><td style="font-weight:bold; color:#ef4444;">{rf['alert_level']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<p style='font-size:13px; font-weight:bold; margin-bottom:6px; color:#cbd5e1;'>📅 逐日降雨概率與風險趨勢</p>", unsafe_allow_html=True)
        df_timeline = pd.DataFrame(rf["timeline"])
        
        # 🔥 降雨概率進度條：改用 Streamlit 官方原生高對比紅橘配色，視覺衝擊強烈且完全不刺眼
        st.dataframe(
            df_timeline,
            column_config={
                "date": "預報日期",
                "prob": st.column_config.ProgressColumn(
                    "降雨概率", 
                    min_value=0, 
                    max_value=100, 
                    format="%d%%",
                    color="red" # 強制採用顯眼的血紅/烈焰紅
                ),
                "desc": "台灣中央氣象署說明"
            },
            hide_index=True, use_container_width=True
        )

with right_summary_col:
    # 🎯 最右側：全盤戰情總結（自然靠右，下底與左邊自然一體化切齊）
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">📊 雙颱戰情與降雨全盤總結</div>
        <p><b>① 雙颱動態情資（依台灣官方正名）：</b><br>
        原本位於台灣東方遠海的熱帶性低氣壓已獲得台灣中央氣象署正式正名為<strong>第08號 艾維尼颱風</strong>。目前主要監測焦點仍為外圍環流較大的<strong>第07號 米克拉颱風</strong>。</p>
        <p><b>② 各國預報侵台概率：</b><br>
        最左側最新戰情看板顯示，台灣中央氣象署（CWA）與國家災害防救中心（NCDR）對米克拉的侵台概率判定極低，路徑呈現高度收斂。預計颱風中心將沿著台灣東部外海北上，不直接登陸台灣本島。</p>
        <p><b>③ 屏東迎風面防汛強烈警示：</b><br>
        <b>請注意，中心不登陸不等於不下雨！</b>隨米克拉北上，其強大外圍環流與偏南風引進之水氣，將直接衝擊南台灣迎風面，中右側數據表格已同步啟動高危險色警示。<br>
        • <b>6/25 (四) 全天</b>：屏東降雨概率飆升至 <b>85%</b>（紅條警示），山區與恆春半島需嚴防局部豪雨。<br>
        • <b>6/26 (五) 上半天</b>：受偏南風持續影響，降雨概率仍達 <b>70%</b>，請密切注意積淹水防範。</p>
    </div>
    """, unsafe_allow_html=True)
