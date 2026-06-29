"""
Application livreur - version intégralement Python (Tkinter)
--------------------------------------------------------------
Pas de serveur web, pas de HTML/CSS/JS : tout est dans ce seul fichier.

Dépendances à installer :
    pip install tkintermapview

Sous Linux, il faut aussi le paquet système tkinter (déjà inclus dans
l'installeur officiel Python sous Windows/macOS) :
    sudo apt-get install python3-tk

Lancement :
    python livreur_app_tkinter.py
"""

import tkinter as tk
from tkinter import ttk
import tkintermapview


# ---------------------------------------------------------------------------
# 1) "Base de données" des commandes (à remplacer par une vraie requête SQL)
# ---------------------------------------------------------------------------

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

# Ordre de tournée déjà optimisé en temps (sortie du moteur d'optimisation)
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


# ---------------------------------------------------------------------------
# 2) Couleurs / style (inspiré du dashboard de référence)
# ---------------------------------------------------------------------------

BLUE = "#2563eb"
BLUE_DARK = "#1d4ed8"
BLUE_PALE = "#eaf1fd"
INK = "#1f2533"
INK_SOFT = "#5b6472"
LINE = "#e3e7ee"
BG = "#f5f7fa"
PANEL_BG = "#ffffff"


class CollapsiblePanel(tk.Frame):
    """Un panneau avec un titre cliquable qui replie/déplie son contenu,
    pour reproduire les menus déroulants demandés dans l'interface."""

    def __init__(self, parent, title, start_open=True, **kwargs):
        super().__init__(parent, bg=PANEL_BG, highlightbackground=LINE,
                          highlightthickness=1, **kwargs)

        self.is_open = start_open

        self.header = tk.Frame(self, bg=PANEL_BG, cursor="hand2")
        self.header.pack(fill="x")

        self.title_label = tk.Label(
            self.header, text=title, bg=PANEL_BG, fg=INK,
            font=("Segoe UI", 10, "bold"), anchor="w", padx=12, pady=10,
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        self.arrow_label = tk.Label(
            self.header, text="▾" if start_open else "▸",
            bg=PANEL_BG, fg=INK_SOFT, font=("Segoe UI", 9), padx=12,
        )
        self.arrow_label.pack(side="right")

        self.body = tk.Frame(self, bg=PANEL_BG)
        if start_open:
            self.body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        for widget in (self.header, self.title_label, self.arrow_label):
            widget.bind("<Button-1>", self.toggle)

    def toggle(self, event=None):
        if self.is_open:
            self.body.pack_forget()
            self.arrow_label.config(text="▸")
        else:
            self.body.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            self.arrow_label.config(text="▾")
        self.is_open = not self.is_open


class LivreurApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Ma Tournée — Livreur")
        self.geometry("1280x760")
        self.configure(bg=BG)

        self.markers = {}
        self.route_path = None

        self._build_topbar()
        self._build_layout()
        self._load_data()

    # ---------------------------------------------------------- topbar ----

    def _build_topbar(self):
        topbar = tk.Frame(self, bg=PANEL_BG, height=52,
                           highlightbackground=LINE, highlightthickness=1)
        topbar.pack(fill="x", side="top")

        left = tk.Frame(topbar, bg=PANEL_BG)
        left.pack(side="left", padx=18, pady=10)

        tk.Label(left, text="📦 Ma Tournée", bg=PANEL_BG, fg=BLUE_DARK,
                 font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(left, text="   Livreur  ›  Tournée du jour", bg=PANEL_BG,
                 fg=INK_SOFT, font=("Segoe UI", 9)).pack(side="left")

        right = tk.Frame(topbar, bg=PANEL_BG)
        right.pack(side="right", padx=18, pady=10)
        tk.Label(right, text="Aymen B. — Tournée Paris 13", bg=BLUE_PALE,
                 fg=BLUE_DARK, font=("Segoe UI", 9, "bold"),
                 padx=10, pady=3).pack()

    # ---------------------------------------------------------- layout ----

    def _build_layout(self):
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        # ---- Sidebar ----
        sidebar = tk.Frame(container, bg=BG, width=360)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)
        sidebar.pack_propagate(False)

        self.panel_summary = CollapsiblePanel(sidebar, "Résumé de la tournée")
        self.panel_summary.pack(fill="x", pady=(0, 10))
        self._build_summary(self.panel_summary.body)

        self.panel_orders = CollapsiblePanel(sidebar, "Livraisons")
        self.panel_orders.pack(fill="both", expand=True, pady=(0, 10))
        self._build_orders_table(self.panel_orders.body)

        self.panel_legend = CollapsiblePanel(sidebar, "Légende", start_open=False)
        self.panel_legend.pack(fill="x")
        self._build_legend(self.panel_legend.body)

        # ---- Carte ----
        map_frame = tk.Frame(container, bg=BG)
        map_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        self.map_widget = tkintermapview.TkinterMapView(
            map_frame, width=800, height=700, corner_radius=8
        )
        self.map_widget.pack(fill="both", expand=True)
        self.map_widget.set_tile_server(
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
        )

    # --------------------------------------------------------- summary ----

    def _build_summary(self, parent):
        grid = tk.Frame(parent, bg=PANEL_BG)
        grid.pack(fill="x")

        self.summary_vars = {}
        items = [
            ("temps", "Temps estimé"),
            ("stops", "Stops"),
            ("volume", "Volume total"),
            ("distance", "Distance"),
        ]
        for i, (key, label) in enumerate(items):
            cell = tk.Frame(grid, bg=BLUE_PALE)
            cell.grid(row=i // 2, column=i % 2, sticky="nsew", padx=4, pady=4)
            grid.grid_columnconfigure(i % 2, weight=1)

            value_lbl = tk.Label(cell, text="—", bg=BLUE_PALE, fg=BLUE_DARK,
                                  font=("Segoe UI", 13, "bold"), anchor="w")
            value_lbl.pack(fill="x", padx=10, pady=(8, 0))
            tk.Label(cell, text=label, bg=BLUE_PALE, fg=INK_SOFT,
                     font=("Segoe UI", 8), anchor="w").pack(fill="x", padx=10, pady=(0, 8))

            self.summary_vars[key] = value_lbl

        self.depart_label = tk.Label(
            parent, text="", bg=PANEL_BG, fg=INK_SOFT,
            font=("Segoe UI", 9), anchor="w", justify="left", wraplength=300,
        )
        self.depart_label.pack(fill="x", pady=(8, 0))

    # ----------------------------------------------------------- table ----

    def _build_orders_table(self, parent):
        columns = ("ordre", "numero", "adresse", "volume", "commande", "limite")
        headers = {
            "ordre": "#", "numero": "N° commande", "adresse": "Adresse",
            "volume": "Vol.", "commande": "Commandée le", "limite": "Livraison prévue",
        }
        widths = {"ordre": 25, "numero": 95, "adresse": 160,
                  "volume": 40, "commande": 80, "limite": 90}

        style = ttk.Style(self)
        style.configure("Orders.Treeview", rowheight=24, font=("Segoe UI", 8))
        style.configure("Orders.Treeview.Heading", font=("Segoe UI", 8, "bold"))

        self.tree = ttk.Treeview(
            parent, columns=columns, show="headings",
            style="Orders.Treeview", height=12,
        )
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="w")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_row_selected)

    # ----------------------------------------------------------- legend ----

    def _build_legend(self, parent):
        rows = [
            ("⚫", "Dépôt de départ"),
            ("🔵", "Arrêt de livraison"),
            ("—", "Itinéraire optimisé (ligne bleue)"),
        ]
        for icon, text in rows:
            row = tk.Frame(parent, bg=PANEL_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=icon, bg=PANEL_BG, fg=BLUE, font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
            tk.Label(row, text=text, bg=PANEL_BG, fg=INK_SOFT, font=("Segoe UI", 9)).pack(side="left")

    # ------------------------------------------------------------ data ----

    def _load_data(self):
        # Résumé
        info = ROUTE_INFO
        h, m = divmod(info["temps_trajet_min"], 60)
        self.summary_vars["temps"].config(text=f"{h}h{m:02d}")
        self.summary_vars["stops"].config(text=str(info["nb_stops"]))
        self.summary_vars["volume"].config(text=str(info["volume_total"]))
        self.summary_vars["distance"].config(text=f"{info['distance_km']} km")
        self.depart_label.config(
            text=f"Départ prévu à {info['heure_depart']} depuis {DEPOT['nom']}"
        )

        # Table + carte
        path_coords = [(DEPOT["lat"], DEPOT["lon"])]

        for i, order_number in enumerate(OPTIMIZED_ROUTE, start=1):
            d = ORDERS_DB[order_number]
            self.tree.insert("", "end", iid=order_number, values=(
                i, order_number, d["adresse"], d["volume"],
                d["date_commande"], d["date_limite"],
            ))
            path_coords.append((d["lat"], d["lon"]))

            marker = self.map_widget.set_marker(
                d["lat"], d["lon"], text=str(i),
                marker_color_circle=BLUE_DARK, marker_color_outside=BLUE,
            )
            self.markers[order_number] = marker

        # Marqueur du dépôt
        self.map_widget.set_marker(
            DEPOT["lat"], DEPOT["lon"], text="Dépôt",
            marker_color_circle=INK, marker_color_outside=INK_SOFT,
        )

        # Tracé de l'itinéraire
        self.map_widget.set_path(path_coords, color=BLUE, width=4)

        # Centrage sur le dépôt avec un zoom raisonnable
        self.map_widget.set_position(DEPOT["lat"], DEPOT["lon"])
        self.map_widget.set_zoom(13)

    # ----------------------------------------------------- interaction ----

    def _on_row_selected(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        order_number = selection[0]
        data = ORDERS_DB[order_number]
        self.map_widget.set_position(data["lat"], data["lon"])
        self.map_widget.set_zoom(15)


if __name__ == "__main__":
    app = LivreurApp()
    app.mainloop()
