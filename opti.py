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
epsilon = 0.1

Clients = {}
Clients[0] = classes.Client(0, (0,0), []) #Dépôt

for i in range(0, nb_clients):
    d = []
    for j in range(nb_jours):
        d.append(demande[j][i])
    client = classes.Client(i+1, coordonnées[i+1], d)
    Clients[i+1] = client

def matrice_distance():
    n = nb_clients + 1
    matrice = np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            x1, y1 = Clients[i].coordonnées
            x2, y2 = Clients[j].coordonnées
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            matrice[i,j] = round(distance,2)
    return matrice

mat = matrice_distance()

def longueur(listcli): #listcli est une liste d'identifiants des points à parcourir qui commence et se termine par 0
    n = len(listcli)
    dist = 0
    for i in range(n-1):
        dist += mat[listcli[i],listcli[i+1]]
    return dist

print(longueur([0,1,2,3,4,5,6,7,8,9,10,0]))

def opti_cli(clients): 
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

cli_opti = opti_cli([0,1,2,3,4,5,6,7,8,9,10,0])

print(cli_opti)
print(longueur(cli_opti))