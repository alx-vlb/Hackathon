import classes
import math
import numpy as np
import requests

epsilon = 0

def matrice_distance(listcord): #Une liste de coordonnées des clients
    n = len(listcord)
    matrice = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            x1, y1 = listcord[i]
            x2, y2 = listcord[j]
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            matrice[i,j] = round(distance,2)
    return matrice

def matrice_dist_reel(coords): #coords est une liste de tuple (longitude,latitude) des clients
    coord_str = ";".join(f"{lon},{lat}" for lon, lat in coords)
    url = f"http://router.project-osrm.org/table/v1/driving/{coord_str}?annotations=distance"
    try:
        resp = requests.get(url, timeout=4)
        data = resp.json()

        # Matrice des distances en mètres
        return data["distances"]
    except:
        print(f"Erreur OSRM")

def longueur(listcli,mat): #listcli est une liste d'identifiants des clients qui commence et se termine par 0
    n = len(listcli)
    dist = 0
    for i in range(n-1):
        dist += mat[listcli[i],listcli[i+1]]
    return dist

def opti_cli(clients, mat): #Une liste d'identifiants du groupe de client à optimiser qui commence et se termine par 0
    n = len(clients)
    clients_opti = list(clients) 
    changement = True
    while changement:
        changement = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                cout_actuel = mat[clients_opti[i-1], clients_opti[i]] + mat[clients_opti[j], clients_opti[j+1]]
                cout_futur = mat[clients_opti[i-1], clients_opti[j]] + mat[clients_opti[i], clients_opti[j+1]]
                if cout_futur + epsilon < cout_actuel:
                    # On inverse le segment entre i et j inclus
                    clients_opti[i:j+1] = reversed(clients_opti[i:j+1])
                    changement = True
    return clients_opti