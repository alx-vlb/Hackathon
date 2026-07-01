from donnees import lire_scenario, generer_coordonnees, generer_coordonnees_gps
from space_subdivision import space_subdiv
from opti import matrice_distance, opti_cli
import sys
import matplotlib.pyplot as plt
import classes 
from angle_subdivision import angle_subdiv

def afficher_zones_et_trajets(zones, tous_les_trajets_coord, Clients):
    """
    Affiche les zones de clients ET dessine les trajets fléchés (sans centroïdes).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    remplissage = []
    couleurs = []
    
    for i, zone in enumerate(zones):
        id_clients = zone[0]
        remplissage.append(zone[1]) # Chargement du camion

        # Extraction des coordonnées des clients de la zone via le dictionnaire Clients
        x = [Clients[id_cli].coordonnées[0] for id_cli in id_clients]
        y = [Clients[id_cli].coordonnées[1] for id_cli in id_clients]

        # Affichage des clients de la zone
        s = ax1.scatter(x, y, label=f"Zone {i+1}", zorder=3)
        couleurs.append(s.get_facecolor()[0]) 

    # Dépôt central (carré rouge)
    ax1.scatter(0, 0, marker="s", s=120, color="red", label="Dépôt", zorder=5)

    # 2. Dessin des trajets fléchés pour chaque camion
    for trajet in tous_les_trajets_coord:
        for k in range(len(trajet) - 1):
            pt_depart = trajet[k]
            pt_arrivee = trajet[k+1]
            
            ax1.annotate(
                "", 
                xy=pt_arrivee,          
                xytext=pt_depart,       
                arrowprops=dict(
                    arrowstyle="->",    
                    lw=1.5,             
                    color="gray",       
                    ls="--"             
                )
            )

    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_title("Subdivision angulaire et Trajets Optimisés")
    ax1.grid(True)
    ax1.axis("equal")
    ax1.legend()

    # 3. Graphique à barres pour le chargement
    camions = [f"C{i+1}" for i in range(len(remplissage))]
    bars = ax2.bar(camions, remplissage, color=couleurs)

    ax2.set_xlabel("Camion")
    ax2.set_ylabel("Chargement")
    ax2.set_title("Chargement de chaque camion")
    ax2.grid(axis="y")

    # Valeurs au-dessus des barres
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
        coordonnées = generer_coordonnees(nb_client)
        mat = matrice_distance(coordonnées)

        Clients = {}
        Clients[0] = classes.Client(0, (0,0), 0)
        Clients[(0,0)] = classes.Client(0, (0,0), 0)
        for i in range(0, nb_client):
            d = demande[0][i]
            client = classes.Client(i+1, coordonnées[i+1], d)
            Clients[i+1] = client
            Clients[coordonnées[i+1]] = client

        zones, angle_final, non_livré = angle_subdiv([i for i in range(nb_client+1)], Clients, P_max_camion, nb_camions, 0)
        print(angle_final)
        print(non_livré)

        tous_les_trajets = []
        for zone in zones:
            trajet = [0] + zone[0] + [0]
            trajet_opt = opti_cli(trajet, mat)
            
            # On récupère la liste des coordonnées correspondantes
            coord_opt = [Clients[id].coordonnées for id in trajet_opt]
            
            # On l'ajoute à notre grande liste de trajets
            tous_les_trajets.append(coord_opt)
            
        # On passe les zones ET les listes de coordonnées à la fonction graphique
        afficher_zones_et_trajets(zones, tous_les_trajets, Clients)