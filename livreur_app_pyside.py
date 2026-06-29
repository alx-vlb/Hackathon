import sys
import os
import requests

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QSizePolicy, QAbstractItemView, QScrollArea,
    QSplitter
)
# On remplace le moteur Web par le moteur graphique Quick de Qt
from PySide6.QtQuickWidgets import QQuickWidget 

# ===========================================================================
# 1) Données de la tournée
# ===========================================================================

ORDERS_DB = {
    "6A14837201FR": {"adresse": "12 Rue de Rivoli, 75004 Paris", "lat": 48.8556, "lon": 2.3611, "date_commande": "24/06/2026", "date_limite": "30/06/2026", "volume": 3},
    "6A14837202FR": {"adresse": "5 Avenue des Gobelins, 75013 Paris", "lat": 48.8389, "lon": 2.3540, "date_commande": "25/06/2026", "date_limite": "29/06/2026", "volume": 1},
    "6A14837203FR": {"adresse": "18 Rue Mouffetard, 75005 Paris", "lat": 48.8440, "lon": 2.3499, "date_commande": "23/06/2026", "date_limite": "29/06/2026", "volume": 2},
    "6A14837204FR": {"adresse": "7 Boulevard Saint-Marcel, 75013 Paris", "lat": 48.8378, "lon": 2.3621, "date_commande": "26/06/2026", "date_limite": "01/07/2026", "volume": 5},
    "6A14837205FR": {"adresse": "31 Rue Monge, 75005 Paris", "lat": 48.8447, "lon": 2.3508, "date_commande": "25/06/2026", "date_limite": "30/06/2026", "volume": 1},
    "6A14837206FR": {"adresse": "60 Rue de la Glaciere, 75013 Paris", "lat": 48.8323, "lon": 2.3475, "date_commande": "27/06/2026", "date_limite": "01/07/2026", "volume": 4},
    "6A14837207FR": {"adresse": "2 Place d'Italie, 75013 Paris", "lat": 48.8313, "lon": 2.3559, "date_commande": "24/06/2026", "date_limite": "29/06/2026", "volume": 2},
}

DEPOT = {"nom": "Dépôt - Bercy", "lat": 48.8389, "lon": 2.3833}

OPTIMIZED_ROUTE = ["6A14837201FR", "6A14837203FR", "6A14837205FR", "6A14837207FR", "6A14837202FR", "6A14837206FR", "6A14837204FR"]

ROUTE_INFO = {
    "temps_trajet_min": 96,
    "nb_stops": len(OPTIMIZED_ROUTE),
    "volume_total": sum(ORDERS_DB[o]["volume"] for o in OPTIMIZED_ROUTE),
    "distance_km": 18.4,
    "heure_depart": "08:30",
}

BLUE = "#2563eb"
BLUE_DARK = "#1d4ed8"
BLUE_PALE = "#eaf1fd"
INK = "#1f2533"
INK_SOFT = "#5b6472"
LINE = "#e3e7ee"
BG = "#f5f7fa"
PANEL_BG = "#ffffff"

# ===========================================================================
# 2) Code de la carte en QML (Le "HTML" version Qt Graphique)
# ===========================================================================

QML_MAP_CODE = f"""import QtQuick
import QtLocation
import QtPositioning

Rectangle {{
    id: root
    anchors.fill: parent
    color: "white"

    Plugin {{
        id: mapPlugin
        name: "osm"
    }}

    Map {{
        id: mainMap
        anchors.fill: parent
        plugin: mapPlugin
        center: QtPositioning.coordinate({DEPOT['lat']}, {DEPOT['lon']})
        zoomLevel: 13

        // --- AJOUT : Gestion des interactions de la souris et du trackpad ---
        
        // 1) Déplacement (Pan) en glissant la souris/le doigt
        DragHandler {{
            id: dragHandler
            target: null
            onTranslationChanged: (delta) => {{
                mainMap.pan(-delta.x, -delta.y)
            }}
        }}

        // 2) Zoom avec la molette de la souris ou le défilement trackpad
        WheelHandler {{
            id: wheelHandler
            onWheel: (event) => {{
                if (event.angleDelta.y > 0) {{
                    mainMap.zoomLevel = Math.min(mainMap.maximumZoomLevel, mainMap.zoomLevel + 0.5)
                }} else {{
                    mainMap.zoomLevel = Math.max(mainMap.minimumZoomLevel, mainMap.zoomLevel - 0.5)
                }}
            }}
        }}

        // 3) Zoom par pincement de doigts (Pinch-to-zoom sur Mac)
        PinchHandler {{
            id: pinchHandler
            target: null
            onScaleChanged: (delta) => {{
                mainMap.zoomLevel += Math.log2(delta)
            }}
        }}

        // --- Reste du code (Route et Marqueurs) ---
        MapPolyline {{
            id: routeLine
            line.color: "{BLUE}"
            line.width: 4
        }}

        MapItemView {{
            model: stopsModel
            delegate: MapQuickItem {{
                coordinate: QtPositioning.coordinate(modelData.lat, modelData.lon)
                anchorPoint: Qt.point(13, 13)
                sourceItem: Rectangle {{
                    width: 26; height: 26; radius: 13
                    color: modelData.isDepot ? "{INK}" : "{BLUE}"
                    border.color: "white"; border.width: 2
                    Text {{
                        anchors.centerIn: parent
                        text: modelData.label
                        color: "white"
                        font.bold: true
                        font.pixelSize: 11
                    }}
                }}
            }}
        }}
    }}

    function setRoutePath(pathPoints) {{
        var path = [];
        for (var i = 0; i < pathPoints.length; i++) {{
            path.push(QtPositioning.coordinate(pathPoints[i].lat, pathPoints[i].lon));
        }}
        routeLine.path = path;
    }}

    function centerOnStop(lat, lon) {{
        mainMap.center = QtPositioning.coordinate(lat, lon);
        mainMap.zoomLevel = 16;
    }}
}}
"""

# ===========================================================================
# 3) Routage OSRM
# ===========================================================================

def fetch_road_route(coords):
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}
    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        geometry = resp.json()["routes"][0]["geometry"]["coordinates"]
        return [{"lat": lat, "lon": lon} for lon, lat in geometry]
    except Exception as exc:
        print(f"[Avertissement] OSRM indisponible. Ligne droite de secours.")
        return [{"lat": lat, "lon": lon} for lat, lon in coords]

# ===========================================================================
# 4) Composants d'interface
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
        self.toggle_btn.setStyleSheet(f"QToolButton {{ background: {PANEL_BG}; border: none; border-bottom: 1px solid {LINE}; padding: 10px 4px; font-weight: 600; font-size: 13px; color: {INK}; text-align: left; }}")
        self.toggle_btn.clicked.connect(self._toggle)

        self.content = QWidget()
        self.content.setStyleSheet(f"background: {PANEL_BG};")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 10, 12, 12)
        self.content.setVisible(start_open)

        outer.addWidget(self.toggle_btn)
        outer.addWidget(self.content)
        self.setStyleSheet(f"CollapsiblePanel {{ background: {PANEL_BG}; border: 1px solid {LINE}; border-radius: 8px; }}")

    def _toggle(self):
        opened = self.toggle_btn.isChecked()
        self.content.setVisible(opened)
        self.toggle_btn.setArrowType(Qt.DownArrow if opened else Qt.RightArrow)

# ===========================================================================
# 5) Fenêtre principale
# ===========================================================================

class LivreurApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ma Tournée — Livreur (Mode Natif)")
        self.resize(1280, 760)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        # --- CORRECTION ICI : On récupère dynamiquement le dossier du script ---
        dossier_du_script = os.path.dirname(os.path.abspath(__file__))
        self.qml_filename = os.path.join(dossier_du_script, "map_native.qml")

        # Écriture du fichier de carte QML temporaire au bon endroit
        with open(self.qml_filename, "w", encoding="utf-8") as f:
            f.write(QML_MAP_CODE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")

        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_map_panel())
        splitter.setSizes([450, 830])

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.addWidget(splitter)
        root.addWidget(body)

        self._load_data()

    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{PANEL_BG}; border-bottom:1px solid {LINE};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)

        brand = QLabel("📦 Ma Tournée")
        brand.setStyleSheet(f"color:{BLUE_DARK}; font-weight:700; font-size:14px;")
        breadcrumb = QLabel("   Livreur  ›  Tournée du jour (Natif)")
        breadcrumb.setStyleSheet(f"color:{INK_SOFT}; font-size:12px;")
        driver = QLabel("Aymen B. — Tournée Paris 13")
        driver.setStyleSheet(f"background:{BLUE_PALE}; color:{BLUE_DARK}; font-weight:600; font-size:12px; padding:5px 12px; border-radius:11px;")

        layout.addWidget(brand)
        layout.addWidget(breadcrumb)
        layout.addStretch()
        layout.addWidget(driver)
        return bar

    def _build_sidebar(self):
        sidebar_content = QWidget()
        sidebar_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(sidebar_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.panel_summary = CollapsiblePanel("Résumé de la tournée")
        self._build_summary(self.panel_summary.content_layout)
        layout.addWidget(self.panel_summary)

        self.panel_orders = CollapsiblePanel("Livraisons")
        self._build_orders_table(self.panel_orders.content_layout)
        layout.addWidget(self.panel_orders, 1)

        scroll = QScrollArea()
        scroll.setWidget(sidebar_content)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        return scroll

    def _build_summary(self, layout):
        grid = QGridLayout()
        grid.setSpacing(8)
        layout.addLayout(grid)

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
        self.depart_label.setWordWrap(True)
        self.depart_label.setStyleSheet(f"color:{INK_SOFT}; font-size:11.5px; margin-top:6px;")
        layout.addWidget(self.depart_label)

    def _build_orders_table(self, layout):
        columns = ["#", "N° commande", "Adresse", "Vol.", "Commandée le", "Livraison prévue"]
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(280)
        self.table.setWordWrap(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (0, 1, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.table.setStyleSheet(f"""
            QTableWidget {{ border: none; font-size: 11px; gridline-color: {LINE}; background: {PANEL_BG}; color: {INK}; }}
            QHeaderView::section {{ background: #fafbfc; color: {INK_SOFT}; font-size: 10px; font-weight: 600; padding: 6px; border: none; border-bottom: 1px solid {LINE}; }}
            QTableWidget::item {{ padding: 6px 4px; color: {INK}; }}
            QTableWidget::item:selected {{ background: {BLUE_PALE}; color: {INK}; }}
        """)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self.table)

    def _build_map_panel(self):
        frame = QFrame()
        frame.setStyleSheet(f"background:{PANEL_BG}; border:1px solid {LINE}; border-radius:8px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- INSTANCIATION DU COMPOSANT NATIF ---
        self.quick_map = QQuickWidget()
        self.quick_map.setResizeMode(QQuickWidget.SizeRootObjectToView)
        layout.addWidget(self.quick_map)
        return frame

    def _load_data(self):
        info = ROUTE_INFO
        self.summary_labels["temps"].setText(f"{divmod(info['temps_trajet_min'], 60)[0]}h{divmod(info['temps_trajet_min'], 60)[1]:02d}")
        self.summary_labels["stops"].setText(str(info["nb_stops"]))
        self.summary_labels["volume"].setText(str(info["volume_total"]))
        self.summary_labels["distance"].setText(f"{info['distance_km']} km")
        self.depart_label.setText(f"Départ prévu à {info['heure_depart']} depuis {DEPOT['nom']}")

        # Préparation de la liste des arrêts pour la carte QML
        qml_stops = [{"lat": DEPOT["lat"], "lon": DEPOT["lon"], "label": "D", "isDepot": True}]
        ordered_coords = [(DEPOT["lat"], DEPOT["lon"])]

        self.table.setRowCount(len(OPTIMIZED_ROUTE))
        for row, order_number in enumerate(OPTIMIZED_ROUTE):
            d = ORDERS_DB[order_number]
            qml_stops.append({"lat": d["lat"], "lon": d["lon"], "label": str(row + 1), "isDepot": False})
            ordered_coords.append((d["lat"], d["lon"]))

            values = [str(row + 1), order_number, d["adresse"], str(d["volume"]), d["date_commande"], d["date_limite"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0: item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            self.table.item(row, 0).setData(Qt.UserRole, order_number)

        self.table.resizeRowsToContents()

        # Injection des données d'arrêts directement dans le contexte QML
        self.quick_map.rootContext().setContextProperty("stopsModel", qml_stops)
        self.quick_map.setSource(QUrl.fromLocalFile(self.qml_filename))

        # Calcul de la route (OSRM) et mise à jour synchrone du tracé QML
        road_route = fetch_road_route(ordered_coords)
        root_qml_object = self.quick_map.rootObject()
        if root_qml_object:
            root_qml_object.setRoutePath(road_route)

    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected: return
        row = selected[0].row()
        order_number = self.table.item(row, 0).data(Qt.UserRole)
        
        # Récupération des coordonnées et recentrage natif
        d = ORDERS_DB[order_number]
        root_qml_object = self.quick_map.rootObject()
        if root_qml_object:
            root_qml_object.centerOnStop(d["lat"], d["lon"])

    def closeEvent(self, event):
        # Nettoyage du fichier QML au moment de fermer
        if os.path.exists(self.qml_filename):
            os.remove(self.qml_filename)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LivreurApp()
    window.show()
    sys.exit(app.exec())
