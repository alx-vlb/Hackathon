from donnees import lire_scenario, generer_coordonnees, generer_coordonnees_gps
from space_subdivision import space_subdiv  #Méthode de création de zones qui ne fonctionne pas sur certains cas limite et moins optimisée que la version angulaire 
from opti import matrice_distance, opti_cli
import sys
import matplotlib.pyplot as plt
import classes 
from angle_subdivision import angle_subdiv

def afficher_zones_et_trajets(zones, tous_les_trajets_coord, Clients):
    """
    Affiche les zones de clients ET dessine les trajets fléchés (sans centroïdes).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6)) #On voulait tracer les trajectoires à côté du remplissage des camions pour faire apparaitre les problèmes

    remplissage = []
    couleurs = [] #On va stocker les couleurs pour avoir une concordance entre les couleurs des trajectoires et le remplissage des camions associés
    
    for i, zone in enumerate(zones):
        id_clients = zone[0]
        remplissage.append(zone[1]) # Chargement du camion

        # Extraction des coordonnées des clients de la zone via le dictionnaire Clients
        x = [Clients[id_cli].coordonnées[0] for id_cli in id_clients]
        y = [Clients[id_cli].coordonnées[1] for id_cli in id_clients]

        # Affichage des clients de la zone
        s = ax1.scatter(x, y, label=f"Zone {i+1}", zorder=3)
        couleurs.append(s.get_facecolor()[0]) #on récupère la couleur de la trajectoire pour la suite

    # Dépôt central (carré rouge)
    ax1.scatter(Clients[0].coordonnées[0], Clients[0].coordonnées[1], marker="s", s=120, color="red", label="Dépôt", zorder=5) #l'indice 0 de client correspond au dépot

    # Dessin des trajets fléchés pour chaque camion
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

    # Affichage du remplissage des camions
    camions = [f"C{i+1}" for i in range(len(remplissage))]
    bars = ax2.bar(camions, remplissage, color=couleurs) # on conserve le code couleurs pour faciliter la compréhension. 

    ax2.set_xlabel("Camion")
    ax2.set_ylabel("Chargement")
    ax2.set_title("Chargement de chaque camion")
    ax2.grid(axis="y")

    # Valeurs au-dessus des barres
    for bar in bars:
        height = bar.get_height() # On récupère la taille des barres 
        ax2.text(
            bar.get_x() + bar.get_width() / 2,  # On place le remplissage du camion au dessus de la barre au milieu
            height,
            f"{height}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erreur : Tu as oublié d'indiquer le nom du fichier dans le terminal.") # Print dans le terminal pour aider à l'utilisation de notre programme
        print("Exemple : python test.py mon_fichier.txt")
    else:
        fichier_choisi = sys.argv[1]  # On utilise sys pour lire les paramètres fourni au terminal
        infos, demande = lire_scenario(fichier_choisi)
        nb_client = infos[0]
        nb_jours = infos[1]
        nb_camions = infos[2]
        P_max_camion = infos[3]
        coordonnées = generer_coordonnees(nb_client) # On place nos clients aléatoirement sur la grille de 40 par 40
        mat = matrice_distance(coordonnées)

        Clients = {}
        Clients[0] = classes.Client(0, (0, 0), 0) # on place le dépot (c'est le client de clé 0)
        #Clients[(48.8566, 2.3522)] = classes.Client(0, (48.8566, 2.3522), 0)
        for i in range(0, nb_client):
            d = demande[0][i]
            client = classes.Client(i+1, coordonnées[i+1], d)
            Clients[i+1] = client
            Clients[coordonnées[i+1]] = client

        zones, angle_final, non_livré = angle_subdiv([i for i in range(nb_client+1)], Clients, P_max_camion, nb_camions, 0) # on crée nos zones 
        print("L'angle sur lequel nous nous sommes arrêtés est " + str(angle_final)) # angle sur lequel on s'arrete 
        print("les clients non livrés ont pour indices " + str(non_livré))  #Indice des clients que nous n'avons pas livré qui seront livré en premier le lendemain 

        tous_les_trajets = []
        for zone in zones:
            trajet = [0] + zone[0] + [0]  # On impose au camion de partir et de revenir au dépot 
            trajet_opt = opti_cli(trajet, mat)
            
            # On récupère la liste des coordonnées correspondantes
            coord_opt = [Clients[id].coordonnées for id in trajet_opt]
            
            # On l'ajoute à notre grande liste de trajets
            tous_les_trajets.append(coord_opt)
            
        # On passe les zones ET les listes de coordonnées à la fonction graphique
        afficher_zones_et_trajets(zones, tous_les_trajets, Clients)