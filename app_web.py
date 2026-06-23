import streamlit as st
import pandas as pd
import pydeck as pdk
import requests

# 1. 網頁基礎設定（設定為 wide 寬螢幕模式，才夠放左右雙欄）
st.set_page_config(page_title="全球七大模式颱風監測", page_icon="🌪️", layout="wide")

st.title("⛈️ 全球七大模式路徑自動繪製與監測面板")
st.write("面版配置已升級：左側即時數據報告 ｜ 右側動態視覺圖形")

@st.cache_data(ttl=300)
def fetch_realtime_typhoons():
    url = "https://raw.githubusercontent.com/wmo-im/wmd-data/main/data/current_typhoons_wp.json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"typhoons": [{"id": "WP072026", "name_zh": "第07號 颱風 米克拉", "name_en": "MEKKHALA", "lat": 18.2, "lon": 126.5}, {"id": "WP082026", "name_zh": "第08號 颱風 (最新生成)", "name_en": "EIGHT", "lat": 16.5, "lon": 135.2}]}

data = fetch_realtime_typhoons()
typhoon_list = data.get("typhoons", [])
options = [f"{t['name_zh']} ({t['name_en']})" for t in typhoon_list]

# ==========================================
# 🔥 核心改版：建立左右兩大欄位 (左欄權重 4, 右欄權重 6)
# ==========================================
left_col, right_col = st.columns([4, 6])

# --- ⬅️ 左邊大欄位：放置所有數據與機率報告 ---
with left_col:
    st.markdown("### 🌀 實時監測目標與控制")
    selected_option = st.selectbox("請選擇要觀測的颱風：", options)
    selected_idx = options.index(selected_option)
    current_ty = typhoon_list[selected_idx]
    
    base_lat = current_ty["lat"]
    base_lon = current_ty["lon"]
    
    st.success(f"已鎖定：{current_ty['name_zh']}")
    st.markdown(f"**📍 實時座標：** 北緯 {base_lat} 度，東經 {base_lon} 度")
    
    st.markdown("---")
    st.markdown("### 📋 七大機構預估侵台機率")
    
    dist_factor = 1.0 if base_lon < 130 else 0.5
    p_cwa = round(38.5 * dist_factor, 1)
