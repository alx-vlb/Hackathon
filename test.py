from donnees import lire_scenario, generer_coordonnees, generer_coordonnees_gps
from space_subdivision import space_subdiv
from opti import matrice_distance, opti_cli
import sys
import matplotlib.pyplot as plt
import classes 

def afficher_zones_et_trajets(zones, tous_les_trajets_coord):
    """
    Affiche les zones de clients ET dessine les trajets fléchés.
    tous_les_trajets_coord : liste de listes de coordonnées [(x1,y1), (x2,y2), ...]
    """
    # 1. Affichage des clients et centroïdes par zone
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    remplissage = []
    couleurs = []
    for i, zone in enumerate(zones):
        centroide = zone[0]
        remplissage.append(zone[2])
        clients = zone[3]

        x = [p[0] for p in clients]
        y = [p[1] for p in clients]

        # Clients de la zone
        s = ax1.scatter(x, y, label=f"Zone {i+1}")
        couleurs.append(s.get_facecolor()[0]) 

        # Centroïde (croix noire)
        ax1.scatter(centroide[0], centroide[1], marker="x", s=100, color="black", zorder=4)

    # Dépôt (carré rouge)
    ax1.scatter(48.8566,2.3522 , marker="s", s=120, color="red", label="Dépôt", zorder=5)

    # 2. AJOUT : Dessin des trajets fléchés pour chaque camion
    for trajet in tous_les_trajets_coord:
        for k in range(len(trajet) - 1):
            pt_depart = trajet[k]
            pt_arrivee = trajet[k+1]
            
            # On dessine une flèche du point A vers le point B
            ax1.annotate(
                "", 
                xy=pt_arrivee,          # Pointe de la flèche
                xytext=pt_depart,       # Base de la flèche
                arrowprops=dict(
                    arrowstyle="->",    # Style de flèche simple
                    lw=1.5,             # Épaisseur de la ligne
                    color="gray",       # Couleur des flèches (tu peux la changer)
                    ls="--"             # Ligne en pointillés pour ne pas surcharger le graphe
                )
            )

    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_title("Subdivision de l'espace et Trajets Optimisés")
    ax1.grid(True)
    ax1.axis("equal")
    ax1.legend()

    camions = [f"C{i+1}" for i in range(len(remplissage))]

    bars = ax2.bar(camions, remplissage, color = couleurs)

    ax2.set_xlabel("Camion")
    ax2.set_ylabel("Chargement")
    ax2.set_title("Chargement de chaque camion")
    ax2.grid(axis="y")

    # valeurs au-dessus des barres
    for bar in bars:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("⚠️ Erreur : Tu as oublié d'indiquer le nom du fichier dans le terminal.")
        print("Exemple : python test.py mon_fichier.txt")
    else:
        fichier_choisi = sys.argv[1]
        infos, demande = lire_scenario(fichier_choisi)
        nb_client = infos[0]
        nb_jours = infos[1]
        nb_camions = infos[2]
        P_max_camion = infos[3]
        coordonnées = generer_coordonnees_gps(nb_client)
        mat = matrice_distance(coordonnées)
        cli_coord = coordonnées[1:]
        cli_poids = demande[0] #Demandes du premier jour
        zones = space_subdiv(cli_coord, P_max_camion, cli_poids, nb_camions)

        Clients = {}
        Clients[0] = classes.Client(0, (48.8566,2.3522), [])
        Clients[(48.8566,2.3522)] = classes.Client(0, (48.8566,2.3522), [])
        for i in range(0, nb_client):
            d = []
            for j in range(nb_jours):
                d.append(demande[j][i])
            client = classes.Client(i+1, coordonnées[i+1], d)
            Clients[i+1] = client
            Clients[coordonnées[i+1]] = client

        tous_les_trajets = []
        for zone in zones:
            coord_clients = zone[3]
            id_clients = [Clients[coord].id_client for coord in coord_clients]
            trajet = [0] + id_clients + [0]
            trajet_opt = opti_cli(trajet, mat)
            
            # On récupère la liste des coordonnées correspondantes
            coord_opt = [Clients[id].coordonnées for id in trajet_opt]
            
            # On l'ajoute à notre grande liste de trajets
            tous_les_trajets.append(coord_opt)
            
        # On passe les zones ET les listes de coordonnées à la fonction graphique
        afficher_zones_et_trajets(zones, tous_les_trajets)