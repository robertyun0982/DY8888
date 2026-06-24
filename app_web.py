import math
from datetime import datetime

# 1. 定義台灣中心基準點 (以台灣地理中心點南投埔里附近，或選取台北/高雄作權重，此處取北緯23.97, 東經120.97)
TAIWAN_CENTER = {"lat": 23.97, "lon": 120.97}

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    使用 Haversine 公式計算地球上兩點之間的大圓距離 (單位: 公里)
    """
    R = 6371.0  # 地球平均半徑 (km)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

# 2. 模擬從各國氣象機構 API / 報文收集到的最新氣旋數據 (颱風、熱帶低壓 TD、熱帶擾動 9xW)
raw_global_data = [
    {
        "id": "202615",
        "name": "米克拉 (MEKKHALA)",
        "type": "Typhoon",
        "sources": {
            "CWA_TW": {"lat": 22.3, "lon": 124.8, "pressure": 950, "max_wind": 40, "update_time": "2026-06-24 13:00"},
            "JMA_JP": {"lat": 22.4, "lon": 124.9, "pressure": 955, "max_wind": 38, "update_time": "2026-06-24 12:45"},
            "JTWC_US": {"lat": 22.2, "lon": 124.6, "pressure": 948, "max_wind": 42, "update_time": "2026-06-24 13:00"},
            "NMC_CN": {"lat": 22.3, "lon": 124.8, "pressure": 950, "max_wind": 40, "update_time": "2026-06-24 13:00"}
        }
    },
    {
        "id": "TD_202603",
        "name": "熱帶性低氣壓 TD",
        "type": "Tropical Depression",
        "sources": {
            "CWA_TW": {"lat": 20.7, "lon": 118.5, "pressure": 1000, "max_wind": 15, "update_time": "2026-06-24 11:00"},
            "HKO_HK": {"lat": 20.5, "lon": 118.2, "pressure": 1002, "max_wind": 14, "update_time": "2026-06-24 11:15"},
            "JMA_JP": {"lat": 20.8, "lon": 118.7, "pressure": 1000, "max_wind": 15, "update_time": "2026-06-24 10:45"}
        }
    },
    {
        "id": "95W",
        "name": "熱帶擾動 INVEST 95W",
        "type": "Tropical Disturbance",
        "sources": {
            "JTWC_US": {"lat": 15.0, "lon": 135.0, "pressure": 1008, "max_wind": 10, "update_time": "2026-06-24 08:00"},
            "JMA_JP": {"lat": 15.5, "lon": 135.2, "pressure": 1010, "max_wind": 8, "update_time": "2026-06-24 09:00"}
        }
    }
]

# 3. 核心處理與過濾邏輯
def process_cyclone_data(data, max_distance_km=1000.0):
    filtered_results = []
    
    for cyclone in data:
        # 計算各國預報位置的平均值作為基準參考點，或以台灣 CWA 為主 (這裡採各國報文的平均位置)
        lats = [info["lat"] for info in cyclone["sources"].values()]
        lons = [info["lon"] for info in cyclone["sources"].values()]
        
        avg_lat = sum(lats) / len(lats)
        avg_lon = sum(lons) / len(lons)
        
        # 計算此氣旋與台灣的距離
        distance_to_taiwan = haversine_distance(
            TAIWAN_CENTER["lat"], TAIWAN_CENTER["lon"], 
            avg_lat, avg_lon
        )
        
        # 篩選 1000 公里以內的氣旋
        if distance_to_taiwan <= max_distance_km:
            cyclone_info = {
                "id": cyclone["id"],
                "name": cyclone["name"],
                "type": cyclone["type"],
                "distance_km": round(distance_to_taiwan, 2),
                "avg_position": {"lat": round(avg_lat, 2), "lon": round(avg_lon, 2)},
                "source_data": cyclone["sources"]
            }
            filtered_results.append(cyclone_info)
            
    return filtered_results

# 4. 執行過濾並格式化輸出
if __name__ == "__main__":
    target_distance = 1000.0
    monitored_cyclones = process_cyclone_data(raw_global_data, max_distance_km=target_distance)
    
    print(f"=== 台灣周邊 {target_distance} 公里內熱帶系統監測報告 ===")
    print(f"基準點：台灣地理中心 (北緯 {TAIWAN_CENTER['lat']}, 東經 {TAIWAN_CENTER['lon']})\n")
    
    if not monitored_cyclones:
        print("目前台灣 1000 公里內無活躍的颱風或熱帶低壓。")
    else:
        for idx, item in enumerate(monitored_cyclones, 1):
            print(f"[{idx}] {item['type']} - {item['name']}")
            print(f"    -> 距台距離: {item['distance_km']} 公里")
            print(f"    -> 綜合平均位置: 北緯 {item['avg_position']['lat']}, 東經 {item['avg_position']['lon']}")
            print(f"    -> 各國多源觀測數據對比:")
            
            for org, details in item["source_data"].items():
                print(f"       * [{org}] 位置({details['lat']}, {details['lon']}) | 中心氣壓: {details['pressure']} hPa | 最大風速: {details['max_wind']} m/s")
            print("-" * 60)
