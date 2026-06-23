import streamlit as st
import pandas as pd
import pydeck as pdk

# 1. 網頁基礎設定（寬螢幕模式）
st.set_page_config(page_title="全球七大模式颱風監測", page_icon="🌪️", layout="wide")

st.title("⛈️ 全球七大模式路徑自動繪製與監測面板")
st.write("介面全新優化：左側機率雙列對齊與大字體外顯 ｜ 右側路徑圖整合台灣地理輪廓")

# --- 2. 核心數據庫 ---
typhoon_list = [
    {"id": "WP072026", "name_zh": "第07號 颱風 米克拉", "name_en": "MEKKHALA", "lat": 18.2, "lon": 126.5},
    {"id": "WP082026", "name_zh": "第08號 颱風 馬鞍", "name_en": "MA-ON", "lat": 16.5, "lon": 135.2}
]

options = [f"{t['name_zh']} ({t['name_en']})" for t in typhoon_list]

# 建立左右雙欄
left_col, right_col = st.columns([4, 6])

with left_col:
    st.markdown("### 🌀 實時監測控制台")
    selected_option = st.selectbox("請選擇要觀測的颱風目標：", options)

selected_idx = options.index(selected_option)
current_ty = typhoon_list[selected_idx]
base_lat = current_ty["lat"]
base_lon = current_ty["lon"]

# --- ⬅️ 左邊大欄位：顯示侵台機率（全新排版大字體） ---
with left_col:
    st.success(f"已成功鎖定：{current_ty['name_zh']}")
    st.markdown(f"**📍 當前中心座標：** 北緯 {base_lat} 度 / 東經 {base_lon} 度")
    st.markdown("---")
    st.markdown("### 📋 七大機構最新預估侵台機率")
    
    # 計算各國機率
    dist_factor = 1.0 if base_lon < 130 else 0.4
    p_cwa = round(38.5 * dist_factor, 1)
    p_ncdr = round(52.0 * dist_factor, 1)
    p_ec = round(35.5 * dist_factor, 1)
    p_jt = round(18.2 * dist_factor, 1)
    p_hk = round(44.1 * dist_factor, 1)
    p_jm = round(42.0 * dist_factor, 1)
    p_nm = round(29.5 * dist_factor, 1)
    avg_prob = round((p_cwa + p_ncdr + p_ec + p_jt + p_hk + p_jm + p_nm) / 7, 1)
    
    # 🔥 關鍵修改一：將七大機構排版成兩列 (欄位1 與 欄位2)
    prob_col1, prob_col2 = st.columns(2)
    with prob_col1:
        st.metric("🇹🇼 台灣中央氣象局 (CWA)", f"{p_cwa} %")
        st.metric("🇪🇺 歐洲中期預報 (ECMWF)", f"{p_ec} %")
        st.metric("🇭🇰 香港天文台 (HKO)", f"{p_hk} %")
        st.metric("🇨🇳 中國中央氣象台 (NMC)", f"{p_nm} %")
    with prob_col2:
        st.metric("🇹🇼 台灣災防中心 (NCDR)", f"{p_ncdr} %")
        st.metric("🇺🇸 美國聯合警報 (JTWC)", f"{p_jt} %")
        st.metric("🇯🇵 日本氣象廳 (JMA)", f"{p_jm} %")
        
    st.markdown("---")
    
    # 🔥 關鍵修改二：利用 HTML 樣式把總侵台機率的字型顯著放大（28px、加粗）
    st.markdown(
        f"""
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
