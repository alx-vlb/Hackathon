from donnees import lire_scenario , generer_coordonnees
from space_subdivision import space_subdiv



infos, demande = lire_scenario("mines_tms_instances/A_D_E_0.txt")
nb_client = infos[0]
li_client = generer_coordonnees(nb_client, delta=20 )[1:]
P_max_camion = infos[-1]
li_poids = demande[0]

print(space_subdiv(li_client, P_max_camion, li_poids))

#affichage
'''import matplotlib.pyplot as plt

def afficher_zones(zones):
    plt.figure(figsize=(8, 8))

    for i, zone in enumerate(zones):
        centroide = zone[0]
        clients = zone[3]

        # coordonnées des clients
        x = [p[0] for p in clients]
        y = [p[1] for p in clients]

        # clients de la zone
        plt.scatter(x, y, label=f"Zone {i+1}")

        # centroïde (croix noire)
        plt.scatter(centroide[0], centroide[1],
                    marker="x", s=100, color="black")

    # dépôt
    plt.scatter(0, 0, marker="s", s=120, color="red", label="Dépôt")

    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Subdivision de l'espace")
    plt.grid(True)
    plt.axis("equal")
    plt.legend()
    plt.show()

zones = space_subdiv(li_client, P_max_camion, li_poids)
print(afficher_zones(zones))'''