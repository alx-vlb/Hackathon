"""
Application livreur - version PySide6
----------------------------------------
Interface bureau native (PySide6) avec une carte OpenStreetMap intégrée
(via QWebEngineView + Leaflet) qui affiche un VRAI tracé routier (et non
plus une ligne droite entre les points), calculé via l'API de routage
OSRM (https://router.project-osrm.org, service public, sans clé).

Important : l'ordre de passage (OPTIMIZED_ROUTE) et les indicateurs de
tournée (ROUTE_INFO : temps, nb stops, volume) restent ceux fournis par
votre moteur d'optimisation - on ne les recalcule pas. OSRM est utilisé
uniquement pour obtenir la géométrie du trajet le long des routes, pour
un affichage fidèle sur la carte.

Dépendances :
    pip install PySide6 PySide6-Addons requests

Lancement :
    python livreur_app_pyside.py
"""

import sys
import json

import requests
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QSizePolicy, QAbstractItemView, QScrollArea,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


# ===========================================================================
# 1) "Base de données" des commandes (à remplacer par une vraie requête SQL)
# ===========================================================================

ORDERS_DB = {
    "6A14837201FR": {
        "adresse": "12 Rue de Rivoli, 75004 Paris",
        "lat": 48.8556, "lon": 2.3611,
        "date_commande": "24/06/2026",
        "date_limite": "30/06/2026",
        "volume": 3,
    },
    "6A14837202FR": {
        "adresse": "5 Avenue des Gobelins, 75013 Paris",
        "lat": 48.8389, "lon": 2.3540,
        "date_commande": "25/06/2026",
        "date_limite": "29/06/2026",
        "volume": 1,
    },
    "6A14837203FR": {
        "adresse": "18 Rue Mouffetard, 75005 Paris",
        "lat": 48.8440, "lon": 2.3499,
        "date_commande": "23/06/2026",
        "date_limite": "29/06/2026",
        "volume": 2,
    },
    "6A14837204FR": {
        "adresse": "7 Boulevard Saint-Marcel, 75013 Paris",
        "lat": 48.8378, "lon": 2.3621,
        "date_commande": "26/06/2026",
        "date_limite": "01/07/2026",
        "volume": 5,
    },
    "6A14837205FR": {
        "adresse": "31 Rue Monge, 75005 Paris",
        "lat": 48.8447, "lon": 2.3508,
        "date_commande": "25/06/2026",
        "date_limite": "30/06/2026",
        "volume": 1,
    },
    "6A14837206FR": {
        "adresse": "60 Rue de la Glaciere, 75013 Paris",
        "lat": 48.8323, "lon": 2.3475,
        "date_commande": "27/06/2026",
        "date_limite": "01/07/2026",
        "volume": 4,
    },
    "6A14837207FR": {
        "adresse": "2 Place d'Italie, 75013 Paris",
        "lat": 48.8313, "lon": 2.3559,
        "date_commande": "24/06/2026",
        "date_limite": "29/06/2026",
        "volume": 2,
    },
}

DEPOT = {"nom": "Dépôt - Bercy", "lat": 48.8389, "lon": 2.3833}

# Ordre de tournée déjà optimisé en temps (sortie de votre moteur d'optimisation)
OPTIMIZED_ROUTE = [
    "6A14837201FR",
    "6A14837203FR",
    "6A14837205FR",
    "6A14837207FR",
    "6A14837202FR",
    "6A14837206FR",
    "6A14837204FR",
]

ROUTE_INFO = {
    "temps_trajet_min": 96,
    "nb_stops": len(OPTIMIZED_ROUTE),
    "volume_total": sum(ORDERS_DB[o]["volume"] for o in OPTIMIZED_ROUTE),
    "distance_km": 18.4,
    "heure_depart": "08:30",
}


# ===========================================================================
# 2) Couleurs (mêmes tokens que les versions précédentes, pour rester cohérent
#    avec la maquette de référence)
# ===========================================================================

BLUE = "#2563eb"
BLUE_DARK = "#1d4ed8"
BLUE_PALE = "#eaf1fd"
INK = "#1f2533"
INK_SOFT = "#5b6472"
LINE = "#e3e7ee"
BG = "#f5f7fa"
PANEL_BG = "#ffffff"


# ===========================================================================
# 3) Routage réel le long des rues (OSRM)
# ===========================================================================

def fetch_road_route(coords):
    """
    coords : liste de (lat, lon) dans l'ordre de passage (dépôt en premier).

    Interroge le service public OSRM pour obtenir la géométrie du trajet
    qui suit réellement les routes entre tous les points, dans l'ordre
    donné (on ne ré-optimise rien, OSRM ne fait que "relier les points
    par la route" segment par segment, dans l'ordre fourni).

    Renvoie une liste de (lat, lon) à tracer sur la carte. En cas
    d'échec (pas d'internet, service indisponible...), retombe sur les
    points d'origine (ligne droite) pour que l'application reste utilisable.
    """
    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        geometry = payload["routes"][0]["geometry"]["coordinates"]  # [lon, lat]
        return [(lat, lon) for lon, lat in geometry]
    except Exception as exc:  # pas d'internet, service down, etc.
        print(f"[avertissement] Tracé routier indisponible ({exc}). "
              f"Affichage d'une ligne droite de secours.")
        return coords


# ===========================================================================
# 4) Page carte (Leaflet) générée et injectée dans QWebEngineView
# ===========================================================================

def build_map_html(depot, stops, road_route):
    payload = {
        "depot": depot,
        "stops": [
            {
                "lat": s["lat"], "lon": s["lon"], "label": str(s["ordre"]),
                "order_number": s["numero_commande"], "address": s["adresse"],
                "volume": s["volume"], "due": s["date_limite"],
            }
            for s in stops
        ],
        "route": road_route,
    }
    data_json = json.dumps(payload)

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  html, body, #map {{ margin:0; padding:0; height:100%; width:100%; }}
  .pin {{
    background:{BLUE}; color:white; width:26px; height:26px; border-radius:50%;
    display:flex; align-items:center; justify-content:center; font-size:12px;
    font-weight:700; border:2px solid white; box-shadow:0 1px 3px rgba(0,0,0,.35);
  }}
  .pin-depot {{ background:{INK}; }}
  .leaflet-popup-content {{ font-size:12.5px; font-family:'Segoe UI',sans-serif; }}
</style>
</head>
<body>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = {data_json};
const map = L.map('map');

L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '&copy; OpenStreetMap contributors', maxZoom: 19
}}).addTo(map);

function numberedIcon(label, isDepot) {{
  return L.divIcon({{
    className: '',
    html: `<div class="pin ${{isDepot ? 'pin-depot' : ''}}">${{label}}</div>`,
    iconSize: [26, 26], iconAnchor: [13, 13]
  }});
}}

const markers = {{}};

L.marker([DATA.depot.lat, DATA.depot.lon], {{icon: numberedIcon('D', true)}})
  .addTo(map)
  .bindPopup(`<b>Dépôt</b><br>${{DATA.depot.nom}}`);

DATA.stops.forEach(s => {{
  const m = L.marker([s.lat, s.lon], {{icon: numberedIcon(s.label, false)}}).addTo(map);
  m.bindPopup(
    `<b>Arrêt ${{s.label}} — ${{s.order_number}}</b><br>${{s.address}}` +
    `<br>Volume : ${{s.volume}}<br>Livraison prévue : ${{s.due}}`
  );
  markers[s.order_number] = m;
}});

if (DATA.route && DATA.route.length > 1) {{
  const latlngs = DATA.route.map(p => [p[0], p[1]]);
  L.polyline(latlngs, {{color: '{BLUE}', weight: 4, opacity: 0.85}}).addTo(map);
  map.fitBounds(latlngs, {{padding: [40, 40]}});
}} else {{
  map.setView([DATA.depot.lat, DATA.depot.lon], 13);
}}

// Appelée depuis Python (runJavaScript) quand on clique une ligne du tableau
function focusStop(orderNumber) {{
  const m = markers[orderNumber];
  if (m) {{
    map.setView(m.getLatLng(), 15, {{animate: true}});
    m.openPopup();
  }}
}}
</script>
</body></html>"""


# ===========================================================================
# 5) Widget panneau repliable (équivalent des menus déroulants de la maquette)
# ===========================================================================

class CollapsiblePanel(QWidget):
    def __init__(self, title, start_open=True, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.toggle_btn = QToolButton()
        self.toggle_btn.setText(f"  {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(start_open)
        self.toggle_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.toggle_btn.setArrowType(Qt.DownArrow if start_open else Qt.RightArrow)
        self.toggle_btn.setStyleSheet(f"""
            QToolButton {{
                background: {PANEL_BG};
                border: none;
                border-bottom: 1px solid {LINE};
                padding: 10px 4px;
                font-weight: 600;
                font-size: 13px;
                color: {INK};
                text-align: left;
            }}
        """)
        self.toggle_btn.clicked.connect(self._toggle)

        self.content = QWidget()
        self.content.setStyleSheet(f"background: {PANEL_BG};")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 10, 12, 12)
        self.content.setVisible(start_open)

        outer.addWidget(self.toggle_btn)
        outer.addWidget(self.content)

        self.setStyleSheet(f"""
            CollapsiblePanel {{
                background: {PANEL_BG};
                border: 1px solid {LINE};
                border-radius: 8px;
            }}
        """)

    def _toggle(self):
        opened = self.toggle_btn.isChecked()
        self.content.setVisible(opened)
        self.toggle_btn.setArrowType(Qt.DownArrow if opened else Qt.RightArrow)


# ===========================================================================
# 6) Fenêtre principale
# ===========================================================================

class LivreurApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ma Tournée — Livreur")
        self.resize(1280, 760)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(10)
        root.addWidget(body)

        body_layout.addWidget(self._build_sidebar(), 0)
        body_layout.addWidget(self._build_map_panel(), 1)

        self._load_data()

    # ------------------------------------------------------------- topbar --

    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background:{PANEL_BG}; border-bottom:1px solid {LINE};")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)

        brand = QLabel("📦 Ma Tournée")
        brand.setStyleSheet(f"color:{BLUE_DARK}; font-weight:700; font-size:14px;")

        breadcrumb = QLabel("   Livreur  ›  Tournée du jour")
        breadcrumb.setStyleSheet(f"color:{INK_SOFT}; font-size:12px;")

        driver = QLabel("Aymen B. — Tournée Paris 13")
        driver.setStyleSheet(f"""
            background:{BLUE_PALE}; color:{BLUE_DARK};
            font-weight:600; font-size:12px;
            padding:5px 12px; border-radius:11px;
        """)

        layout.addWidget(brand)
        layout.addWidget(breadcrumb)
        layout.addStretch()
        layout.addWidget(driver)
        return bar

    # ------------------------------------------------------------ sidebar --

    def _build_sidebar(self):
        sidebar_content = QWidget()
        layout = QVBoxLayout(sidebar_content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.panel_summary = CollapsiblePanel("Résumé de la tournée")
        self._build_summary(self.panel_summary.content_layout)
        layout.addWidget(self.panel_summary)

        self.panel_orders = CollapsiblePanel("Livraisons")
        self._build_orders_table(self.panel_orders.content_layout)
        layout.addWidget(self.panel_orders, 1)

        self.panel_legend = CollapsiblePanel("Légende", start_open=False)
        self._build_legend(self.panel_legend.content_layout)
        layout.addWidget(self.panel_legend)

        scroll = QScrollArea()
        scroll.setWidget(sidebar_content)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(370)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        return scroll

    def _build_summary(self, layout):
        grid = QGridLayout()
        grid.setSpacing(8)
        layout.addLayout(grid)

        self.summary_labels = {}
        items = [
            ("temps", "Temps estimé"),
            ("stops", "Stops"),
            ("volume", "Volume total"),
            ("distance", "Distance"),
        ]
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
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(220)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (0, 1, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size: 11px; gridline-color: {LINE};
            }}
            QHeaderView::section {{
                background: #fafbfc; color: {INK_SOFT};
                font-size: 10px; font-weight: 600;
                padding: 6px; border: none; border-bottom: 1px solid {LINE};
            }}
            QTableWidget::item {{ padding: 4px; }}
            QTableWidget::item:selected {{
                background: {BLUE_PALE}; color: {INK};
            }}
        """)

        self.table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self.table)

    def _build_legend(self, layout):
        rows = [
            ("⚫", "Dépôt de départ"),
            ("🔵", "Arrêt de livraison"),
            ("—", "Itinéraire (suit les routes réelles via OSRM)"),
        ]
        for icon, text in rows:
            row = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet(f"color:{BLUE}; font-size:12px;")
            text_lbl = QLabel(text)
            text_lbl.setStyleSheet(f"color:{INK_SOFT}; font-size:11px;")
            row.addWidget(icon_lbl)
            row.addWidget(text_lbl)
            row.addStretch()
            layout.addLayout(row)

    # --------------------------------------------------------- map panel --

    def _build_map_panel(self):
        frame = QFrame()
        frame.setStyleSheet(f"background:{PANEL_BG}; border:1px solid {LINE}; border-radius:8px;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.web_view)
        return frame

    # -------------------------------------------------------------- data --

    def _load_data(self):
        info = ROUTE_INFO
        h, m = divmod(info["temps_trajet_min"], 60)
        self.summary_labels["temps"].setText(f"{h}h{m:02d}")
        self.summary_labels["stops"].setText(str(info["nb_stops"]))
        self.summary_labels["volume"].setText(str(info["volume_total"]))
        self.summary_labels["distance"].setText(f"{info['distance_km']} km")
        self.depart_label.setText(
            f"Départ prévu à {info['heure_depart']} depuis {DEPOT['nom']}"
        )

        stops = []
        ordered_coords = [(DEPOT["lat"], DEPOT["lon"])]

        self.table.setRowCount(len(OPTIMIZED_ROUTE))
        for row, order_number in enumerate(OPTIMIZED_ROUTE):
            d = ORDERS_DB[order_number]
            stops.append({
                "ordre": row + 1,
                "numero_commande": order_number,
                **d,
            })
            ordered_coords.append((d["lat"], d["lon"]))

            values = [
                str(row + 1), order_number, d["adresse"],
                str(d["volume"]), d["date_commande"], d["date_limite"],
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            # On garde le numéro de commande accessible sur la ligne
            self.table.item(row, 0).setData(Qt.UserRole, order_number)

        # Calcule le tracé qui suit réellement les routes (OSRM)
        road_route = fetch_road_route(ordered_coords)

        html = build_map_html(DEPOT, stops, road_route)
        self.web_view.setHtml(html, QUrl("https://localhost/"))

    # ------------------------------------------------------- interaction --

    def _on_row_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        order_number = self.table.item(row, 0).data(Qt.UserRole)
        self.web_view.page().runJavaScript(f"focusStop('{order_number}');")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LivreurApp()
    window.show()
    sys.exit(app.exec())