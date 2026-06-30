from donnees import lire_scenario , generer_coordonnees
from space_subdivision import space_subdiv
import sys
import matplotlib.pyplot as plt

def afficher_zones(zones):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    remplissage = []
    couleurs = []
    for i, zone in enumerate(zones):
        centroide = zone[0]
        remplissage.append(zone[2])
        clients = zone[3]

        # coordonnées des clients
        x = [p[0] for p in clients]
        y = [p[1] for p in clients]

        # clients de la zone
        s = ax1.scatter(x, y, label=f"Zone {i+1}")
        couleurs.append(s.get_facecolor()[0]) 

        # centroïde (croix noire)
        ax1.scatter(centroide[0], centroide[1],
                    marker="x", s=100, color="black")
    print(remplissage)
    # dépôt
    ax1.scatter(0, 0, marker="s", s=120, color="red", label="Dépôt")

    ax1.set_xlabel("x")
    ax1.set_ylabel("y")
    ax1.set_title("Subdivision de l'espace")
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
        nb_camions = infos[2]
        P_max_camion = infos[-1]
        li_client = generer_coordonnees(nb_client, delta=20)[1:]
        li_poids = demande[0]
        zones = space_subdiv(li_client, P_max_camion, li_poids, nb_camions)
        afficher_zones(zones)