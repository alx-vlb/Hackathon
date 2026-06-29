##Extraction des données du fichier txt

def lire_scenario(nom_fichier):
    with open(nom_fichier, "r") as f:
        lignes = [ligne.strip() for ligne in f if ligne.strip()]

    # Les 4 paramètres
    infos = [
        int(lignes[0].split()[1]),  # nb_clients
        int(lignes[1].split()[1]),  # nb_jours
        int(lignes[2].split()[1]),  # nb_camions
        int(lignes[3].split()[1])   # volume_max_camion
    ]

    # La matrice de demande quotidienne
    debut = lignes.index("demande_quotidienne") + 1

    demande = [
        [int(x) for x in ligne.split()]
        for ligne in lignes[debut:]
    ]

    return infos, demande

infos, demande = lire_scenario("mines_tms_instances/A_D_E_0.txt")

print(infos)
print(demande)

#Générer graphe

import random

def generer_coordonnees(nb_clients, delta=20):
    """
    Génère les coordonnées des clients.
    Le dépôt est en (0,0)
    Paramètres :
        nb_clients : nombre de clients
        delta : les coordonnées sont tirées entre -delta et +delta
    Retour :
        liste des coordonnées [(0,0), (x1,y1), ..., (xn,yn)]
    """
    coordonnees = [(0, 0)]  # dépôt

    for _ in range(nb_clients):
        x = random.randint(-delta, delta)
        y = random.randint(-delta, delta)
        coordonnees.append((x, y))

    return coordonnees

#Test
infos, demande = lire_scenario("mines_tms_instances/A_D_E_4.txt")
nb_clients = infos[0]
coordonnees = generer_coordonnees(nb_clients)
print(coordonnees)