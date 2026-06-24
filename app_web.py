import streamlit as st
import pandas as pd
import pydeck as pdk
import math
import time

# 1. 頁面基礎設置
st.set_page_config(page_title="勇式颱風侵台概率暨屏東縣降雨監測", page_icon="⚡", layout="wide")

# 2. 核心 CSS (確保版型大器、無切字、且所有欄位高度同步)
st.markdown("""
    <style>
        .block-container { max-width: 1800px !important; }
        .main-title { font-size: 32px !important; font-weight: bold !important; color: #f8fafc !important; margin-bottom: 10px; }
        .marquee-box { background-color: #1e293b; border: 1px solid #334155; padding: 10px; border-radius: 8px; color: #38bdf8; font-weight: bold; margin-bottom: 20px; }
        .card { background-color: #0f172a; border: 1px solid #1e293b; padding: 20px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. 標題與跑馬燈
st.markdown('<div class="main-title">⚡ 勇式颱風侵台概率暨屏東縣降雨監測</div>', unsafe_allow_html=True)

# 模擬數據：這裏保留了所有的七國細節與預測路徑
DATA = {
    "🌀 第07號 米克拉颱風 (強烈颱風)": {
        "probs": [("CWA", 1.2), ("NCDR", 0.8), ("ECMWF", 2.1), ("JTWC", 2.5), ("JMA", 1.4), ("HKO", 1.1), ("NMC", 1.3)],
        "circles": [
            {"time": "6/24", "lon": 126.8, "lat": 23.1, "radius": 150000, "color": [255, 149, 0, 80]},
            {"time": "6/25", "lon": 128.0, "lat": 25.5, "radius": 180000, "color": [255, 149, 0, 70]},
            {"time": "6/26", "lon": 129.5, "lat": 28.0, "radius": 200000, "color": [255, 59, 48, 60]},
            {"time": "6/27", "lon": 131.0, "lat": 30.5, "radius": 220000, "color": [255, 59, 48, 50]},
            {"time": "6/28", "lon": 133.0, "lat": 33.0, "radius": 250000, "color": [255, 59, 48, 40]}
        ],
        "paths": [{"path": [[124.6, 20.2], [126.8, 23.1], [128.0, 25.5], [129.5, 28.0], [131.0, 30.5], [133.0, 33.0]], "color": [0, 255, 200]}],
        "rain": pd.DataFrame({"日期": ["6/24", "6/25", "6/26", "6/27", "6/28"], "降雨概率(%)": [45, 75, 65, 40, 30], "說明": ["陣雨", "豪雨高峰", "午後雷陣雨", "局部短暫雨", "晴午後雨"]})
    },
    "🌀 第08號 無花果颱風 (HIGOS)": {
        "probs": [("CWA", 0), ("NCDR", 0), ("ECMWF", 0), ("JTWC", 0), ("JMA", 0), ("HKO", 0), ("NMC", 0)],
        "circles": [{"time": "6/24", "lon": 139.5, "lat": 20.5, "radius": 200000, "color": [236, 72, 153, 90]}],
        "paths": [{"path": [[146.0, 14.5], [143.0, 17.0], [139.5, 20.5]], "color": [255, 0, 255]}],
        "rain": pd.DataFrame({"日期": ["6/24", "6/25", "6/26", "6/27", "6/28"], "降雨概率(%)": [10, 10, 10, 10, 15], "說明": ["無影響", "無影響", "無影響", "無影響", "無影響"]})
    }
}

option = st.selectbox("🎯 選擇監測標的：", list(DATA.keys()))
data = DATA[option]
avg = round(sum([p[1] for p in data["probs"]]) / 7, 1)

st.markdown(f'<div class="marquee-box"><marquee>💡 勇式小叮嚀：監測目標【{option}】。7國平均侵台機率：{avg}%。屏東縣降雨機率預報已更新。 🔄</marquee></div>', unsafe_allow_html=True)

# 4. 版面分割：左中右
col1, col2, col3 = st.columns([20, 50, 30])

with col1:
    st.markdown('<div class="card"><b>🌐 7國機率概算</b><br><br>'+'<br>'.join([f"{p[0]}: {p[1]}%" for p in data["probs"]])+'<br><hr><b>平均值: '+str(avg)+'%</b></div>', unsafe_allow_html=True)

with col2:
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(latitude=25, longitude=130, zoom=3.8),
        layers=[
            pdk.Layer("ScatterplotLayer", pd.DataFrame(data["circles"]), get_position=["lon", "lat"], get_radius="radius", get_fill_color="color"),
            pdk.Layer("PathLayer", pd.DataFrame(data["paths"]), get_path="path", get_color="color", width_min_pixels=4)
        ]
    ))

with col3:
    st.markdown('<div class="card"><b>📊 勇式總結</b><br><br>1. <b>侵台機率：</b> 綜合預測均值為 {avg}%。<br>2. <b>屏東監測：</b> 根據最新水氣分析，降雨風險如下：</div>', unsafe_allow_html=True)
    st.dataframe(data["rain"], hide_index=True, use_container_width=True)
