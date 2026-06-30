import sys
import os
import requests
import colorsys

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QScrollArea, QSplitter, QStackedWidget, 
    QCheckBox, QPushButton, QAbstractItemView, QLineEdit
)
from PySide6.QtQuickWidgets import QQuickWidget

# ===========================================================================
# 1) Données brutes issues de l'Algorithme d'Optimisation (VRP)
# ===========================================================================
OPTIMIZED_COURSES = [
    # --- TOURNEE 1 ---
    [
        {"id": "6A14837201FR", "adresse": "12 Rue de Rivoli, 75004 Paris", "date_commande": "24/06/2026", "date_limite": "30/06/2026", "volume": 3},
        {"id": "6A14837203FR", "adresse": "18 Rue Mouffetard, 75005 Paris", "date_commande": "23/06/2026", "date_limite": "29/06/2026", "volume": 2},
        {"id": "6A14837205FR", "adresse": "31 Rue Monge, 75005 Paris", "date_commande": "25/06/2026", "date_limite": "30/06/2026", "volume": 1},
        {"id": "6A14837207FR", "adresse": "2 Place d'Italie, 75013 Paris", "date_commande": "24/06/2026", "date_limite": "29/06/2026", "volume": 2}
    ],
    # --- TOURNEE 2 ---
    [
        {"id": "6A14837202FR", "adresse": "5 Avenue des Gobelins, 75013 Paris", "date_commande": "25/06/2026", "date_limite": "29/06/2026", "volume": 1},
        {"id": "6A14837206FR", "adresse": "60 Rue de la Glacière, 75013 Paris", "date_commande": "27/06/2026", "date_limite": "01/07/2026", "volume": 4}
    ],
    # --- TOURNEE 3 ---
    [
        {"id": "6A14837204FR", "adresse": "7 Boulevard Saint-Marcel, 75013 Paris", "date_commande": "26/06/2026", "date_limite": "01/07/2026", "volume": 5}
    ]
]

DEPOT = {"nom": "Dépôt - Bercy", "lat": 48.8389, "lon": 2.3833}

# Valeurs d'initialisation par défaut
META_DATES = ["Aujourd'hui - 29/06/2026", "Aujourd'hui - 29/06/2026", "Demain - 30/06/2026"]
META_STATS = [
    {"temps": "1h24", "distance": "12.4 km", "depart": "08:30"},
    {"temps": "0h52", "distance": "8.1 km", "depart": "10:15"},
    {"temps": "0h45", "distance": "6.8 km", "depart": "09:00"}
]

# Thème UI
BLUE_DARK, BLUE_PALE, INK, INK_SOFT, LINE, BG, PANEL_BG = "#1d4ed8", "#eaf1fd", "#1f2533", "#5b6472", "#e3e7ee", "#f5f7fa", "#ffffff"

# ===========================================================================
# 2) Fonctions Techniques
# ===========================================================================

def geocode_address(address_str):
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": address_str, "limit": 1}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if data["features"]:
            lon, lat = data["features"][0]["geometry"]["coordinates"]
            return lat, lon
    except:
        pass
    return 48.8566, 2.3522

def get_route_color(index):
    golden_ratio_conjugate = 0.618033988749895
    hue = (index * golden_ratio_conjugate) % 1.0
    return '#{:02x}{:02x}{:02x}'.format(*(int(c*255) for c in colorsys.hsv_to_rgb(hue, 0.85, 0.90)))

def fetch_road_route(coords):
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=4)
        geometry = resp.json()["routes"][0]["geometry"]["coordinates"]
        return [{"lat": lat, "lon": lon} for lon, lat in geometry]
    except:
        return [{"lat": lat, "lon": lon} for lat, lon in coords]

# ===========================================================================
# 3) QML Code (Carte)
# ===========================================================================

QML_MAP_CODE = f"""import QtQuick
import QtLocation
import QtPositioning

Rectangle {{
    id: root; anchors.fill: parent; color: "white"
    Plugin {{ id: mapPlugin; name: "osm" }}
    Map {{
        id: mainMap; anchors.fill: parent; plugin: mapPlugin; center: QtPositioning.coordinate({DEPOT['lat']}, {DEPOT['lon']}); zoomLevel: 13
        DragHandler {{ target: null; onTranslationChanged: (delta) => mainMap.pan(-delta.x, -delta.y) }}
        MouseArea {{
            anchors.fill: parent; acceptedButtons: Qt.NoButton
            onWheel: (wheel) => {{
                var zoomPas = wheel.angleDelta.y / 360;
                mainMap.zoomLevel = Math.max(mainMap.minimumZoomLevel, Math.min(mainMap.maximumZoomLevel, mainMap.zoomLevel + zoomPas));
            }}
        }}
        PinchHandler {{ target: null; onScaleChanged: (delta) => mainMap.zoomLevel += Math.log2(delta) }}
        MapQuickItem {{
            coordinate: QtPositioning.coordinate({DEPOT['lat']}, {DEPOT['lon']}); anchorPoint: Qt.point(15, 15)
            sourceItem: Rectangle {{ width: 30; height: 30; radius: 15; color: "{INK}"; border.color: "white"; border.width: 2; Text {{ anchors.centerIn: parent; text: "D"; color: "white"; font.bold: true }} }}
        }}
    }}
    property var drawnLines: ({{}})
    property var drawnMarkers: ({{}})
    function toggleRoute(routeId, color, pathPoints, markerPoints, isVisible) {{
        if (isVisible) {{
            var lineStr = 'import QtQuick; import QtLocation; MapPolyline {{ line.color: "' + color + '"; line.width: 4; path: [] }}';
            var lineObj = Qt.createQmlObject(lineStr, mainMap, "line_" + routeId);
            var path = [];
            for (var i = 0; i < pathPoints.length; i++) path.push(QtPositioning.coordinate(pathPoints[i].lat, pathPoints[i].lon));
            lineObj.path = path;
            mainMap.addMapItem(lineObj);
            drawnLines[routeId] = lineObj;

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
            if (drawnLines[routeId]) {{ mainMap.removeMapItem(drawnLines[routeId]); drawnLines[routeId].destroy(); delete drawnLines[routeId]; }}
            if (drawnMarkers[routeId]) {{
                for (var k = 0; k < drawnMarkers[routeId].length; k++) {{ mainMap.removeMapItem(drawnMarkers[routeId][k]); drawnMarkers[routeId][k].destroy(); }}
                delete drawnMarkers[routeId];
            }}
        }}
    }}
    function centerOnStop(lat, lon) {{ mainMap.center = QtPositioning.coordinate(lat, lon); mainMap.zoomLevel = 16; }}
}}
"""

# ===========================================================================
# 4) Composants Graphiques de l'interface
# ===========================================================================

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
        self.content.setVisible(start_open)
        outer.addWidget(self.toggle_btn)
        outer.addWidget(self.content)
        self.setStyleSheet(f"CollapsiblePanel {{ background: {PANEL_BG}; border: 1px solid {LINE}; border-radius: 8px; margin-bottom: 8px; }}")

    def _toggle(self):
        opened = self.toggle_btn.isChecked()
        self.content.setVisible(opened)
        self.toggle_btn.setArrowType(Qt.DownArrow if opened else Qt.RightArrow)

class RouteCard(QFrame):
    on_details_requested = Signal(str)
    on_visibility_toggled = Signal(str, bool)

    def __init__(self, route_data):
        super().__init__()
        self.route_data = route_data
        self.setStyleSheet(f"RouteCard {{ background: #fafbfc; border: 1px solid {LINE}; border-radius: 6px; }} RouteCard:hover {{ border-color: {route_data['color']}; background: #ffffff; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet(f"QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 2px solid {route_data['color']}; }} QCheckBox::indicator:checked {{ background: {route_data['color']}; }}")
        self.checkbox.toggled.connect(lambda checked: self.on_visibility_toggled.emit(self.route_data['id'], checked))
        
        info_layout = QVBoxLayout()
        driver_display = route_data['driver'].strip() if route_data['driver'].strip() else "Non attribuée"
        
        self.title = QLabel(f"Tournée {route_data['id']} - {driver_display}")
        self.title.setStyleSheet(f"font-weight: bold; color: {INK}; font-size: 13px; background: transparent;")
        
        self.subtitle = QLabel(f"Commandes : {len(route_data['orders'])}  .  Départ : {route_data['stats']['depart']}")
        self.subtitle.setStyleSheet(f"font-size: 11px; color: {INK_SOFT}; background: transparent;")
        
        info_layout.addWidget(self.title)
        info_layout.addWidget(self.subtitle)

        btn_details = QPushButton("Voir détails")
        btn_details.setStyleSheet(f"color: {route_data['color']}; font-weight: bold; border: none; background: transparent; font-size: 12px;")
        btn_details.setCursor(Qt.PointingHandCursor)
        btn_details.clicked.connect(lambda: self.on_details_requested.emit(self.route_data['id']))

        layout.addWidget(self.checkbox)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(btn_details)

    def update_driver_name_display(self, new_name):
        driver_display = new_name.strip() if new_name.strip() else "Non attribuée"
        self.title.setText(f"Tournée {self.route_data['id']} - {driver_display}")

    def update_departure_display(self, new_depart):
        self.subtitle.setText(f"Commandes : {len(self.route_data['orders'])}  .  Départ : {new_depart}")

    def set_checkbox_state(self, checked):
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)

# ===========================================================================
# 5) Main Application Window
# ===========================================================================

class ManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vue Globale Magasin - Pipeline Algorithmique Connecté")
        self.resize(1340, 840)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        self.route_cards_references = {}
        self.date_panels_references = {}
        self.active_route_id = None

        self.routes_model = {}
        print("\n--- GÉOCODAGE & IMPORTATION DES TOURNÉES DE L'ALGO ---")
        for idx, course_orders in enumerate(OPTIMIZED_COURSES):
            print(f"Traitement de la Tournée {idx+1}...")
            for order in course_orders:
                lat, lon = geocode_address(order["adresse"])
                order["lat"] = lat
                order["lon"] = lon

            r_id = f"T-{idx+1:03d}"
            route_ui = {
                "id": r_id,
                "driver": "",  
                "date": META_DATES[idx % len(META_DATES)],
                "stats": META_STATS[idx % len(META_STATS)],
                "color": get_route_color(idx),
                "orders": course_orders,
                "visible": False
            }
            self.routes_model[r_id] = route_ui
        print("--- IMPORTATION RÉUSSIE ---\n")

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
        self.left_container.setStyleSheet(f"background: {PANEL_BG}; border: none;")
        
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

        self._update_unassigned_counters()

    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{PANEL_BG}; border-bottom:1px solid {LINE};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        brand = QLabel("Flux Marchandises")
        brand.setStyleSheet(f"color:{BLUE_DARK}; font-weight:700; font-size:14px;")
        self.breadcrumb = QLabel("   Manager  >  Tournées Algorithmiques Optimisées")
        self.breadcrumb.setStyleSheet(f"color:{INK_SOFT}; font-size:12px;")
        layout.addWidget(brand)
        layout.addWidget(self.breadcrumb)
        layout.addStretch()
        return bar

    def _build_dispatch_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {PANEL_BG}; border: none; }}")
        
        content = QWidget()
        content.setStyleSheet(f"background: {PANEL_BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)

        grouped = {}
        for r_id, r_data in self.routes_model.items(): 
            grouped.setdefault(r_data["date"], []).append(r_data)

        for date_label, routes_list in grouped.items():
            panel = CollapsiblePanel(date_label, start_open=True)
            self.date_panels_references[date_label] = panel
            
            for r_data in routes_list:
                card = RouteCard(r_data)
                card.on_visibility_toggled.connect(self._toggle_route_on_map)
                card.on_details_requested.connect(self._open_route_details)
                
                self.route_cards_references[r_data["id"]] = card
                panel.content_layout.addWidget(card)
            layout.addWidget(panel)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _update_unassigned_counters(self):
        counters = {date: 0 for date in self.date_panels_references.keys()}
        for r_id, r_data in self.routes_model.items():
            if not r_data["driver"].strip():
                counters[r_data["date"]] += 1
                
        for date_label, panel in self.date_panels_references.items():
            unassigned_count = counters[date_label]
            if unassigned_count > 0:
                s = "s" if unassigned_count > 1 else ""
                panel.toggle_btn.setText(f"  {date_label} ({unassigned_count} tournée{s} non attribuée{s})")
            else:
                panel.toggle_btn.setText(f"  {date_label} (Toutes les tournées sont attribuées)")

    def _toggle_route_on_map(self, route_id, is_visible):
        route_data = self.routes_model[route_id]
        route_data["visible"] = is_visible
        
        if route_id == self.active_route_id:
            self.detail_map_checkbox.blockSignals(True)
            self.detail_map_checkbox.setChecked(is_visible)
            self.detail_map_checkbox.blockSignals(False)
            
        if route_id in self.route_cards_references:
            self.route_cards_references[route_id].set_checkbox_state(is_visible)

        root_obj = self.quick_map.rootObject()
        if not root_obj: return

        if is_visible:
            coords = [(DEPOT["lat"], DEPOT["lon"])]
            markers = []
            for i, order in enumerate(route_data["orders"]):
                coords.append((order["lat"], order["lon"]))
                markers.append({"lat": order["lat"], "lon": order["lon"], "label": str(i+1)})
            
            path = fetch_road_route(coords)
            root_obj.toggleRoute(route_data["id"], route_data["color"], path, markers, True)
        else:
            root_obj.toggleRoute(route_data["id"], "", [], [], False)

    def _build_details_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {PANEL_BG};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)

        btn_back = QPushButton("Retour au tableau général")
        btn_back.setStyleSheet(f"text-align: left; color: {INK_SOFT}; border: none; font-weight: bold; font-size: 12px; padding: 4px 0px; background: transparent;")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._close_details)
        layout.addWidget(btn_back)

        # Panneau de Configuration de la Tournée
        assignment_frame = QFrame()
        assignment_frame.setStyleSheet(f"background: #fafbfc; border: 1px solid {LINE}; border-radius: 8px;")
        assignment_layout = QVBoxLayout(assignment_frame)
        assignment_layout.setContentsMargins(12, 12, 12, 12)
        assignment_layout.setSpacing(10)
        
        # 1. Gestion du Livreur
        driver_row = QHBoxLayout()
        input_label = QLabel("Livreur attitré :")
        input_label.setStyleSheet(f"font-weight: 600; color: {INK}; font-size: 12px; background: transparent;")
        self.driver_input = QLineEdit()
        self.driver_input.setPlaceholderText("Entrez le nom ou l'ID du chauffeur...")
        self.driver_input.setStyleSheet(f"QLineEdit {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: {INK}; }} QLineEdit:focus {{ border-color: {BLUE_DARK}; }}")
        self.driver_input.textEdited.connect(self._on_driver_name_edited)
        self.driver_input.returnPressed.connect(self._close_details) 
        driver_row.addWidget(input_label)
        driver_row.addWidget(self.driver_input, 1)
        assignment_layout.addLayout(driver_row)

        # 2. Information du Camion (Fixe / Lecture seule)
        truck_row = QHBoxLayout()
        truck_title_label = QLabel("Véhicule chargé :")
        truck_title_label.setStyleSheet(f"font-weight: 600; color: {INK}; font-size: 12px; background: transparent;")
        self.truck_label = QLabel("Camion N°—")
        self.truck_label.setStyleSheet(f"color: {INK}; font-size: 12px; font-weight: bold; background: transparent;")
        truck_row.addWidget(truck_title_label)
        truck_row.addWidget(self.truck_label, 1)
        assignment_layout.addLayout(truck_row)

        # 3. Modification de l'heure de départ
        depart_row = QHBoxLayout()
        depart_input_label = QLabel("Heure de départ :")
        depart_input_label.setStyleSheet(f"font-weight: 600; color: {INK}; font-size: 12px; background: transparent;")
        self.depart_input = QLineEdit()
        self.depart_input.setPlaceholderText("HH:MM")
        self.depart_input.setStyleSheet(f"QLineEdit {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: {INK}; }} QLineEdit:focus {{ border-color: {BLUE_DARK}; }}")
        self.depart_input.textEdited.connect(self._on_departure_time_edited)
        depart_row.addWidget(depart_input_label)
        depart_row.addWidget(self.depart_input, 1)
        assignment_layout.addLayout(depart_row)

        # 4. Affichage Carte
        self.detail_map_checkbox = QCheckBox("Afficher le trajet sur la carte")
        self.detail_map_checkbox.toggled.connect(self._on_detail_checkbox_toggled)
        assignment_layout.addWidget(self.detail_map_checkbox)

        layout.addWidget(assignment_frame)

        # Résumé des indicateurs de performance de la tournée
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
            value_lbl = QLabel("—")
            value_lbl.setStyleSheet(f"color:{BLUE_DARK}; font-size:17px; font-weight:700; background:transparent;")
            label_lbl = QLabel(label)
            label_lbl.setStyleSheet(f"color:{INK_SOFT}; font-size:10.5px; background:transparent;")
            cell_layout.addWidget(value_lbl)
            cell_layout.addWidget(label_lbl)
            grid.addWidget(cell, i // 2, i % 2)
            self.summary_labels[key] = value_lbl

        self.depart_label = QLabel("")
        self.depart_label.setStyleSheet(f"color:{INK_SOFT}; font-size:11.5px; margin-top:4px; background: transparent;")
        self.panel_summary.content_layout.addWidget(self.depart_label)
        layout.addWidget(self.panel_summary)

        # Tableau des Commandes / Séquencement
        self.panel_orders = CollapsiblePanel("Ordre de passage optimisé (Séquence)")
        columns = ["Étape", "N° commande", "Adresse", "Vol.", "Date commande", "Date Limite"]
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
        for col in (0, 1, 3, 4, 5): header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.table.setStyleSheet(f"""
            QTableWidget {{ border: none; font-size: 11px; background: {PANEL_BG}; color: {INK}; }}
            QHeaderView::section {{ background: #fafbfc; color: {INK_SOFT}; font-size: 10px; font-weight: 600; padding: 6px; border: none; border-bottom: 1px solid {LINE}; }}
            QTableWidget::item {{ padding: 7px 4px; }}
            QTableWidget::item:selected {{ background: {BLUE_PALE}; color: {INK}; }}
        """)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        self.panel_orders.content_layout.addWidget(self.table)
        layout.addWidget(self.panel_orders, 1)

        return page

    def _open_route_details(self, route_id):
        route_data = self.routes_model[route_id]
        self.active_route_id = route_id
        
        driver_text = route_data['driver'].strip() if route_data['driver'].strip() else "Non attribuée"
        self.breadcrumb.setText(f"   Manager  >  Tournée {route_data['id']} ({driver_text})")
        
        self.driver_input.setText(route_data["driver"])
        
        # Identification du camion d'après l'index de la tournée (T-001 -> Camion N°1)
        try:
            truck_num = int(route_id.split("-")[1])
        except ValueError:
            truck_num = 1
        self.truck_label.setText(f"Camion N°{truck_num}")

        # Remplissage du champ éditable de l'heure de départ
        self.depart_input.setText(route_data["stats"]["depart"])
        
        self.detail_map_checkbox.blockSignals(True)
        self.detail_map_checkbox.setChecked(route_data["visible"])
        self.detail_map_checkbox.setStyleSheet(f"""
            QCheckBox {{ font-size: 12px; color: {INK}; font-weight: 500; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 2px solid {route_data['color']}; }}
            QCheckBox::indicator:checked {{ background: {route_data['color']}; }}
        """)
        self.detail_map_checkbox.blockSignals(False)
        
        stats = route_data["stats"]
        orders = route_data["orders"]
        vols = sum(o["volume"] for o in orders)
        
        self.summary_labels["temps"].setText(stats["temps"])
        self.summary_labels["stops"].setText(str(len(orders)))
        self.summary_labels["volume"].setText(str(vols))
        self.summary_labels["distance"].setText(stats["distance"])
        self.depart_label.setText(f"Départ à {stats['depart']} depuis {DEPOT['nom']}")

        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            values = [str(row + 1), order["id"], order["adresse"], str(order["volume"]), order["date_commande"], order["date_limite"]]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 0: item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            self.table.item(row, 0).setData(Qt.UserRole, order)

        self.table.resizeRowsToContents()
        self.left_container.setCurrentIndex(1)

    def _on_driver_name_edited(self, new_text):
        if self.active_route_id and self.active_route_id in self.routes_model:
            self.routes_model[self.active_route_id]["driver"] = new_text
            
            driver_text = new_text.strip() if new_text.strip() else "Non attribuée"
            self.breadcrumb.setText(f"   Manager  >  Tournée {self.active_route_id} ({driver_text})")
            
            if self.active_route_id in self.route_cards_references:
                self.route_cards_references[self.active_route_id].update_driver_name_display(new_text)

            self._update_unassigned_counters()

    def _on_departure_time_edited(self, new_time):
        """Met à jour l'heure de départ de la tournée de façon synchronisée partout dans l'UI"""
        if self.active_route_id and self.active_route_id in self.routes_model:
            # 1. Sauvegarde dans le modèle de données interne
            self.routes_model[self.active_route_id]["stats"]["depart"] = new_time
            
            # 2. Rafraîchissement des textes de la vue détail courante
            self.depart_label.setText(f"Départ à {new_time} depuis {DEPOT['nom']}")
            
            # 3. Répercussion sur le composant (Card) du tableau de bord d'accueil
            if self.active_route_id in self.route_cards_references:
                self.route_cards_references[self.active_route_id].update_departure_display(new_time)

    def _on_detail_checkbox_toggled(self, checked):
        if self.active_route_id:
            self._toggle_route_on_map(self.active_route_id, checked)

    def _close_details(self):
        self.active_route_id = None
        self.breadcrumb.setText("   Manager  >  Tournées Algorithmiques Optimisées")
        self.left_container.setCurrentIndex(0)

    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        order = self.table.item(row, 0).data(Qt.UserRole)
        
        root_obj = self.quick_map.rootObject()
        if root_obj and order:
            root_obj.centerOnStop(order["lat"], order["lon"])

    def closeEvent(self, event):
        if os.path.exists(self.qml_filename): os.remove(self.qml_filename)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ManagerApp()
    window.show()
    sys.exit(app.exec())
