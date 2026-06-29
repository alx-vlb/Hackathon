import classes
import donnees
import math
import numpy as np

infos, demande = donnees.lire_scenario("mines_tms_instances/A_D_E_0.txt")
nb_clients = infos[0]
nb_jours = infos[1]
nb_camions = infos[2]
volume_max_camion = infos[3]
coordonnées = donnees.generer_coordonnees(nb_clients, delta=20)

Clients = []

for i in range(nb_clients):
    d = []
    for j in range(nb_jours):
        d.append(demande[j][i])
    client = classes.Client(i, coordonnées[i], d)
    Clients.append(client)

def matrice_distance(coordonnées):
    n = len(coordonnées)
    matrice = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            x1, y1 = coordonnées[i]
            x2, y2 = coordonnées[j]
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            matrice[i][j] = round(distance,3)
    return matrice

def dist(clients): #clients est une liste d'élément de la classe Client
    n = len(clients)
    dist = 0
    for i in range(n-1):
        dist += matrice_distance(coordonnées)[clients[i].id_client][clients[i+1].id_client]
    dist += math.sqrt(clients[0].coordonnées[0]**2+clients[0].coordonnées[1]**2) #Distance au dépôt
    dist += math.sqrt(clients[n-1].coordonnées[0]**2+clients[n-1].coordonnées[1]**2) #Distance au dépôt
    return dist