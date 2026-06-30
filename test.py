from donnees import lire_scenario, generer_coordonnees
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
    plt.figure(figsize=(9, 9))

    # 1. Affichage des clients et centroïdes par zone
    for i, zone in enumerate(zones):
        centroide = zone[0]
        clients = zone[3]

        x = [p[0] for p in clients]
        y = [p[1] for p in clients]

        # Clients de la zone
        plt.scatter(x, y, label=f"Zone {i+1}", zorder=3)

        # Centroïde (croix noire)
        plt.scatter(centroide[0], centroide[1], marker="x", s=100, color="black", zorder=4)

    # Dépôt (carré rouge)
    plt.scatter(0, 0, marker="s", s=120, color="red", label="Dépôt", zorder=5)

    # 2. AJOUT : Dessin des trajets fléchés pour chaque camion
    for trajet in tous_les_trajets_coord:
        for k in range(len(trajet) - 1):
            pt_depart = trajet[k]
            pt_arrivee = trajet[k+1]
            
            # On dessine une flèche du point A vers le point B
            plt.annotate(
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

    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Subdivision de l'espace et Trajets Optimisés")
    plt.grid(True)
    plt.axis("equal")
    plt.legend()
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
        coordonnées = generer_coordonnees(nb_client, delta=20)
        mat = matrice_distance(coordonnées)
        cli_coord = coordonnées[1:]
        cli_poids = demande[0] #Demandes du premier jour
        zones = space_subdiv(cli_coord, P_max_camion, cli_poids, nb_camions)

        Clients = {}
        Clients[0] = classes.Client(0, (0,0), [])
        Clients[(0,0)] = classes.Client(0, (0,0), [])
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