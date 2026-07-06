with map_col:
        # 🎯 🎯 【純粹高精確圓點地圖圖層】 🎯 🎯
        html_map_code = """
        <!DOCTYPE html>
        <html>
        <head>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                #map { width: 100%; height: 515px; border-radius: 8px; border: 1px solid #334155; }
                body { margin: 0; padding: 0; background: #0f172a; }
                .leaflet-popup-content { font-family: sans-serif; font-size: 12px; font-weight: bold; }
                /* 氣象站文字提示窗自訂樣式，輔助圓點點擊 */
                .leaflet-tooltip {
                    background: rgba(15, 23, 42, 0.9);
                    border: 1px solid #38bdf8;
                    color: #fff;
                    font-weight: bold;
                    font-size: 11px;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map', {zoomControl: false}).setView([21.5, 125.0], 5);

                L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
                    attribution: 'Google Maps'
                }).addTo(map);

                // 已移除原本的 L.polygon 梯形外框

                // 大面積半透明覆蓋圈
                var pathCircles = [
                    {lat: 16.0, lng: 124.0, col: '#06b6d4', op: 0.12, rad: 200000},
                    {lat: 17.5, lng: 122.5, col: '#06b6d4', op: 0.18, rad: 200000},
                    {lat: 19.2, lng: 120.8, col: '#06b6d4', op: 0.25, rad: 220000},
                    {lat: 21.0, lng: 118.5, col: '#ef4444', op: 0.35, rad: 240000}, 
                    {lat: 23.0, lng: 116.5, col: '#ef4444', op: 0.25, rad: 250000},
                    {lat: 26.0, lng: 115.0, col: '#ef4444', op: 0.18, rad: 260000},
                    {lat: 30.0, lng: 114.2, col: '#ef4444', op: 0.12, rad: 270000},
                    
                    {lat: 17.0, lng: 142.0, col: '#a855f7', op: 0.12, rad: 200000},
                    {lat: 17.2, lng: 140.0, col: '#a855f7', op: 0.18, rad: 200000},
                    {lat: 17.5, lng: 137.5, col: '#ef4444', op: 0.35, rad: 240000}, 
                    {lat: 17.6, lng: 134.0, col: '#ef4444', op: 0.25, rad: 250000},
                    {lat: 18.0, lng: 130.0, col: '#ef4444', op: 0.18, rad: 260000},
                    {lat: 19.5, lng: 125.0, col: '#ef4444', op: 0.12, rad: 270000}
                ];

                pathCircles.forEach(function(pt) {
                    L.circle([pt.lat, pt.lng], {
                        radius: pt.rad, 
                        color: pt.col,
                        weight: 1.2,
                        fillColor: pt.col,
                        fillOpacity: pt.op
                    }).addTo(map);
                });

                // 🔴 定位圓點
                var nodes = [
                    {lat: 21.0, lng: 118.5, info: "🌀 熱帶低壓 TD09 (當前核心位置)", col: '#f59e0b', rad: 8},
                    {lat: 23.0, lng: 116.5, info: "熱帶低壓 TD09 (預報位置)", col: '#ffffff', rad: 5},
                    {lat: 26.0, lng: 115.0, info: "熱帶低壓 TD09 (預報位置)", col: '#ffffff', rad: 5},
                    
                    {lat: 17.5, lng: 137.5, info: "🌀 巴威颱風 (BAWI) (當前核心位置)", col: '#f59e0b', rad: 8},
                    {lat: 17.6, lng: 134.0, info: "巴威颱風 (BAWI) (預報位置)", col: '#ffffff', rad: 5},
                    
                    {lat: 22.67, lng: 120.49, info: "⚠️ 屏東守備防禦指揮點", col: '#ef4444', rad: 9}
                ];

                nodes.forEach(function(n) {
                    var marker = L.circleMarker([n.lat, n.lng], {
                        radius: n.rad,
                        color: '#0f172a',
                        weight: 2,
                        fillColor: n.col,
                        fillOpacity: 1
                    }).addTo(map).bindPopup(n.info);
                    
                    marker.bindTooltip(n.info.split(" (")[0], {permanent: false, direction: 'top'});
                });
            </script>
        </body>
        </html>
        """
        components.html(html_map_code, height=520)
        
        st.markdown("""
        <div style="background-color:#0f172a; border:1px solid #334155; padding:10px; border-radius:6px; margin-top:8px;">
            <span style="font-size:11px; color:#94a3b8; font-weight:bold;">🌀 高確定性精準圖層動態說明：</span><br>
            <span style="color:#f59e0b; font-size:12px;">●</span> <b style="font-size:12px;">黃色核心圓點：</b>代表 <b>巴威颱風 (BAWI)</b> 與 <b>熱帶低壓 TD09</b> 的即時中心定位點。<br>
            <span style="color:#ef4444; font-size:12px;">●</span> <b style="font-size:12px;">紅色守備圓點：</b>代表屏東本地重點防禦指揮中心位置。<br>
            <span style="color:#ef4444; font-size:12px;">●</span> <b style="font-size:12px;">高精準確定性路徑：</b>每一個巨型半透明侵襲圈皆精準切齊圓點經緯度，由深至淺呈現氣旋未來移動的線性軌跡。
        </div>
        """, unsafe_allow_html=True)
