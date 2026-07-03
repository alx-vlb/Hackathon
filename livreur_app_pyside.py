import sys
import os
import requests
import colorsys

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QScrollArea, QSplitter, QStackedWidget, 
    QCheckBox, QPushButton, QAbstractItemView, QLineEdit, QTabWidget,
    QSizePolicy
)
from PySide6.QtQuickWidgets import QQuickWidget
import angle_main as main
import donnees

# On place le dépôt à ses vraie coordonnées dans Paris
DEPOT = {"nom": "Dépôt Central", "lat": 48.8566, "lon": 2.3522}

# Thème de l'interface
BLUE_DARK, BLUE_PALE, INK, INK_SOFT, LINE, BG, PANEL_BG = "#0f691e", "#eaf1fd", "#1f2533", "#5b6472", "#e3e7ee", "#f5f7fa", "#ffffff"

# Fonctions utiles

def get_route_color(day_idx, truck_idx):
    #On cherche à Génèrer une couleur unique avec une dispersion maximale pour les camions
    # On attribue une plage fixe de 10 index par jour.
    slot_index = (day_idx * 12) + truck_idx/2
    
    # On utilise le nombre d'or pour tourner sur le spectre chromatique sans retomber sur une couleur déjà utilisée
    hue = (slot_index * 0.618033988749895) % 1.0
    
    # Conversion en Hexadécimal RGB (Saturé à 80% et Luminosité à 70% pour être lisible mais avec un style un peu sobre et professionnel)
    return '#{:02x}{:02x}{:02x}'.format(*(int(c*255) for c in colorsys.hsv_to_rgb(hue, 0.80, 0.70)))


#Tracé des routes
def fetch_road_route(coords):

    coord_str = ";".join(f"{lon},{lat}" for lat, lon in coords) #On adapte le format des coordonnées pour l'API d'OSRM
    url = f"https://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson" #On prépare la requête qu'on envoie à au serveurs publics d'OSRM pour avoir le tracé complet des routes pour des camions
    try:
        resp = requests.get(url, timeout=4) #On envoie la requête en imposant un timeout de 4 secondes pour éviter que le programme se bloque indéfiniment en cas de conflit
        geometry = resp.json()["routes"][0]["geometry"]["coordinates"] #La réponse est au format json on l'extrait donc sous la forme d'une liste
        return [{"lat": lat, "lon": lon} for lon, lat in geometry] #On met enfin tout sous la forme d'une liste de dictionnaire, c'est le format adapté au code QML de la carte
    except:
        return [{"lat": lat, "lon": lon} for lat, lon in coords] #Si l'utilisateur ne peut pas communiquer avec les serveur d'OSRM, on affiche simplement les points reliés par des lignes droites

# Code QML de la carte

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

# Ne maîtrisant pas assez le Java Script, nous avons fait appel à un agent IA pour générer le code QML de la carte 

# Composants Graphiques de l'interface

class CollapsiblePanel(QWidget): #on créé une classe "Menu déroulant" car il n'y en a pas parmis les composants de base de Qt
    def __init__(self, title, start_open=True, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True) #On force Qt à appliquer le code CSS à notre attribut car il ne le fait pas par défault 
        

        
        outer = QVBoxLayout(self) #self va empiler les éléments de façon verticale
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        
        self.toggle_btn = QPushButton() #rends l'entête cliquable
        self.toggle_btn.setText(title)
        self.toggle_btn.setCheckable(True) #transforme le bouton en interrupteur on/off
        self.toggle_btn.setChecked(start_open) #définit l'état initial de l'interrupteur
        
        self.toggle_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) #Le bouton s'ettire sur toute la largeur de la fenêtre de façon à ce que celle-ci soit ajustable
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{ 
                background: #fafbfc; 
                border: none; 
                border-bottom: 1px solid {LINE}; 
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;         
                padding: 12px 15px; 
                font-weight: 600; 
                font-size: 13px; 
                color: {INK}; 
                text-align: left; 
            }}
            QPushButton:hover {{
                background: #f0f2f5;
            }}
        """) # Code CSS pour le designe du bouton
        self.toggle_btn.clicked.connect(self._toggle) #Cliquer sur le bouton actionne la fonction _toggle
        
        self.content = QWidget() #on créé le "tiroir" dans lequel on mettra les informations de notre menu déroulant
        self.content.setStyleSheet(f"background: {PANEL_BG}; border-bottom-left-radius: 7px; border-bottom-right-radius: 7px;") #oon arrondit les angles du bas
        self.content_layout = QVBoxLayout(self.content) #On définit un layout propre au tiroir pour pouvoir organiser les éléments qu'il contient
        self.content_layout.setContentsMargins(12, 12, 12, 12) #ajout d'un padding
        self.content.setVisible(start_open) #Le tiroir sera visible ou non au démarrage en fonction de la valeur de start_open
        
        #On empile nos éléments verticalement dans outer
        outer.addWidget(self.toggle_btn)
        outer.addWidget(self.content)

        #On créé une bordure autour de self de façon à pouvoir empile tout les boutons "jours" élégamment.
        self.setStyleSheet(f"CollapsiblePanel {{ background: {PANEL_BG}; border: 1px solid {LINE}; border-radius: 8px; margin-bottom: 12px; }}")

    def _toggle(self): #permet d'afficher/masquer les menus déroulants.
        
        opened = self.toggle_btn.isChecked()
        self.content.setVisible(opened)

class RouteCard(QFrame):
    on_details_requested = Signal(str) #Émettra un str lorsque l'utilisateur cliquera sur voir détails
    on_visibility_toggled = Signal(str, bool) #Émets aussi un booléen 

    def __init__(self, route_data):
        super().__init__()
        self.route_data = route_data #On garde en mémoire le dictionnaire contenant toutes les infos du camion reçu en paramètre
        self.setStyleSheet(f"RouteCard {{ background: #fafbfc; border: 1px solid {LINE}; border-radius: 6px; }} RouteCard:hover {{ border-color: {route_data['color']}; background: #ffffff; }}") #La case qui affiche la tournéee change d'aspect lorsque la souris passe dessus de sorte à comprendre intuitivement que l'on peut intéragir avec
        
        layout = QHBoxLayout(self)  #Ici on a un layout horizontal (QH) et non vertical (QV) comme tout à l'heure 
        layout.setContentsMargins(12, 12, 12, 12)

        self.checkbox = QCheckBox() #on définit la case à cocher
        self.checkbox.setStyleSheet(f"QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 2px solid {route_data['color']}; }} QCheckBox::indicator:checked {{ background: {route_data['color']}; }}") #On dessine la case à cocher, elle prend la même couleur que celle utilisé pour tracer la route
        self.checkbox.toggled.connect(lambda checked: self.on_visibility_toggled.emit(self.route_data['id'], checked)) #envoie à l'application l'information qu'une case à été coché (checked) et qu'elle case à été coché (self.route_data['id'])
        
        #On ajoute toute les informations que l'on souhaite afficher dans la case
        #======================================================================
        info_layout = QVBoxLayout() #empiler le titre et le sous-titre
        driver_display = route_data['driver'].strip() if route_data['driver'].strip() else "Non attribuée" #si aucun chauffeur n'est attribué à la tournée on écrit "Non attribuée"
        
        self.title = QLabel(f"{route_data['label_display']} - {driver_display}")
        self.title.setStyleSheet(f"font-weight: bold; color: {INK}; font-size: 13px; background: transparent;")
        
        self.subtitle = QLabel(f"Commandes : {len(route_data['orders'])}  .  Départ : {route_data['stats']['depart']}")
        self.subtitle.setStyleSheet(f"font-size: 11px; color: {INK_SOFT}; background: transparent;")
        
        info_layout.addWidget(self.title)
        info_layout.addWidget(self.subtitle)

        btn_details = QPushButton("Voir détails")
        btn_details.setStyleSheet(f"color: {route_data['color']}; font-weight: bold; border: none; background: transparent; font-size: 12px;")
        btn_details.setCursor(Qt.PointingHandCursor)
        btn_details.clicked.connect(lambda: self.on_details_requested.emit(self.route_data['id']))
        #======================================================================

        #On place maintenant les éléments dans le tiroir comme on l'a fait dans la calsse précédente
        layout.addWidget(self.checkbox)
        layout.addLayout(info_layout)
        layout.addStretch() #On ajoute un espace entre le bouton "voir détails" et la checkbox et les infos par souci d'esthétisme.
        layout.addWidget(btn_details)

#Les 3 fonctions qui suivent servent à mettre à jour la carte en direct sans avoir besoin de la regénérer à chaque fois

    def update_driver_name_display(self, new_name):
        driver_display = new_name.strip() if new_name.strip() else "Non attribuée"
        self.title.setText(f"{self.route_data['label_display']} - {driver_display}")

    def update_departure_display(self, new_depart):
        self.subtitle.setText(f"Commandes : {len(self.route_data['orders'])}  .  Départ : {new_depart}")

    def set_checkbox_state(self, checked):
        self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        self.checkbox.blockSignals(False)

#la fenêtre principale, celle que le magasin utilise pour voir toutes les tournées du dépôt

class ManagerApp(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestion des commandes du magasin")
        self.resize(1340, 840)
        self.setStyleSheet(f"QMainWindow {{ background: {BG}; }}")

        self.route_cards_references = {} #on garde une référence vers chaque RouteCard affichée, pour pouvoir les mettre à jour depuis l'extérieur (ex: cocher une case) sans reconstruire toute la liste
        self.active_route_id = None #id de la tournée actuellement affichée dans la page détail, None si on est sur la vue d'ensemble
        
        self.orders_db = {} #toutes les commandes de tous les jours, remplies par _load_all_data_from_backend()
        self.routes_model = {} #toutes les tournées de tous les jours (regroupements de commandes déjà optimisés par l'algo)

        self._load_all_data_from_backend() #on va chercher les données calculées par angle_main.py et on les remet en forme pour l'interface

        dossier_du_script = os.path.dirname(os.path.abspath(__file__))
        self.qml_filename = os.path.join(dossier_du_script, "map_manager.qml")
        with open(self.qml_filename, "w", encoding="utf-8") as f: #le QML doit être un vrai fichier sur le disque pour que QQuickWidget puisse le charger, on ne peut pas lui passer une simple chaîne de caractères
            f.write(QML_MAP_CODE)

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

        self.tabs.addTab(self.tab_today, "Planning des Tournées")
        self.tabs.addTab(self.tab_future, "Synthèse Globale Commandes")
        
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.addWidget(self.tabs)
        root.addWidget(body)

    def _load_all_data_from_backend(self): #le pont entre le moteur de calcul (angle_main.py) et l'interface : on lit ses variables globales et on les transforme en dictionnaires que l'UI sait afficher
        for cid, client in main.Clients.items():
            if isinstance(cid, tuple) or cid == 0:
                continue #le dico Clients contient chaque client deux fois (une fois par id entier, une fois par coordonnées) + le dépôt : on ne garde que les entrées par id entier
            
            
           
            client_idx = cid - 1 #les id clients commencent à 1 (0 = dépôt), mais demande[jour] est un tableau qui commence à l'index 0 : d'où le décalag
           
           
            for jour_idx in range(main.nb_jours):
                vol = main.demande[jour_idx][client_idx]
                if vol > 0: #s'il n'y a pas de volume ce jour-là pour ce client, on ne crée pas de commande
                    order_id = f"C-{cid}-J{jour_idx+1}" #identifiant unique = client + jour, pour ne pas mélanger les commandes du même client à des jours différents
                    rue = donnees.rues[cid % len(donnees.rues)] #on pioche un nom de rue "au hasard" dans la liste de donnees.py, juste pour avoir un affichage lisible (pas de vraie adresse dans les données du moteur)
                    lat, lon = client.coordonnées
                    
                    if -100 < lat < 100 and -100 < lon < 100 and not (40 < lat < 55): #si les coordonnées ressemblent à du cartésien abstrait (généré par generer_coordonnees) plutôt qu'à du GPS réel autour de Paris, on les "projette" grossièrement sur Paris pour que la carte affiche quelque chose de cohérent

                        lat = 48.8566 + (lat * 0.003)
                        lon = 2.3522 + (lon * 0.003)
                    
                    self.orders_db[order_id] = {
                        "adresse": f"{rue}, 75000 Paris",
                        "date_limite": f"Jour {jour_idx+1}",
                        "volume": vol,
                        "lat": lat,
                        "lon": lon,
                        "jour": jour_idx + 1
                    }

        for jour in range(1, main.nb_jours + 1): #ici on reconstruit les tournées pour tous les jours

            tournees_du_jour = main.course.get(jour, [])
            for idx, trajet in enumerate(tournees_du_jour):
                client_ids = [cid for cid in trajet if cid != 0] #on retire les passages au dépôt (0), qui ouvrent et ferment chaque trajet
                if not client_ids:
                    continue
                    
                unique_route_id = f"J{jour}_Camion_{idx+1}" #il faut préfixer par le jour, sinon "Camion N°1" du jour 2 écraserait "Camion N°1" du jour 1 dans routes_model

                course_orders = []
                for cid in client_ids:
                    order_id = f"C-{cid}-J{jour}"
                    if order_id in self.orders_db: #normalement toujours vrai puisqu'on vient de le construire juste au-dessus, mais on vérifie par sécurité
                        order_data = self.orders_db[order_id].copy()
                        order_data["id"] = order_id
                        course_orders.append(order_data)

                self.routes_model[unique_route_id] = {
                    "id": unique_route_id,
                    "jour": jour,
                    "label_display": f"Camion N°{idx+1}",
                    "driver": "",  
                    "stats": {"depart": "08:30"},
                    "color": get_route_color(jour, idx),
                    "orders": course_orders,
                    "visible": False
                }

    def _build_topbar(self): #juste le bandeau du haut avec le titre, rien d'interactif ici
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

    def _setup_today_tab(self): #construit l'onglet principal : à gauche la liste des tournées (ou le détail d'une tournée), à droite la carte
        layout = QVBoxLayout(self.tab_today)
        layout.setContentsMargins(0, 10, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal) #permet de faire glisser la frontière entre le panneau de gauche et la carte
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        
        self.left_container = QStackedWidget() #un "empileur" de pages : une seule des deux pages ajoutées ci-dessous est visible à la fois (comme des onglets, mais sans barre d'onglets visible)
        self.left_container.setMinimumWidth(460)
        self.left_container.setStyleSheet(f"background: {PANEL_BG}; border: none;")
        
        self.view_dispatch = self._build_multi_day_dispatch_page() #page 0 : la liste de toutes les tournées, regroupées par jour
        self.view_details = self._build_details_page() #page 1 : le détail d'une tournée précise (ordre de passage, affectation d'un chauffeur...)
        self.left_container.addWidget(self.view_dispatch)
        self.left_container.addWidget(self.view_details)
        
        self.map_frame = QFrame()
        self.map_frame.setStyleSheet(f"background:{PANEL_BG}; border:1px solid {LINE}; border-radius:8px;")
        map_layout = QVBoxLayout(self.map_frame)
        map_layout.setContentsMargins(0, 0, 0, 0)

        self.quick_map = QQuickWidget() #widget Qt qui sait afficher du QML (donc notre carte OpenStreetMap) à l'intérieur d'une fenêtre PySide "classique"
        
        self.quick_map.setResizeMode(QQuickWidget.SizeRootObjectToView)  #la carte QML doit s'adapter à la taille du widget, pas l'inverse

        self.quick_map.setSource(QUrl.fromLocalFile(self.qml_filename))
        map_layout.addWidget(self.quick_map)

        splitter.addWidget(self.left_container)
        splitter.addWidget(self.map_frame)
        splitter.setSizes([460, 880]) #largeur de départ de chaque côté, l'utilisateur peut ensuite l'ajuster à la souris
        layout.addWidget(splitter)

    def _build_multi_day_dispatch_page(self): #la vue d'ensemble : un menu déroulant par jour, contenant les tournées de ce jour-là
        scroll = QScrollArea() #indispensable car la liste peut devenir plus haute que l'écran une fois tous les jours dépliés
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {PANEL_BG}; border: none; }}")
        
        content = QWidget()
        content.setStyleSheet(f"background: {PANEL_BG};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)

        for jour in range(1, main.nb_jours + 1):
            routes_du_jour = [r for r in self.routes_model.values() if r["jour"] == jour] #on filtre routes_model pour ne garder que les tournées de ce jour précis
            if not routes_du_jour:
                continue #si aucune tournée ce jour-là (aucun client à livrer), on n'affiche même pas le panneau, pour ne pas polluer l'écran
                
            panel_jour = CollapsiblePanel(f"Jour {jour} ({len(routes_du_jour)} tournées)", start_open=(jour==1)) #seul le jour 1 est déplié par défaut, pour que l'écran ne soit pas noyé au démarrage

            for r_data in routes_du_jour:
                card = RouteCard(r_data)
                card.on_visibility_toggled.connect(self._toggle_route_on_map) #quand on coche la case d'une carte, on prévient ManagerApp pour qu'il mette à jour la carte OSM

                card.on_details_requested.connect(self._open_route_details)  #quand on clique sur "Voir détails", on bascule vers la page détail
                
                self.route_cards_references[r_data["id"]] = card
                panel_jour.content_layout.addWidget(card)
                
            layout.addWidget(panel_jour)
            
        layout.addStretch() #évite que les panneaux s'étirent pour remplir tout l'espace vertical disponible
        scroll.setWidget(content)
        return scroll

    def _toggle_route_on_map(self, route_id, is_visible): #appelée à chaque fois qu'on coche/décoche une tournée, que ce soit depuis la liste ou depuis la page détail
        route_data = self.routes_model[route_id]
        route_data["visible"] = is_visible
        
        if route_id == self.active_route_id: #si la tournée qu'on vient de cocher est celle actuellement affichée en détail, on synchronise sa case à cocher aussi

            self.detail_map_checkbox.blockSignals(True)
            self.detail_map_checkbox.setChecked(is_visible)
            self.detail_map_checkbox.blockSignals(False)
            
        if route_id in self.route_cards_references: #et inversement, si l'action vient de la page détail, on synchronise la carte correspondante dans la liste

            self.route_cards_references[route_id].set_checkbox_state(is_visible)

        root_obj = self.quick_map.rootObject() #l'objet racine du QML, celui qui expose les fonctions toggleRoute()/centerOnStop() qu'on a définies dans QML_MAP_CODE
        if not root_obj: return  #sécurité : si la carte n'a pas fini de se charger, on ne fait rien plutôt que de planter

        if is_visible:
            #La route commence au Dépôt
            coords = [(DEPOT["lat"], DEPOT["lon"])]
            markers = []
            for i, order in enumerate(route_data["orders"]):
                coords.append((order["lat"], order["lon"]))
                markers.append({"lat": order["lat"], "lon": order["lon"], "label": str(i+1)})
            
            #La route se ferme en retournant au Dépôt
            coords.append((DEPOT["lat"], DEPOT["lon"]))
            
            path = fetch_road_route(coords) if len(coords) < 150 else [{"lat": lat, "lon": lon} for lat, lon in coords] #au-delà de 150 points l'API OSRM devient trop lente/risque de refuser la requête, on affiche alors des lignes droites plutôt que de bloquer l'appli
            root_obj.toggleRoute(route_data["id"], route_data["color"], path, markers, True)
        else:
            root_obj.toggleRoute(route_data["id"], "", [], [], False) #on rappelle la même fonction QML mais avec isVisible=False : c'est elle qui se charge de retirer le tracé et les marqueurs

    def _build_details_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {PANEL_BG};")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(10)

        btn_back = QPushButton("Retour au planning général")
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
        assignment_layout.addLayout(driver_row)
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
        self.truck_label.setText(f"Jour {route_data['jour']} — {route_data['label_display']}")
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
        
        #On affiche explicitement le Dépôt au début et à la fin du tableau de passage
        self.table.setRowCount(len(orders) + 2)
        
        #Ligne de départ (Dépôt)
        item_start_step = QTableWidgetItem("1")
        item_start_step.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(0, 0, item_start_step)
        self.table.setItem(0, 1, QTableWidgetItem("-"))
        self.table.setItem(0, 2, QTableWidgetItem(DEPOT["nom"]))
        self.table.setItem(0, 3, QTableWidgetItem("-"))
        self.table.setItem(0, 4, QTableWidgetItem("-"))
        
        # Clients intermédiaires
        for r_idx, order in enumerate(orders):
            row = r_idx + 1
            values = [str(row + 1), order["id"], order["adresse"], str(order["volume"]), order["date_limite"]]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col == 0: item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
            self.table.item(row, 0).setData(Qt.UserRole, order)
            
        # Ligne d'arrivée (Retour Dépôt)
        last_row = len(orders) + 1
        item_end_step = QTableWidgetItem(str(last_row + 1))
        item_end_step.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(last_row, 0, item_end_step)
        self.table.setItem(last_row, 1, QTableWidgetItem("-"))
        self.table.setItem(last_row, 2, QTableWidgetItem(DEPOT["nom"]))
        self.table.setItem(last_row, 3, QTableWidgetItem("-"))
        self.table.setItem(last_row, 4, QTableWidgetItem("-"))

        self.table.resizeRowsToContents()
        self.left_container.setCurrentIndex(1)

    def _on_driver_name_edited(self, new_text):
        if self.active_route_id and self.active_route_id in self.routes_model:
            self.routes_model[self.active_route_id]["driver"] = new_text
            if self.active_route_id in self.route_cards_references:
                self.route_cards_references[self.active_route_id].update_driver_name_display(new_text)

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
        item_step = self.table.item(row, 0)
        if not item_step: return
        
        order = item_step.data(Qt.UserRole)
        root_obj = self.quick_map.rootObject()
        if root_obj:
            if order:
                root_obj.centerOnStop(order["lat"], order["lon"])
            else:
                #Si pas d'order_data associé, c'est que l'utilisateur a cliqué sur le dépôt initial ou final
                root_obj.centerOnStop(DEPOT["lat"], DEPOT["lon"])

    def _setup_future_tab(self):
        layout = QVBoxLayout(self.tab_future)
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Registre Global des Commandes à Livrer (Moteur Angulaire)")
        title.setStyleSheet(f"font-weight: bold; color: {INK}; font-size: 14px; padding-bottom: 10px;")
        layout.addWidget(title)

        columns = ["ID Commande", "Adresse de livraison", "Volume Colis", "Échéance Planifiée"]
        table_future = QTableWidget(len(self.orders_db), len(columns))
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

        sorted_orders = sorted(self.orders_db.items(), key=lambda x: (x[1]['jour'], x[0]))
        for row, (c_id, data) in enumerate(sorted_orders):
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
