with map_col:
        # 🎯 🎯 【純粹高精確圓點地圖圖層】 🎯 🎯
        # 💡 已修正：補齊了 JavaScript 結尾處的 f-string 大括號轉義
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
                .leaflet-tooltip {{
                    background: rgba(15, 23, 42, 0.9);
                    border: 1px solid #38bdf8;
                    color: #fff;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map', {{zoomControl: false}}).setView([20.0, 122.0], 5);

                L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{
                    attribution: 'Google Maps'
                }}).addTo(map);

                // 大面積半透明覆蓋圈
                var pathCircles = [
                    {{lat: 16.5, lng: 113.5, col: '#06b6d4', op: 0.15, rad: 180000}},
                    {{lat: {td09_lat}, lng: {td09_lng}, col: '#ef4444', op: 0.25, rad: 200000}},
                    {{lat: 18.5, lng: 110.8, col: '#ef4444', op: 0.20, rad: 220000}},
                    {{lat: 19.8, lng: 109.2, col: '#06b6d4', op: 0.15, rad: 220000}},
                    
                    {{lat: {bawi_lat}, lng: {bawi_lng}, col: '#ef4444', op: 0.30, rad: 240000}}, 
                    {{lat: 18.2, lng: 134.0, col: '#ef4444', op: 0.20, rad: 250000}},
                    {{lat: 19.5, lng: 130.0, col: '#ef4444', op: 0.15, rad: 260000}}
                ];

                pathCircles.forEach(function(pt) {{
                    L.circle([pt.lat, pt.lng], {{
                        radius: pt.rad, 
                        color: pt.col,
                        weight: 1.2,
                        fillColor: pt.col,
                        fillOpacity: pt.op
                    }}).addTo(map);
                }});

                // 定位圓點
                var nodes = [
                    {{lat: {td09_lat}, lng: {td09_lng}, info: "🌀 熱帶低壓 TD09 (南海西沙海面當前核心)", col: '#f59e0b', rad: 8}},
                    {{lat: {bawi_lat}, lng: {bawi_lng}, info: "🌀 巴威颱風 (BAWI) (東部遠洋當前核心)", col: '#f59e0b', rad: 8}},
                    {{lat: {taiwan_lat}, lng: {taiwan_lng}, info: "⚠️ 屏東守備防禦指揮點", col: '#ef4444', rad: 9}},
                    
                    // 📅 5 天精確預測位置
                    {{lat: 18.5, lng: 111.0, info: "📅 第 1 天預測位置 (逐漸接近海南島沿海)", col: '#38bdf8', rad: 6}},
                    {{lat: 19.6, lng: 109.5, info: "📅 第 2 天預測位置 (中心預估登陸海南島)", col: '#34d399', rad: 6}},
                    {{lat: 20.8, lng: 108.2, info: "📅 第 3 天預測位置 (進入北部灣海面)", col: '#a855f7', rad: 6}},
                    {{lat: 22.0, lng: 106.8, info: "📅 第 4 天預測位置 (登陸華南內陸並減弱)", col: '#94a3b8', rad: 6}},
                    {{lat: 23.2, lng: 105.5, info: "📅 第 5 天預測位置 (減弱消散為一般低壓)", col: '#64748b', rad: 6}}
                ];

                nodes.forEach(function(n) {{
                    var marker = L.circleMarker([n.lat, n.lng], {{
                        radius: n.rad,
                        color: '#0f172a',
                        weight: 2,
                        fillColor: n.col,
                        fillOpacity: 1
                    }}).addTo(map).bindPopup(n.info);
                    
                    marker.bindTooltip(n.info.split(" (")[0], {{permanent: false, direction: 'top'}});
                }});
            </script>
        </body>
        </html>
        """
        components.html(html_map_code, height=520)
