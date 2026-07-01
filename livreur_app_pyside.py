import sys
import os
import requests
import colorsys

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QScrollArea, QSplitter, QStackedWidget, 
    QCheckBox, QPushButton, QAbstractItemView, QLineEdit, QTabWidget
)
from PySide6.QtQuickWidgets import QQuickWidget

# --- IMPORTATION DU MOTEUR DE CALCUL ---
# Cela va exécuter angle_main.py en arrière-plan et nous donner accès à ses variables
import angle_main as main
import donnees

# Le Dépôt est forcé aux coordonnées de Paris pour l'affichage de la carte
DEPOT = {"nom": "Dépôt Central", "lat": 48.8566, "lon": 2.3522}

# Thème UI
BLUE_DARK, BLUE_PALE, INK, INK_SOFT, LINE, BG, PANEL_BG = "#1d4ed8", "#eaf1fd", "#1f2533", "#5b6472", "#e3e7ee", "#f5f7fa", "#ffffff"

# ===========================================================================
# Fonctions Techniques
# ===========================================================================

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
# QML Code (Carte)
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
    function centerOnStop(lat, lon) {{ mainMap.center = QtPositioning.coordinate(lat, lon); mainMap.zoomLevel = 15; }}
}}
"""

# ===========================================================================
# Composants Graphiques de l'interface
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
        
        self.title = QLabel(f"{route_data['id']} - {driver_display}")
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
        self.title.setText(f"{self.route_data['id']} - {driver_display}")

    def update_departure_display(self, new_depart):
        self.subtitle.setText(f"Commandes : {len(self.route_data['orders'])}  .  Départ : {new_depart}")

    def set_checkbox_state(self, checked):
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)

# ===========================================================================
# Main Application Window
# ===========================================================================

class ManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vue Globale Magasin - ERP Logistique")
        self.resize(1340, 840)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        self.route_cards_references = {}
        self.active_route_id = None
        
        self.orders_db = {}
        self.algo_output = []
        self.routes_model = {}

        # 1. Extraction et formatage des données depuis main.py
        self._load_data_from_backend()

        # 2. Construction du pont de données
        self._build_routes_from_algo()

        # 3. Fichier QML temporaire
        dossier_du_script = os.path.dirname(os.path.abspath(__file__))
        self.qml_filename = os.path.join(dossier_du_script, "map_manager.qml")
        with open(self.qml_filename, "w", encoding="utf-8") as f:
            f.write(QML_MAP_CODE)

        # 4. Structure principale
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        root.addWidget(self._build_topbar())

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: none; border-top: 1px solid {LINE}; }}
            QTabBar::tab {{ background: #e3e7ee; color: {INK_SOFT}; padding: 10px 20px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }}
            QTabBar::tab:selected {{ background: {PANEL_BG}; color: {BLUE_DARK}; border: 1px solid {LINE}; border-bottom: none; }}
        """)

        self.tab_today = QWidget()
        self._setup_today_tab()
        
        self.tab_future = QWidget()
        self._setup_future_tab()

        self.tabs.addTab(self.tab_today, "Tournées du Jour (J1)")
        self.tabs.addTab(self.tab_future, "Commandes en attente (Futur)")
        
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.addWidget(self.tabs)
        root.addWidget(body)

        self._update_unassigned_counters()

    def _load_data_from_backend(self):
        """Traduit les objets métier de classes.py en dictionnaires d'interface"""
        print("\n--- SYNCHRONISATION AVEC LE MOTEUR ALGORITHMIQUE ---")
        
        # A. Construction de la base de données globale
        for cid, client in main.Clients.items():
            if isinstance(cid, tuple) or cid == 0:
                continue # On ignore les clés sous forme de tuple et le Dépôt (0)
            
            for jour_idx in range(main.nb_jours):
                vol = client.demande[jour_idx]
                if vol > 0: # S'il y a un colis prévu pour ce jour
                    order_id = f"C-{cid}-J{jour_idx+1}"
                    # Attribution d'une fausse rue pour l'esthétique
                    rue = donnees.rues[cid % len(donnees.rues)] 
                    
                    lat, lon = client.coordonnées
                    # Si l'algo utilise des coordonnées cartésiennes de test (-20 à 20), on les projette sur Paris
                    if -100 < lat < 100 and -100 < lon < 100 and not (40 < lat < 55):
                        lat = 48.8566 + (lat * 0.003)
                        lon = 2.3522 + (lon * 0.003)
                    
                    self.orders_db[order_id] = {
                        "adresse": f"{rue}, 75000 Paris",
                        "date_commande": f"Jour {max(1, jour_idx)}",
                        "date_limite": f"Jour {jour_idx+1}",
                        "volume": vol,
                        "lat": lat,
                        "lon": lon,
                        "jour": jour_idx + 1
                    }
        
        # B. Récupération des tournées calculées pour le Jour 1
        if 1 in main.course:
            for trajet in main.course[1]:
                camion_commandes = []
                for cid in trajet:
                    if cid != 0: # On ignore le passage au dépôt (0)
                        order_id = f"C-{cid}-J1"
                        if order_id in self.orders_db:
                            camion_commandes.append(order_id)
                
                # S'il y a des clients dans ce camion, on sauvegarde la tournée
                if camion_commandes:
                    self.algo_output.append(camion_commandes)

    def _build_routes_from_algo(self):
        """Transforme l'ALGO_OUTPUT (liste d'IDs) en données complètes pour l'UI"""
        for idx, client_ids in enumerate(self.algo_output):
            truck_name = f"Camion N°{idx+1}"
            
            course_orders = []
            for order_id in client_ids:
                if order_id in self.orders_db:
                    order_data = self.orders_db[order_id].copy()
                    order_data["id"] = order_id
                    course_orders.append(order_data)

            route_ui = {
                "id": truck_name,
                "driver": "",  
                "date": "Jour 1", 
                "stats": {
                    "temps": "Non calculé", 
                    "distance": "Non calculée",
                    "depart": "08:30"
                },
                "color": get_route_color(idx),
                "orders": course_orders,
                "visible": False
            }
            self.routes_model[truck_name] = route_ui
        print("--- INTERFACE PRÊTE ---\n")

    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{PANEL_BG}; border-bottom:1px solid {LINE};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        brand = QLabel("Flux Marchandises")
        brand.setStyleSheet(f"color:{BLUE_DARK}; font-weight:700; font-size:14px;")
        layout.addWidget(brand)
        layout.addStretch()
        return bar

    # ===========================================================================
    # GESTION ONGLET 1 : PLANIFICATION DU JOUR
    # ===========================================================================

    def _setup_today_tab(self):
        layout = QVBoxLayout(self.tab_today)
        layout.setContentsMargins(0, 10, 0, 0)
        
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
        
        layout.addWidget(splitter)

    def _build_dispatch_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {PANEL_BG}; border: none; }}")
        
        content = QWidget()
        content.setStyleSheet(f"background: {PANEL_BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)

        self.panel_today = CollapsiblePanel("Tournées du jour", start_open=True)
        
        for r_id, r_data in self.routes_model.items(): 
            card = RouteCard(r_data)
            card.on_visibility_toggled.connect(self._toggle_route_on_map)
            card.on_details_requested.connect(self._open_route_details)
            
            self.route_cards_references[r_data["id"]] = card
            self.panel_today.content_layout.addWidget(card)
            
        layout.addWidget(self.panel_today)
        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def _update_unassigned_counters(self):
        unassigned_count = sum(1 for r in self.routes_model.values() if not r["driver"].strip())
        
        if unassigned_count > 0:
            s = "s" if unassigned_count > 1 else ""
            self.panel_today.toggle_btn.setText(f"  Tournées du Jour 1 ({unassigned_count} tournée{s} non attribuée{s})")
        else:
            self.panel_today.toggle_btn.setText(f"  Tournées du Jour 1 (Toutes les tournées sont attribuées)")

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
            
            # Pour éviter les ralentissements réseau, on appelle OSRM que s'il y a peu de points, sinon ligne droite
            path = fetch_road_route(coords) if len(coords) < 15 else [{"lat": lat, "lon": lon} for lat, lon in coords]
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

        assignment_frame = QFrame()
        assignment_frame.setStyleSheet(f"background: #fafbfc; border: 1px solid {LINE}; border-radius: 8px;")
        assignment_layout = QVBoxLayout(assignment_frame)
        assignment_layout.setContentsMargins(12, 12, 12, 12)
        assignment_layout.setSpacing(10)
        
        self.truck_label = QLabel("Camion N°—")
        self.truck_label.setStyleSheet(f"color: {INK}; font-size: 14px; font-weight: bold; background: transparent; padding-bottom: 5px;")
        assignment_layout.addWidget(self.truck_label)

        driver_row = QHBoxLayout()
        input_label = QLabel("Livreur attitré :")
        input_label.setStyleSheet(f"font-weight: 600; color: {INK}; font-size: 12px; background: transparent;")
        self.driver_input = QLineEdit()
        self.driver_input.setPlaceholderText("Entrez le nom du chauffeur...")
        self.driver_input.setStyleSheet(f"QLineEdit {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: {INK}; }}")
        self.driver_input.textEdited.connect(self._on_driver_name_edited)
        self.driver_input.returnPressed.connect(self._close_details) 
        driver_row.addWidget(input_label)
        driver_row.addWidget(self.driver_input, 1)
        assignment_layout.addLayout(driver_row)

        depart_row = QHBoxLayout()
        depart_input_label = QLabel("Heure de départ :")
        depart_input_label.setStyleSheet(f"font-weight: 600; color: {INK}; font-size: 12px; background: transparent;")
        self.depart_input = QLineEdit()
        self.depart_input.setPlaceholderText("HH:MM")
        self.depart_input.setStyleSheet(f"QLineEdit {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: {INK}; }}")
        self.depart_input.textEdited.connect(self._on_departure_time_edited)
        depart_row.addWidget(depart_input_label)
        depart_row.addWidget(self.depart_input, 1)
        assignment_layout.addLayout(depart_row)

        self.detail_map_checkbox = QCheckBox("Afficher le trajet sur la carte")
        self.detail_map_checkbox.toggled.connect(self._on_detail_checkbox_toggled)
        assignment_layout.addWidget(self.detail_map_checkbox)

        layout.addWidget(assignment_frame)

        self.panel_orders = CollapsiblePanel("Ordre de passage optimisé")
        columns = ["Étape", "N° commande", "Adresse", "Vol.", "Date limite"]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(400)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (0, 1, 3, 4): header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

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
        
        self.driver_input.setText(route_data["driver"])
        self.truck_label.setText(route_data["id"])
        self.depart_input.setText(route_data["stats"]["depart"])
        
        self.detail_map_checkbox.blockSignals(True)
        self.detail_map_checkbox.setChecked(route_data["visible"])
        self.detail_map_checkbox.setStyleSheet(f"""
            QCheckBox {{ font-size: 12px; color: {INK}; font-weight: 500; }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 2px solid {route_data['color']}; }}
            QCheckBox::indicator:checked {{ background: {route_data['color']}; }}
        """)
        self.detail_map_checkbox.blockSignals(False)
        
        orders = route_data["orders"]
        self.table.setRowCount(len(orders))
        for row, order in enumerate(orders):
            values = [str(row + 1), order["id"], order["adresse"], str(order["volume"]), order["date_limite"]]
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
            if self.active_route_id in self.route_cards_references:
                self.route_cards_references[self.active_route_id].update_driver_name_display(new_text)
            self._update_unassigned_counters()

    def _on_departure_time_edited(self, new_time):
        if self.active_route_id and self.active_route_id in self.routes_model:
            self.routes_model[self.active_route_id]["stats"]["depart"] = new_time
            if self.active_route_id in self.route_cards_references:
                self.route_cards_references[self.active_route_id].update_departure_display(new_time)

    def _on_detail_checkbox_toggled(self, checked):
        if self.active_route_id:
            self._toggle_route_on_map(self.active_route_id, checked)

    def _close_details(self):
        self.active_route_id = None
        self.left_container.setCurrentIndex(0)

    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        order = self.table.item(row, 0).data(Qt.UserRole)
        
        root_obj = self.quick_map.rootObject()
        if root_obj and order:
            root_obj.centerOnStop(order["lat"], order["lon"])

    # ===========================================================================
    # GESTION ONGLET 2 : COMMANDES FUTURES
    # ===========================================================================
    
    def _setup_future_tab(self):
        layout = QVBoxLayout(self.tab_future)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Base de données des commandes en attente (Non traitées par l'algorithme du Jour 1)")
        title.setStyleSheet(f"font-weight: bold; color: {INK}; font-size: 14px; padding-bottom: 10px;")
        layout.addWidget(title)

        # Identification des commandes déjà assignées aujourd'hui
        assigned_order_ids = set()
        for truck_orders in self.algo_output:
            assigned_order_ids.update(truck_orders)

        # Filtrage des commandes futures (celles qui ne sont pas dans les camions d'aujourd'hui)
        future_orders = [
            (c_id, data) for c_id, data in self.orders_db.items() if c_id not in assigned_order_ids
        ]

        columns = ["N° commande", "Adresse", "Vol.", "Date Limite"]
        table_future = QTableWidget(len(future_orders), len(columns))
        table_future.setHorizontalHeaderLabels(columns)
        table_future.verticalHeader().setVisible(False)
        table_future.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_future.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_future.setShowGrid(False)

        header = table_future.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for col in (0, 2, 3): header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        table_future.setStyleSheet(f"""
            QTableWidget {{ border: 1px solid {LINE}; font-size: 12px; background: {PANEL_BG}; color: {INK}; border-radius: 8px; }}
            QHeaderView::section {{ background: #fafbfc; color: {INK_SOFT}; font-size: 11px; font-weight: 600; padding: 10px; border: none; border-bottom: 1px solid {LINE}; }}
            QTableWidget::item {{ padding: 10px; border-bottom: 1px solid #f0f0f0; }}
            QTableWidget::item:selected {{ background: {BLUE_PALE}; color: {INK}; }}
        """)

        for row, (c_id, data) in enumerate(future_orders):
            values = [c_id, data["adresse"], str(data["volume"]), data["date_limite"]]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 2: item.setTextAlignment(Qt.AlignCenter)
                table_future.setItem(row, col, item)

        layout.addWidget(table_future)

    def closeEvent(self, event):
        if os.path.exists(self.qml_filename): os.remove(self.qml_filename)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ManagerApp()
    window.show()
    sys.exit(app.exec())
