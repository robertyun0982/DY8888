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

# --- 🚀 2. 戰情室專用高級 CSS 操控 (色彩美學聯動升級) ---
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
            transition: all 0.3s ease;
        }
        /* 各國名稱字體：全白加粗 */
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
        
        /* 🎨 7國色彩美學定義：完美聯動頂部框線與底部地圖線 */
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

        /* 地圖區自訂圖例面板 */
        .map-container {
            position: relative;
        }
        .legend-panel {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(15, 23, 42, 0.9);
            border: 1px solid #475569;
            padding: 12px;
            border-radius: 6px;
            z-index: 999;
            color: #ffffff
