import sys
import os
import requests
import colorsys

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QScrollArea, QSplitter, QStackedWidget, 
    QCheckBox, QPushButton, QAbstractItemView
)
from PySide6.QtQuickWidgets import QQuickWidget

# ===========================================================================
# 1) Générateur de Couleurs Dynamiques (Jusqu'à 100 teintes distinctes)
# ===========================================================================

def get_route_color(index, total_max=100):
    """
    Génère une couleur Hexadécimale unique et très contrastée.
    Distribue les teintes équitablement sur le cercle chromatique (espace HSV).
    """
    # On utilise le nombre d'or (0.618033988749895) pour maximiser la dispersion des couleurs consécutives
    golden_ratio_conjugate = 0.618033988749895
    hue = (index * golden_ratio_conjugate) % 1.0
    
    # Saturation et luminosité élevées pour une visibilité optimale sur la carte
    saturation = 0.85
    value = 0.90
    
    rgb = colorsys.hsv_to_rgb(hue, saturation, value)
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

# ===========================================================================
# 2) Données Simulées (Magasin, Commandes et Tournées)
# ===========================================================================

DEPOT = {"nom": "Dépôt - Bercy", "lat": 48.8389, "lon": 2.3833}

ORDERS_DB = {
    "6A14837201FR": {"adresse": "12 Rue de Rivoli, 75004 Paris", "lat": 48.8556, "lon": 2.3611, "date_commande": "24/06/2026", "date_limite": "30/06/2026", "volume": 3},
    "6A14837202FR": {"adresse": "5 Avenue des Gobelins, 75013 Paris", "lat": 48.8389, "lon": 2.3540, "date_commande": "25/06/2026", "date_limite": "29/06/2026", "volume": 1},
    "6A14837203FR": {"adresse": "18 Rue Mouffetard, 75005 Paris", "lat": 48.8440, "lon": 2.3499, "date_commande": "23/06/2026", "date_limite": "29/06/2026", "volume": 2},
    "6A14837204FR": {"adresse": "7 Boulevard Saint-Marcel, 75013 Paris", "lat": 48.8378, "lon": 2.3621, "date_commande": "26/06/2026", "date_limite": "01/07/2026", "volume": 5},
    "6A14837205FR": {"adresse": "31 Rue Monge, 75005 Paris", "lat": 48.8447, "lon": 2.3508, "date_commande": "25/06/2026", "date_limite": "30/06/2026", "volume": 1},
    "6A14837206FR": {"adresse": "60 Rue de la Glaciere, 75013 Paris", "lat": 48.8323, "lon": 2.3475, "date_commande": "27/06/2026", "date_limite": "01/07/2026", "volume": 4},
    "6A14837207FR": {"adresse": "2 Place d'Italie, 75013 Paris", "lat": 48.8313, "lon": 2.3559, "date_commande": "24/06/2026", "date_limite": "29/06/2026", "volume": 2},
}

# Liste des tournées (sans couleur écrite en dur, on les attribue à l'initialisation)
RAW_ROUTES = [
    {"id": "T-001", "date": "Aujourd'hui - 29/06/2026", "driver": "Aymen B.", "orders": ["6A14837201FR", "6A14837203FR", "6A14837205FR", "6A14837207FR"], "stats": {"temps": "1h24", "distance": "12.4 km", "depart": "08:30"}},
    {"id": "T-002", "date": "Aujourd'hui - 29/06/2026", "driver": "Sarah L.", "orders": ["6A14837202FR", "6A14837206FR"], "stats": {"temps": "0h52", "distance": "8.1 km", "depart": "10:15"}},
    {"id": "T-003", "date": "Demain - 30/06/2026", "driver": "Marc D.", "orders": ["6A14837204FR"], "stats": {"temps": "0h45", "distance": "6.8 km", "depart": "09:00"}},
]

# Attribution automatique d'une couleur unique par index
ROUTES = []
for idx, r in enumerate(RAW_ROUTES):
    r["color"] = get_route_color(idx)
    ROUTES.append(r)

# Thème graphique UI
BLUE_DARK = "#1d4ed8"
BLUE_PALE = "#eaf1fd"
INK = "#1f2533"
INK_SOFT = "#5b6472"
LINE = "#e3e7ee"
BG = "#f5f7fa"
PANEL_BG = "#ffffff"

# ===========================================================================
# 3) QML : Carte dynamique multi-tracés (Points + Lignes de couleurs)
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

            // 2. Tracé des marqueurs (Lieux de livraison avec numéros d'étape)
            var markers = [];
            for (var j = 0; j < markerPoints.length; j++) {{
                var m = markerPoints[j];
                var markerStr = 'import QtQuick; import QtLocation; import QtPositioning; MapQuickItem {{ coordinate: QtPositioning.coordinate(' + m.lat + ',' + m.lon + '); anchorPoint: Qt.point(13,13); sourceItem: Rectangle {{ width:26; height:26; radius:13; color: "' + color + '"; border.color: "white"; border.width: 2; Text {{ anchors.centerIn: parent; text: "' + m.label + '"; color: "white"; font.bold: true; font.pixelSize: 11 }} }} }}';
                var markerObj = Qt.createQmlObject(markerStr, mainMap, "marker_" + routeId + "_" + j);
                mainMap.addMapItem(markerObj);
                markers.push(markerObj);
            }}
            drawnMarkers[routeId] = markers;
        }} else {{
            // Nettoyage complet
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

# ===========================================================================
# 4) OSRM Engine & UI Widgets
# ===========================================================================

def fetch_road_route(coords):
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=4)
        geometry = resp.json()["routes"][0]["geometry"]["coordinates"]
        return [{"lat": lat, "lon": lon} for lon, lat in geometry]
    except:
        return [{"lat": lat, "lon": lon} for lat, lon in coords]

class CollapsiblePanel(QWidget):
    def __init__(self, title, start_open=True, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setText(f"  {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(start_open)
        self.toggle_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.toggle_btn.setArrowType(Qt.DownArrow if start_open else Qt.RightArrow)
        self.toggle_btn.setStyleSheet(f"QToolButton {{ background: {PANEL_BG}; border: none; border-bottom: 1px solid {LINE}; padding: 12px 6px; font-weight: 600; font-size: 13px; color: {INK}; text-align: left; }}")
        self.toggle_btn.clicked.connect(self._toggle)

        self.content = QWidget()
        self.content.setStyleSheet(f"background: {PANEL_BG};")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(8)
        self.content.setVisible(start_open)
        
        outer.addWidget(self.toggle_btn)
        outer.addWidget(self.content)
        self.setStyleSheet(f"CollapsiblePanel {{ background: {PANEL_BG}; border: 1px solid {LINE}; border-radius: 8px; margin-bottom: 8px; }}")

    def _toggle(self):
        opened = self.toggle_btn.isChecked()
        self.content.setVisible(opened)
        self.toggle_btn.setArrowType(Qt.DownArrow if opened else Qt.RightArrow)

class RouteCard(QFrame):
    on_details_requested = Signal(dict)
    on_visibility_toggled = Signal(dict, bool)

    def __init__(self, route_data):
        super().__init__()
        self.route_data = route_data
        self.setStyleSheet(f"RouteCard {{ background: #fafbfc; border: 1px solid {LINE}; border-radius: 6px; }} RouteCard:hover {{ border-color: {route_data['color']}; background: #ffffff; }}")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet(f"QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 2px solid {route_data['color']}; }} QCheckBox::indicator:checked {{ background: {route_data['color']}; }}")
        self.checkbox.toggled.connect(lambda checked: self.on_visibility_toggled.emit(self.route_data, checked))
        
        info_layout = QVBoxLayout()
        title = QLabel(f"Tournée {route_data['id']} — {route_data['driver']}")
        title.setStyleSheet(f"font-weight: bold; color: {INK}; font-size: 13px;")
        subtitle = QLabel(f"{len(route_data['orders'])} commandes  •  Départ : {route_data['stats']['depart']}")
        subtitle.setStyleSheet(f"font-size: 11px; color: {INK_SOFT};")
        info_layout.addWidget(title)
        info_layout.addWidget(subtitle)

        btn_details = QPushButton("Voir détails ➔")
        btn_details.setStyleSheet(f"color: {route_data['color']}; font-weight: bold; border: none; background: transparent; font-size: 12px;")
        btn_details.setCursor(Qt.PointingHandCursor)
        btn_details.clicked.connect(lambda: self.on_details_requested.emit(self.route_data))

        layout.addWidget(self.checkbox)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(btn_details)

# ===========================================================================
# 5) Main Application Screen
# ===========================================================================

class ManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vue Globale Magasin — Dispatch")
        self.resize(1340, 840)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        dossier_du_script = os.path.dirname(os.path.abspath(__file__))
        self.qml_filename = os.path.join(dossier_du_script, "map_manager.qml")
        with open(self.qml_filename, "w", encoding="utf-8") as f:
            f.write(QML_MAP_CODE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        root.addWidget(self._build_topbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        self.left_container = QStackedWidget()
        self.left_container.setMinimumWidth(460)
        
        self.view_dispatch = self._build_dispatch_page()
        self.view_details = self._build_details_page()
        
        self.left_container.addWidget(self.view_dispatch)
        self.left_container.addWidget(self.view_details)
        
        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(f"background:{PANEL_BG}; border:1px solid {LINE}; border-radius:8px;")
        map_layout = QVBoxLayout(self.map_frame)
        map_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_map = QQuickWidget()
        self.quick_map.setResizeMode(QQuickWidget.SizeRootObjectToView)
        self.quick_map.setFocusPolicy(Qt.StrongFocus)
        self.quick_map.setSource(QUrl.fromLocalFile(self.qml_filename))
        map_layout.addWidget(self.quick_map)

        splitter.addWidget(self.left_container)
        splitter.addWidget(self.map_frame)
        splitter.setSizes([460, 880])
        
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.addWidget(splitter)
        root.addWidget(body)

    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{PANEL_BG}; border-bottom:1px solid {LINE};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)

        brand = QLabel("Flux Marchandises")
        brand.setStyleSheet(f"color:{BLUE_DARK}; font-weight:700; font-size:14px;")
        self.breadcrumb = QLabel("   Manager  ›  Tableau de Bord Général")
        self.breadcrumb.setStyleSheet(f"color:{INK_SOFT}; font-size:12px;")
        
        layout.addWidget(brand)
        layout.addWidget(self.breadcrumb)
        layout.addStretch()
        return bar

    def _build_dispatch_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)

        grouped = {}
        for r in ROUTES:
            grouped.setdefault(r["date"], []).append(r)

        for date_label, routes_list in grouped.items():
            panel = CollapsiblePanel(date_label, start_open=True)
            for r_data in routes_list:
                card = RouteCard(r_data)
                card.on_visibility_toggled.connect(self._toggle_route_on_map)
                card.on_details_requested.connect(self._open_route_details)
                panel.content_layout.addWidget(card)
            layout.addWidget(panel)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _toggle_route_on_map(self, route_data, is_visible):
        root_obj = self.quick_map.rootObject()
        if not root_obj: return

        if is_visible:
            coords = [(DEPOT["lat"], DEPOT["lon"])]
            markers = []
            for i, o_id in enumerate(route_data["orders"]):
                o = ORDERS_DB[o_id]
                coords.append((o["lat"], o["lon"]))
                markers.append({"lat": o["lat"], "lon": o["lon"], "label": str(i+1)})
            
            path = fetch_road_route(coords)
            root_obj.toggleRoute(route_data["id"], route_data["color"], path, markers, True)
        else:
            root_obj.toggleRoute(route_data["id"], "", [], [], False)

    def _build_details_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)

        btn_back = QPushButton("⬅ Retour au tableau général")
        btn_back.setStyleSheet(f"text-align: left; color: {INK_SOFT}; border: none; font-weight: bold; font-size: 12px; padding: 4px 0px;")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._close_details)
        layout.addWidget(btn_back)

        self.panel_summary = CollapsiblePanel("Résumé de la tournée sélectionnée")
        grid = QGridLayout()
        grid.setSpacing(8)
        self.panel_summary.content_layout.addLayout(grid)

        self.summary_labels = {}
        items = [("temps", "Temps estimé"), ("stops", "Stops"), ("volume", "Volume total"), ("distance", "Distance")]
        for i, (key, label) in enumerate(items):
            cell = QFrame()
            cell.setStyleSheet(f"background:{BLUE_PALE}; border-radius:8px;")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(10, 8, 10, 8)
            cell_layout.setSpacing(2)

            value_lbl = QLabel("—")
            value_lbl.setStyleSheet(f"color:{BLUE_DARK}; font-size:17px; font-weight:700; background:transparent;")
            label_lbl = QLabel(label)
            label_lbl.setStyleSheet(f"color:{INK_SOFT}; font-size:10.5px; background:transparent;")

            cell_layout.addWidget(value_lbl)
            cell_layout.addWidget(label_lbl)
            grid.addWidget(cell, i // 2, i % 2)
            self.summary_labels[key] = value_lbl

        self.depart_label = QLabel("")
        self.depart_label.setStyleSheet(f"color:{INK_SOFT}; font-size:11.5px; margin-top:4px;")
        self.panel_summary.content_layout.addWidget(self.depart_label)
        layout.addWidget(self.panel_summary)

        self.panel_orders = CollapsiblePanel("Livraisons de la tournée")
        columns = ["#", "N° commande", "Adresse", "Vol.", "Commandée le", "Livraison prévue"]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(320)
        self.table.setWordWrap(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (0, 1, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.table.setStyleSheet(f"""
            QTableWidget {{ border: none; font-size: 11px; gridline-color: {LINE}; background: {PANEL_BG}; color: {INK}; }}
            QHeaderView::section {{ background: #fafbfc; color: {INK_SOFT}; font-size: 10px; font-weight: 600; padding: 6px; border: none; border-bottom: 1px solid {LINE}; }}
            QTableWidget::item {{ padding: 7px 4px; color: {INK}; }}
            QTableWidget::item:selected {{ background: {BLUE_PALE}; color: {INK}; }}
        """)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.panel_orders.content_layout.addWidget(self.table)
        layout.addWidget(self.panel_orders, 1)

        return page

    def _open_route_details(self, route_data):
        self.active_route_data = route_data
        self.breadcrumb.setText(f"   Manager  ›  Tournée {route_data['id']} ({route_data['driver']})")
        
        stats = route_data["stats"]
        orders = route_data["orders"]
        vols = sum(ORDERS_DB[o]["volume"] for o in orders)
        
        self.summary_labels["temps"].setText(stats["temps"])
        self.summary_labels["stops"].setText(str(len(orders)))
        self.summary_labels["volume"].setText(str(vols))
        self.summary_labels["distance"].setText(stats["distance"])
        self.depart_label.setText(f"Départ à {stats['depart']} depuis {DEPOT['nom']}")

        self.table.setRowCount(len(orders))
        for row, order_num in enumerate(orders):
            d = ORDERS_DB[order_num]
            values = [str(row + 1), order_num, d["adresse"], str(d["volume"]), d["date_commande"], d["date_limite"]]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 0: item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            self.table.item(row, 0).setData(Qt.UserRole, order_num)

        self.table.resizeRowsToContents()
        self.left_container.setCurrentIndex(1)

    def _close_details(self):
        self.breadcrumb.setText("   Manager  ›  Tableau de Bord Général")
        self.left_container.setCurrentIndex(0)

    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        order_num = self.table.item(row, 0).data(Qt.UserRole)
        
        d = ORDERS_DB[order_num]
        root_obj = self.quick_map.rootObject()
        if root_obj:
            root_obj.centerOnStop(d["lat"], d["lon"])

    def closeEvent(self, event):
        if os.path.exists(self.qml_filename):
            os.remove(self.qml_filename)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ManagerApp()
    window.show()
    sys.exit(app.exec())
