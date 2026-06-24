import streamlit as st
import pandas as pd
import pydeck as pdk
import time
import math

# 基礎設定
st.set_page_config(page_title="勇式防汛戰情室", page_icon="⚡", layout="wide")

# CSS 優化：確保標題完整與容器排版彈性
st.markdown("""
    <style>
        .title-text { font-size: 30px; font-weight: bold; color: #f8fafc; margin-bottom: 20px; }
        .data-card { background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #1e293b; }
        .metric-val { font-size: 20px; font-weight: bold; color: #38bdf8; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title-text">⚡ 勇式颱風侵台概率暨屏東縣降雨監測</div>', unsafe_allow_html=True)

# 核心氣象資料庫（保留詳細數值）
REAL_TIME_DATA = {
    "🌀 第07號 米克拉颱風": {
        "probs": [("CWA", 1.2), ("NCDR", 0.8), ("ECMWF", 2.1), ("JTWC", 2.5), ("JMA", 1.4), ("HKO", 1.1), ("NMC", 1.3)],
        "circles": [
            {"time": "6/24", "lon": 126.8, "lat": 23.1, "radius": 150000, "color": [255, 149, 0, 80]},
            {"time": "6/25", "lon": 128.0, "lat": 25.5, "radius": 180000, "color": [255, 149, 0, 70]},
            {"time": "6/26", "lon": 129.5, "lat": 28.0, "radius": 200000, "color": [255, 59, 48, 60]},
            {"time": "6/27", "lon": 131.0, "lat": 30.5, "radius": 220000, "color": [255, 59, 48, 50]},
            {"time": "6/28", "lon": 133.0, "lat": 33.0, "radius": 250000, "color": [255, 59, 48, 40]}
        ],
        "paths": [{"path": [[124.6, 20.2], [126.8, 23.1], [128.0, 25.5], [129.5, 28.0], [131.0, 30.5], [133.0, 33.0]], "color": [0, 255, 200]}],
        "rain": pd.DataFrame({"日期": ["6/24", "6/25", "6/26", "6/27", "6/28"], "降雨概率(%)": [45, 75, 65, 40, 30], "說明": ["外圍環流", "降雨高峰", "午後雷陣雨", "局部短暫雨", "穩定"]})
    },
    "🌀 第08號 無花果颱風 (HIGOS)": {
        "probs": [("CWA", 0.0), ("NCDR", 0.0), ("ECMWF", 0.0), ("JTWC", 0.0), ("JMA", 0.0), ("HKO", 0.0), ("NMC", 0.0)],
        "circles": [{"time": "6/24", "lon": 139.5, "lat": 20.5, "radius": 200000, "color": [236, 72, 153, 90]}],
        "paths": [{"path": [[146.0, 14.5], [143.0, 17.0], [139.5, 20.5]], "color": [255, 0, 255]}],
        "rain": pd.DataFrame({"日期": ["6/24", "6/25", "6/26", "6/27", "6/28"], "降雨概率(%)": [10, 10, 10, 10, 15], "說明": ["無影響", "無影響", "無影響", "無影響", "穩定"]})
    }
}

# 互動選單
option = st.selectbox("🎯 選擇受偵測威脅物：", list(REAL_TIME_DATA.keys()))
data = REAL_TIME_DATA[option]

# 版面佈局：左 (數據) | 中 (地圖) | 右 (總結)
col1, col2, col3 = st.columns([20, 50, 30])

with col1:
    st.markdown("### 🌐 7國機率概算")
    df_probs = pd.DataFrame(data["probs"], columns=["機構", "機率(%)"])
    st.table(df_probs)
    avg_p = df_probs["機率(%)"].mean()
    st.metric("平均侵台機率", f"{avg_p:.1f}%")

with col2:
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(latitude=25, longitude=130, zoom=3.8),
        layers=[
            pdk.Layer("ScatterplotLayer", pd.DataFrame(data["circles"]), get_position=["lon", "lat"], get_radius="radius", get_fill_color="color"),
            pdk.Layer("PathLayer", pd.DataFrame(data["paths"]), get_path="path", get_color="color", width_min_pixels=4)
        ]
    ))

with col3:
    st.markdown("### 📊 屏東防汛監測")
    st.dataframe(data["rain"], hide_index=True, use_container_width=True)
    st.info("💡 勇式總結：米克拉颱風已遠離，但外圍水氣仍持續影響屏東迎風面，請留意 6/25-6/26 的降雨強度。")
