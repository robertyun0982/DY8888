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
    """ 地球大圓距離空間圍欄核心演算法 """
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1) * math.cos(p2) * math.sin(dl/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 1)

# --- 🚀 2. 戰情室專用高級 CSS 操控 (左側條列排版、強化路徑視覺) ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.0rem !important; 
            padding-bottom: 0px !important; 
            max-width: 1520px !important; 
            margin: 0 auto;
        }
        
        /* 🎨 左側條列式各國預報機率面板 */
        .sidebar-prob-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
            background-color: #0f172a;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #334155;
        }
        .prob-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            border-radius: 6px;
            background-color: #1e293b;
            font-weight: bold;
        }
        .prob-label {
            color: #FFFFFF !important;
            font-size: 14px;
        }
        .prob-value {
            font-size: 16px;
        }
        
        /* 各國條列色彩映射 */
        .cwa-border { border-left: 4px solid rgb(255,59,48); } .cwa-text { color: rgb(255,59,48); }
        .ncdr-border { border-left: 4px solid rgb(255,149,0); } .ncdr-text { color: rgb(255,149,0); }
        .ecmwf-border { border-left: 4px solid rgb(255,214,10); } .ecmwf-text { color: rgb(255,214,10); }
        .jtwc-border { border-left: 4px solid rgb(52,211,153); } .jtwc-text { color: rgb(52,211,153); }
        .jma-border { border-left: 4px solid rgb(0,199,190); } .jma-text { color: rgb(0,199,190); }
        .hko-border { border-left: 4px solid rgb(0,122,255); } .hko-text { color: rgb(0,122,255); }
        .nmc-border { border-left: 4px solid rgb(175,82,222); } .nmc-text { color: rgb(175,82,222); }

        /* 地圖元件高度 */
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
        
        /* 右側專業戰情文字區塊 */
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
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ 勇式雙颱侵台概率暨動態降雨監測系統")

# --- 🎯 3. 實時雙颱與降雨圖資數據結構 (TD08 正式正名) ---
REAL_TIME_DATA = [
    {
        "id": "WP072026", 
        "name_zh": "第07號 米克拉颱風 (強颱等級)", 
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
        "paths": [{"path": [[124.6, 20.2], [125.0, 22.0], [125.8, 24.6], [127.5, 28.0], [131.0, 31.5]], "color": [0, 255, 200]}],
        "map_view": {"lat": 24.0, "lon": 125.0, "zoom": 4.2}
    },
    {
        "id": "TD082026", 
        "name_zh": "第08號 艾維尼颱風 (EWINIAR) - 原TD08正名", 
        "name_en": "EWINIAR", 
        "lat": 16.5, "lon": 143.0, 
        "base_probs": {"CWA": 0.0, "NCDR": 0.0, "ECMWF": 0.0, "JTWC": 0.0, "JMA": 0.0, "HKO": 0.0, "NMC": 0.0},
        "has_rain_threat": False,
        "rain_forecast": {
            "county": "屏東縣",
            "accumulated_5day": "0~10 mm",
            "rain_days": ["遠海系統無影響"],
            "alert_level": "無直接或外圍威脅",
            "timeline": [
                {"date": "6/24", "prob": 10, "desc": "晴到多雲"},
                {"date": "6/25", "prob": 10, "desc": "晴到多雲"},
                {"date": "6/26", "prob": 15, "desc": "穩定夏季天氣"},
                {"date": "6/27", "prob": 10, "desc": "穩定天氣"},
                {"date": "6/28", "prob": 10, "desc": "穩定天氣"}
            ]
        },
        # 🔥 視覺強化：顯著拉大半透明半徑，並改用醒目的高飽和度發光紫色與粉色，解決不明显問題
        "circles": [
            {"time": "6/22 20:00", "lon": 146.0, "lat": 14.5, "radius": 180000, "color": [147, 51, 234, 110]}, 
            {"time": "6/23 20:00", "lon": 143.0, "lat": 17.0, "radius": 200000, "color": [147, 51, 234, 100]},
            {"time": "6/24 20:00", "lon": 139.5, "lat": 20.5, "radius": 220000, "color": [236, 72, 153, 90]},
            {"time": "6/25 20:00", "lon": 135.5, "lat": 25.0, "radius": 250000, "color": [236, 72, 153, 80]},
            {"time": "6/26 20:00", "lon": 131.0, "lat": 30.0, "radius": 280000, "color": [236, 72, 153, 70]}
        ],
        # 連接線加粗加亮
        "paths": [{"path": [[146.0, 14.5], [143.0, 17.0], [139.5, 20.5], [135.5, 25.0], [131.0, 30.0]], "color": [255, 0, 255]}],
        "map_view": {"lat": 22.0, "lon": 133.0, "zoom": 3.6} # 自動為艾維尼調整最佳中心視野
    }
]

# 颱風切換選單
options = [f"🌀 {s['name_zh']}" for s in REAL_TIME_DATA]
selected_option = st.selectbox("🎯 選擇受偵測威脅物：", options, label_visibility="collapsed")
selected_idx = options.index(selected_option)
current_sys = REAL_TIME_DATA[selected_idx]

p_dict = current_sys["base_probs"]
avg_yong_prob = round(sum(p_dict.values()) / len(p_dict), 1)

# 橫向提示燈號
if current_sys["has_rain_threat"]:
    st.warning(f"⚠️ 【侵台綜合概率：{avg_yong_prob}%】米克拉颱風路徑偏北，中心不登陸，但外圍環流將直接衝擊【屏東縣】造成強降雨！")
else:
    st.success(f"🍏 【侵台綜合概率：0.0%】{current_sys['name_zh']}正名確立。路徑在遠海大角度北轉遠離，對台安全無威脅。")

# --- 🚀 4. 核心排版重構：左側條列與地圖數據 ✕ 右側總結 (完全免滾動) ---
left_main_col, right_summary_col = st.columns([68, 32], gap="medium")

with left_main_col:
    # 再次切分：最左側為機構條列列，中間地圖，地圖右側為屏東數據
    list_col, map_col, data_col = st.columns([22, 43, 35], gap="small")
    
    with list_col:
        # 🎯 完美移至左側條列的機構機率
        st.markdown("<p style='font-size:13px; font-weight:bold; margin-bottom:5px;'>🌐 機構預報侵台率</p>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="sidebar-prob-container">
            <div class="prob-row cwa-border"><span class="prob-label">CWA 台灣</span><span class="prob-value cwa-text">{p_dict.get('CWA', 0.0)}%</span></div>
            <div class="prob-row ncdr-border"><span class="prob-label">NCDR 災害</span><span class="prob-value ncdr-text">{p_dict.get('NCDR', 0.0)}%</span></div>
            <div class="prob-row ecmwf-border"><span class="prob-label">ECMWF 歐洲</span><span class="prob-value ecmwf-text">{p_dict.get('ECMWF', 0.0)}%</span></div>
            <div class="prob-row jtwc-border"><span class="prob-label">JTWC 美軍</span><span class="prob-value jtwc-text">{p_dict.get('JTWC', 0.0)}%</span></div>
            <div class="prob-row jma-border"><span class="prob-label">JMA 日本</span><span class="prob-value jma-text">{p_dict.get('JMA', 0.0)}%</span></div>
            <div class="prob-row hko-border"><span class="prob-label">HKO 香港</span><span class="prob-value hko-text">{p_dict.get('HKO', 0.0)}%</span></div>
            <div class="prob-row nmc-border"><span class="prob-label">NMC 中國</span><span class="prob-value nmc-text">{p_dict.get('NMC', 0.0)}%</span></div>
        </div>
        """, unsafe_allow_html=True)

    with map_col:
        df_circles = pd.DataFrame(current_sys["circles"])
        df_paths = pd.DataFrame(current_sys["paths"])
        map_layers = []

        # 渲染發光半透明圓圈與預報中心軌跡
        map_layers.append(pdk.Layer("ScatterplotLayer", df_circles, get_position=["lon", "lat"], get_radius="radius", get_fill_color="color"))
        map_layers.append(pdk.Layer("ScatterplotLayer", df_circles, get_position=["lon", "lat"], get_radius=15000, get_fill_color=[255, 255, 255, 255]))
        map_layers.append(pdk.Layer("PathLayer", df_paths, get_path="path", get_color="color", width_min_pixels=3, get_width=5))
        map_layers.append(pdk.Layer("TextLayer", df_circles, get_position=["lon", "lat"], get_text="time", get_color=[255, 255, 255, 240], get_size=13, get_alignment_baseline="'bottom'"))

        # 地標基準
        poi_data = [
            {"label": "TAIWAN 防禦中心", "lon": TW_LON, "lat": TW_LAT, "size": 35000, "color": [0, 149, 255, 255]},
            {"label": "屏東防禦點", "lon": PT_LON, "lat": PT_LAT, "size": 20000, "color": [236, 72, 153, 255]}
        ]
        map_layers.append(pdk.Layer("ScatterplotLayer", pd.DataFrame(poi_data), get_position=["lon", "lat"], get_radius="size", get_fill_color="color"))
        
        # 依據所選颱風自動切換最佳視野狀態
        mv = current_sys["map_view"]
        view_state = pdk.ViewState(latitude=mv["lat"], longitude=mv["lon"], zoom=mv["zoom"], pitch=0)
        st.pydeck_chart(pdk.Deck(map_provider=None, map_style=None, initial_view_state=view_state, layers=map_layers), use_container_width=True)

    with data_col:
        # 屏東防汛面板
        rf = current_sys["rain_forecast"]
        st.markdown(f"""
        <div class="pingtung-box">
            <div class="pingtung-title">📍 屏東縣降雨防汛面板</div>
            <table style="width:100%; border-collapse: collapse; font-size:13px;">
                <tr style="border-bottom: 1px solid #334155;"><td style="padding:6px 0; color:#94a3b8;">監測區域</td><td style="font-weight:bold; color:#f43f5e;">{rf['county']} 全區</td></tr>
                <tr style="border-bottom: 1px solid #334155;"><td style="padding:6px 0; color:#94a3b8;">5日累積雨量</td><td style="font-weight:bold; color:#38bdf8; font-size:16px;">{rf['accumulated_5day']}</td></tr>
                <tr style="border-bottom: 1px solid #334155;"><td style="padding:6px 0; color:#94a3b8;">核心降雨時段</td><td style="font-weight:bold; color:#fbbf24;">{', '.join(rf['rain_days'])}</td></tr>
                <tr><td style="padding:6px 0; color:#94a3b8;">風險強度</td><td style="font-weight:bold; color:#ef4444;">{rf['alert_level']}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # 逐日趨勢
        st.markdown("<p style='font-size:13px; font-weight:bold; margin-bottom:5px;'>📅 逐日降雨概率與風險趨勢</p>", unsafe_allow_html=True)
        df_timeline = pd.DataFrame(rf["timeline"])
        st.dataframe(
            df_timeline,
            column_config={
                "date": "預報日期",
                "prob": st.column_config.ProgressColumn("降雨概率", min_value=0, max_value=100, format="%d%%"),
                "desc": "天氣說明"
            },
            hide_index=True, use_container_width=True, height=220
        )

with right_summary_col:
    # 🎯 右側固定總結區塊
    st.markdown(f"""
    <div class="summary-box">
        <div class="summary-title">📊 雙颱戰情與降雨全盤總結</div>
        <p><b>① 雙颱共存與正名情資：</b><br>
        原遠海系統 TD08 已正式升格並正名為<strong>第08號 艾維尼颱風（EWINIAR）</strong>。目前雙颱在西北太平洋共存。左側地圖已全面優化兩者路徑，並大幅加粗、拉亮艾維尼的遠海半透明圓圈，使其動態極度清晰。</p>
        <p><b>② 各國預報路徑高度收斂：</b><br>
        左側直條列顯示，各機構成員對米克拉的侵台概率判定均低於 6%。兩颱中心均不登陸台灣。米克拉將於 25日 最接近東部海域後大角度向東北轉向日本；而新正名的艾維尼颱風則在遠海即完成北轉，侵台概率精確為 0%。</p>
        <p><b>③ 迎風面屏東縣豪雨警戒：</b><br>
        <b>注意！沒颱風登陸不等於不下雨！</b>隨米克拉北上，其強大外圍環流配合偏南風，將在明後天對屏東迎風面直接灌入大量水氣。<br>
        • <b>6/25 (四) 【強降雨高峰】</b>：屏東降雨機率高達 <b>85%</b>，山區及恆春半島嚴防豪雨。<br>
        • <b>6/26 (五) 上半天</b>：水氣持續移入，降雨機率 <b>70%</b>，仍有大雨風險。</p>
    </div>
    """, unsafe_allow_html=True)
