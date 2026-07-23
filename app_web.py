import requests
import re

def get_real_td_position(token):
    """
    實時對接氣象署 API 抓取熱帶低壓 (TD)
    不使用任何預設/假的座標
    """
    # 氣象署颱風與熱帶低壓 Open Data API
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/W-C0034-005?Authorization={token}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('success') == 'true':
            return None, "API 認證或請求失敗"

        # 1. 嘗試直接從結構化欄位抓取
        sections = data.get('records', {}).get('tropicalCyclones', {}).get('tropicalCyclone', [])
        for tc in sections:
            # 尋找分析資料
            analysis = tc.get('analysisData', {}).get('fix', [])
            for fix in analysis:
                lat = fix.get('latitude')
                lng = fix.get('longitude')
                wind = fix.get('maxWindSpeed')
                
                # 安全轉碼：避免 null 導致程式崩潰
                if lat and lng:
                    return {
                        "name": tc.get('cwaTyphoonName', '熱帶性低氣壓'),
                        "lat": float(lat),
                        "lng": float(lng),
                        "wind": wind if wind else "15"
                    }, "成功透過結構欄位抓取"

        # 2. 備援方案：若欄位為 null，強行掃描整份 JSON 文字中的經緯度描述
        raw_text = str(data)
        lat_match = re.search(r'北緯\s*([\d\.]+)\s*度', raw_text)
        lng_match = re.search(r'東經\s*([\d\.]+)\s*度', raw_text)
        
        if lat_match and lng_match:
            return {
                "name": "熱帶性低氣壓 (TD)",
                "lat": float(lat_match.group(1)),
                "lng": float(lng_match.group(1)),
                "wind": "15"
            }, "成功透過報文文字解析座標"

        return None, "氣象署目前無運作中的熱帶低壓數據"

    except Exception as e:
        return None, f"連線或解析例外：{str(e)}"
