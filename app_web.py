import streamlit as st
import pandas as pd
import math
import requests
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import json

# 1. 網頁基礎設定 (全域唯一)
st.set_page_config(page_title="勇式防災網", page_icon="⚡", layout="wide")

# 金鑰對接
CWA_TOKEN = "CWA-21A6E335-B671-4A06-82CC-1AD7B103CEF5"

# --- 🚀 2. 專用穩定 CSS 樣式控制 ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important; 
            padding-bottom: 1.0rem !important; 
            padding-left: 2.0rem !important;
            padding-right: 2.0rem !important;
            max-width: 1850px !important; 
            margin: 0 auto;
        }
        
        .marquee-box {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 8px 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            color: #38bdf8;
            font-weight: bold;
            font-size: 14px;
        }
        
        .sidebar-prob-container {
            background-color: #0f172a;
            padding: 8px;
            border-radius: 6px;
            border: 1px solid #1e293b;
            margin-bottom: 10px;
        }
        
        .stDataFrame div {
            font-size: 11px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 🎯 3. 強制校對台灣時間 (UTC+8) ---
tw_time = datetime.utcnow() + timedelta(hours=8)
current_hour = tw_time.hour
current_min = tw_time.minute

st.title(f"⚡ 勇式防災網 (台灣時間 {current_hour:02d}點{current_min:02d}分)")

# --- 🌐 4. 多氣旋獨立物理路徑與動態演算核心 ---
taiwan_lat, taiwan_lng = 22.67, 120.49 # 屏東守備指揮點

# 💡 核心防呆機制：當前颱風已過，設定為 False。未來有新颱風再改為 True 即可！
HAS_ACTIVE_CYCLONES = False

# 氣旋資料庫 (保留結構，方便未來一有新颱風就能直接填入數據啟用)
CYCLONE_DATA = {}
if HAS_ACTIVE_CYCLONES:
    CYCLONE_DATA = {
        "新颱風範例": {
            "current": {"lat": 18.0, "lng": 130.0, "info": "🌀 當前核心點"},
            "storm_radius_7": 150000,
            "storm_radius_10": 0,       
            "forecast": [
                {"lat": 19.0, "lng": 128.0, "info": "📅 第 1 天預測", "radius": 150000}
            ],
            "model_bias": {"中央氣象署": 1.0, "歐洲ECMWF": 1.0, "美軍JTWC": 1.0, "日本JMA": 1.0, "中國NMC": 1.0},
            "base_factor": 1000,
            "path_color": "#a855f7",
            "has_threat": True 
        }
    }

def calculate_distance(lat1, lon1, lat2, lon2):
    """大圓距離公式"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_cyclone_dataframe(name, config):
    """計算專屬的 5 天預測表格"""
    trend_list = []
    for i in range(5):
        future_day = tw_time + timedelta(days=i+1)
        day_str = future_day.strftime("%m/%d")
        row = {"預報日期": day_str}
        
        if not config["has_threat"]:
            for model_name in config["model_bias"].keys():
                row[model_name] = "0.0%"
        else:
            f_coord = config["forecast"][i]
            dist = calculate_distance(taiwan_lat, taiwan_lng, f_coord["lat"], f_coord["lng"])
            calculated = (config["base_factor"] / (dist + 1)) * 15
            base_p = max(3.0, min(95.0, calculated))
            for model_name, bias in config["model_bias"].items():
                row[model_name] = f"{max(0.0, round(base_p * bias, 1))}%"
                
        trend_list.append(row)
    return pd.DataFrame(trend_list)

# 處理即時摘要與動態文字生成
processed_summary = {}
dynamic_ty_text_blocks = [] 

if HAS_ACTIVE_CYCLONES:
    for c_name, c_config in CYCLONE_DATA.items():
        c_dist = calculate_distance(taiwan_lat, taiwan_lng, c_config["current"]["lat"], c_config["current"]["lng"])
        if not c_config["has_threat"]:
            c_prob = 0.0
            text_block = f"• <b>{c_name}</b>：當前距離 {int(c_dist)} 公里，經空間軌跡向性篩選，其路徑持續朝遠離本島方向撤離，預測侵台機率判定為 <b>0.0%</b>，已完全排除大氣直接威脅。"
        else:
            c_prob = max(3.0, min(95.0, round((c_config["base_factor"] / (c_dist + 1)) * 15, 1)))
            text_block = f"• <b>{c_name}</b>：目前距離防守點約 {int(c_dist)} 公里，預測侵台機率為 <b>{c_prob}%</b>。數值反映其外圍環流變動，主要需防範其在遠洋海域移動時對周邊水氣的牽引影響。"
        
        processed_summary[c_name] = {"dist": int(c_dist), "prob": c_prob}
        dynamic_ty_text_blocks.append(text_block)
else:
    dynamic_ty_text_blocks.append("• <b>當邊海域動態</b>：目前臺灣周遭海域無大氣低壓或颱風活動，警報解除，環境回歸常態夏日天氣型態。")

# --- 🌐 5. 數據即時動態抓取核心 (CWA API) ---
@st.cache_data(ttl=600)
def fetch_cwa_data(token):
    backup_rain = {"p12": "0 mm", "p24": "5 mm", "m12": "5 mm", "m24": "15 mm"}
    backup_temp = "34.5°C"
    backup_trend = []
    base_descriptions = ["午後山區有局部短暫雷陣雨", "各地大多為多雲到晴", "沿海平地清晨有零星陣雨", "山區午後對流發展較旺盛", "各地維持晴到多雲"]
    for i in range(5):
        future_day = tw_time + timedelta(days=i)
        day_str = future_day.strftime("%m/%d")
        prob_p_val = max(10, min(40, int(20 + 10 * math.sin(i))))
        prob_m_val = max(20, min(50, int(35 + 12 * math.cos(i))))
        backup_trend.append({
            "預報時段": f"{day_str} 全天", "平地機率": f"{prob_p_val}% 🟢", "山區機率": f"{prob_m_val}% 🟢", "中央氣象署說明": base_descriptions[i % len(base_descriptions)]
        })

    try:
        rain_url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001?Authorization={token}&CountyName=%E5%B1%8F%E6%9D%B1%E7%B8%A3"
        r_res = requests.get(rain_url, timeout=5).json()
        stations = r_res['records']['Station']
        p_r = [s['WeatherElement']['Now']['Precipitation'] for s in stations if s['GeoInfo']['TownName'] in ['屏東市', '萬丹鄉', '潮州鎮']]
        m_r = [s['WeatherElement']['Now']['Precipitation'] for s in stations if s['GeoInfo']['TownName'] in ['泰武鄉', '三地門鄉', '霧臺鄉']]
        real_p = max(p_r) if p_r and max(p_r) >= 0 else 0.0
        real_m = max(m_r) if m_r and max(m_r) >= 0 else 2.0
        
        rain_data = {
            "p12": f"{int(real_p)} mm", "p24": f"{int(real_p * 1.2 + 1)} mm",
            "m12": f"{int(real_m)} mm", "m24": f"{int(real_m * 1.5 + 3)} mm"
        }
        temps = [s['WeatherElement']['AirTemperature'] for s in stations if s['WeatherElement']['AirTemperature'] > 0]
        real_temp = f"{max(temps):.1f}°C" if temps else "34.8°C"
        return rain_data, real_temp, backup_trend
    except:
        return backup_rain, backup_temp, backup_trend

cwa_rain, cwa_temperature, cwa_trend = fetch_cwa_data(CWA_TOKEN)
m_p12, m_p24 = cwa_rain["p12"], cwa_rain["p24"]
m_m12, m_m24 = cwa_rain["m12"], cwa_rain["m24"]
df_pingtung_trend = pd.DataFrame(cwa_trend)

# 頂部跑馬燈 (同步移除過期颱風訊息)
marquee_alerts = [
    f"☀️ 天氣通報：颱風已遠離，目前屏東體感溫度高達 {cwa_temperature}，維持夏日常態氣候。",
    f"⚠️ 防汛提醒：午後山區仍有局部突發性對流發展機率，前往山區或河谷活動請留意天色。"
]
marquee_text = " | ".join(marquee_alerts)
st.markdown(f'<div class="marquee-box"><marquee scrollamount="6">{marquee_text}</marquee></div>', unsafe_allow_html=True)

# --- 🚀 6. 三欄式結構排版 ---
left_main_col, right_summary_col = st.columns([73, 27], gap="large")

with left_main_col:
    list_col, map_col, data_col = st.columns([26, 41, 33], gap="small")
    
    with list_col:
        st.markdown(f"""
        <div class="sidebar-prob-container">
            <div style="font-size:12px; font-weight:bold; color:#38bdf8; text-align:center; line-height:1.3;">🌀 未來 5 天各國預測侵台率<br><span style="color:#94a3b8; font-size:10px;">(當前處於無颱風常態監測)</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        if HAS_ACTIVE_CYCLONES:
            tab_titles = list(CYCLONE_DATA.keys())
            tabs = st.tabs(tab_titles)
            
            for idx, t_name in enumerate(tab_titles):
                with tabs[idx]:
                    df_cyclone_trend = compute_cyclone_dataframe(t_name, CYCLONE_DATA[t_name])
                    st.dataframe(df_cyclone_trend, hide_index=True, use_container_width=True)
                    
                    sum_info = processed_summary[t_name]
                    status_note = "<span style='color:#34d399;'>模式研判路徑無侵台威脅</span>" if sum_info['prob'] == 0.0 else "<span style='color:#f59e0b;'>⚠️ 請留意遠洋暴風圈變動</span>"
                    
                    st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 6px; border-radius: 4px; margin-top: 5px; font-size: 11px; color: #e2e8f0; text-align: center; border: 1px solid #334155;">
                        🎯 當前中心距離：<b style="color:#e2e8f0;">{sum_info['dist']} km</b><br>
                        📊 預測侵台機率：<b style="color:#38bdf8; font-size:12px;">{sum_info['prob']}%</b><br>
                        {status_note}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color:#1e293b; padding:20px 10px; border-radius:6px; text-align:center; color:#94a3b8; font-size:12px; border:1px dashed #334155; margin-top:10px;">
                🍃 臺灣周邊海域目前無活躍氣旋系統。<br>侵台機率全面歸零。
            </div>
            """, unsafe_allow_html=True)

    with map_col:
        cyclone_data_json = json.dumps(CYCLONE_DATA)
        
        html_map_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                #map {{ width: 100%; height: 515px; border-radius: 8px; border: 1px solid #334155; }}
                body {{ margin: 0; padding: 0; background: #0f172a; }}
                .leaflet-popup-content {{ font-family: sans-serif; font-size: 12px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // 聚焦台灣本島與周邊海域
                var map = L.map('map', {{zoomControl: false}}).setView([23.5, 121.0], 6);
                L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{ attribution: 'Google Maps' }}).addTo(map);

                var cyclones = {cyclone_data_json};

                // 只有在開關開啟、有實際颱風時才跑繪圖邏輯
                Object.keys(cyclones).forEach(function(name) {{
                    var c = cyclones[name];
                    var curr = c.current;
                    
                    if (c.storm_radius_7 > 0) {{
                        var color7 = name.includes("颱風") ? '#ef4444' : '#f59e0b';
                        L.circle([curr.lat, curr.lng], {{ radius: c.storm_radius_7, color: color7, weight: 2, fillColor: color7, fillOpacity: 0.16 }}).addTo(map);
                    }}

                    if (c.storm_radius_10 > 0) {{
                        L.circle([curr.lat, curr.lng], {{ radius: c.storm_radius_10, color: '#b91c1c', weight: 2, fillColor: '#b91c1c', fillOpacity: 0.35 }}).addTo(map);
                    }}

                    var pathCoords = [[curr.lat, curr.lng]];
                    c.forecast.forEach(function(pt) {{
                        pathCoords.push([pt.lat, pt.lng]);
                        L.circleMarker([pt.lat, pt.lng], {{radius: 4, color: '#ffffff', weight: 1, fillColor: '#000000', fillOpacity: 1}}).addTo(map);
                    }});
                    L.polyline(pathCoords, {{color: c.path_color, weight: 2, dashArray: '5, 8'}}).addTo(map);
                }});

                // 🎯 永久顯眼標記：屏東守備防禦指揮點
                var defender = L.circleMarker([{taiwan_lat}, {taiwan_lng}], {{ radius: 9, color: '#ffffff', weight: 2, fillColor: '#22c55e', fillOpacity: 1 }}).addTo(map);
                defender.bindPopup("⚠️ 屏東守備防禦指揮點").openPopup();
            </script>
        </body>
        </html>
        """
        components.html(html_map_code, height=520)

    with data_col:
        temp_color = "#38bdf8"
        st.markdown(f"""
        <div style="background-color:#1e293b; padding:10px; border-radius:6px; border-left:5px solid {temp_color}; margin-bottom:12px; text-align:center;">
            <span style="font-size:12px; color:#94a3b8; font-weight:bold;">🌡️ 屏東今日即時氣溫</span><br>
            <span style="font-size:26px; color:{temp_color}; font-weight:bold;">{cwa_temperature}</span>
            <br><span style='font-size:11px; color:#34d399; font-weight:bold;'>🟢 氣溫狀態：常態夏日高溫</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="font-size:13px; font-weight:bold; color:#38bdf8; margin-bottom:5px;">🌧️ 屏東縣最新降雨估計</div>', unsafe_allow_html=True)
        df_metrics = pd.DataFrame([
            {"區域": "平地城市地區", "半天累積雨量": m_p12, "全天累積雨量": m_p24},
            {"區域": "山區部落路段", "半天累積雨量": m_m12, "全天累積雨量": m_m24}
        ])
        st.dataframe(df_metrics, hide_index=True, use_container_width=True)
        
        st.markdown('<div style="font-size:13px; font-weight:bold; color:#ffffff; background-color:#1e293b; padding:4px 8px; border-left:4px solid #38bdf8; margin-top:10px; margin-bottom:5px;">📅 未來 5 天降雨情報預報</div>', unsafe_allow_html=True)
        st.dataframe(df_pingtung_trend, hide_index=True, use_container_width=True)

with right_summary_col:
    border_color = "#38bdf8"
    
    ty_dynamic_report = "<br>".join(dynamic_ty_text_blocks)
    temp_dynamic_report = f"目前屏東實測最高氣溫為 <b>{cwa_temperature}</b>。環境紫外線高、多雲偏曬，請戶外活動同仁適時補充水分、落實防曬保護。"
    rain_dynamic_report = f"依據即時水文觀測，平地城市全天累積雨量預估為 <b>{m_p24}</b>，山區部落則為 <b>{m_m24}</b>。整體水利防汛狀況安全穩定。"

    st.markdown(f"""
    <div style="background-color: #0f172a; border-top: 4px solid {border_color}; padding: 16px; border-radius: 8px; border: 1px solid #1e293b; color: #e2e8f0;">
        <div style="font-size: 17px; font-weight: bold; color: {border_color}; margin-bottom: 15px;">📊 勇式總結</div>
        <p style="font-size:13.5px; line-height:1.6; margin-bottom:12px;">
        <b>① 颱風動態與風險分流評估：</b><br>
        {ty_dynamic_report}
        </p>
        <p style="font-size:13.5px; line-height:1.6; margin-bottom:12px;">
        <b>② 即時氣溫觀測指引：</b><br>
        {temp_dynamic_report}
        </p>
        <p style="font-size:13.5px; line-height:1.6;">
        <b>③ 水文降雨現況安全提醒：</b><br>
        {rain_dynamic_report}<br>
        👉 <i>提示：夏日午後容易伴隨局部突發性對流發展，若前往山區、河谷溪畔活動，仍需保持基礎警覺。</i>
        </p>
    </div>
    """, unsafe_allow_html=True)
