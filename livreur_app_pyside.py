# ===========================================================================
# 2) QML : Carte dynamique multi-tracés (Points corrigés)
# ===========================================================================

QML_MAP_CODE = f"""import QtQuick
import QtLocation
import QtPositioning

Rectangle {{
    id: root
    anchors.fill: parent
    color: "white"

    Plugin {{ id: mapPlugin; name: "osm" }}

    Map {{
        id: mainMap
        anchors.fill: parent
        plugin: mapPlugin
        center: QtPositioning.coordinate({DEPOT['lat']}, {DEPOT['lon']})
        zoomLevel: 13

        DragHandler {{ target: null; onTranslationChanged: (delta) => mainMap.pan(-delta.x, -delta.y) }}
        MouseArea {{
            anchors.fill: parent; acceptedButtons: Qt.NoButton
            onWheel: (wheel) => {{
                var zoomPas = wheel.angleDelta.y / 360;
                mainMap.zoomLevel = Math.max(mainMap.minimumZoomLevel, Math.min(mainMap.maximumZoomLevel, mainMap.zoomLevel + zoomPas));
            }}
        }}
        PinchHandler {{ target: null; onScaleChanged: (delta) => mainMap.zoomLevel += Math.log2(delta) }}
        
        // Dépôt fixe principal
        MapQuickItem {{
            coordinate: QtPositioning.coordinate({DEPOT['lat']}, {DEPOT['lon']})
            anchorPoint: Qt.point(15, 15)
            sourceItem: Rectangle {{
                width: 30; height: 30; radius: 15; color: "{INK}"; border.color: "white"; border.width: 2
                Text {{ anchors.centerIn: parent; text: "D"; color: "white"; font.bold: true }}
            }}
        }}
    }}

    property var drawnLines: ({{}})
    property var drawnMarkers: ({{}})

    function toggleRoute(routeId, color, pathPoints, markerPoints, isVisible) {{
        if (isVisible) {{
            // 1. Tracé de la ligne de route
            var lineStr = 'import QtQuick; import QtLocation; MapPolyline {{ line.color: "' + color + '"; line.width: 4; path: [] }}';
            var lineObj = Qt.createQmlObject(lineStr, mainMap, "line_" + routeId);
            var path = [];
            for (var i = 0; i < pathPoints.length; i++) path.push(QtPositioning.coordinate(pathPoints[i].lat, pathPoints[i].lon));
            lineObj.path = path;
            mainMap.addMapItem(lineObj);
            drawnLines[routeId] = lineObj;

            // 2. Tracé des marqueurs de livraison associés
            var markers = [];
            for (var j = 0; j < markerPoints.length; j++) {{
                var m = markerPoints[j];
                
                // --- CORRECTION ICI : Ajout de "import QtPositioning;" au début de la chaîne ---
                var markerStr = 'import QtQuick; import QtLocation; import QtPositioning; MapQuickItem {{ coordinate: QtPositioning.coordinate(' + m.lat + ',' + m.lon + '); anchorPoint: Qt.point(13,13); sourceItem: Rectangle {{ width:26; height:26; radius:13; color: "' + color + '"; border.color: "white"; border.width: 2; Text {{ anchors.centerIn: parent; text: "' + m.label + '"; color: "white"; font.bold: true; font.pixelSize: 11 }} }} }}';
                
                var markerObj = Qt.createQmlObject(markerStr, mainMap, "marker_" + routeId + "_" + j);
                mainMap.addMapItem(markerObj);
                markers.push(markerObj);
            }}
            drawnMarkers[routeId] = markers;
        }} else {{
            // Nettoyage de la carte si décochée
            if (drawnLines[routeId]) {{ mainMap.removeMapItem(drawnLines[routeId]); drawnLines[routeId].destroy(); delete drawnLines[routeId]; }}
            if (drawnMarkers[routeId]) {{
                for (var k = 0; k < drawnMarkers[routeId].length; k++) {{ mainMap.removeMapItem(drawnMarkers[routeId][k]); drawnMarkers[routeId][k].destroy(); }}
                delete drawnMarkers[routeId];
            }}
        }}
    }}

    function centerOnStop(lat, lon) {{
        mainMap.center = QtPositioning.coordinate(lat, lon);
        mainMap.zoomLevel = 16;
    }}
}}
"""
