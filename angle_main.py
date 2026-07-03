from opti import matrice_distance, opti_cli
from donnees import lire_scenario, generer_coordonnees
from angle_subdivision import angle_subdiv
import classes

# Lecture du scénario
infos, demande = lire_scenario("mines_tms_instances/C_D_H_3.txt")

nb_client = infos[0]
nb_jours = infos[1]
nb_camions = infos[2]
P_max_camion = infos[3]

# Génération des coordonnées (index 0 = dépôt, 1..N = clients)
coordonnees = generer_coordonnees(nb_client)

# Matrice de distance globale sur toutes les coordonnées
mat = matrice_distance(coordonnees)

#On crée les clients et on les stocke dans un dictionnaire pour un accès rapide par id ou par coordonnées
Clients = {}
Clients[0] = classes.Client(0, (0,0), [0]*nb_jours)
Clients[(0,0)] = Clients[0]

for i in range(0, nb_client):
    d = [demande[j][i] for j in range(nb_jours)]
    client = classes.Client(i+1, coordonnees[i+1], d)
    Clients[i+1] = client
    Clients[coordonnees[i+1]] = client

course = {}
angle_depart = 0

# Boucle sur les jours pour à la fin proposer un plan de livraison pour chaque jour avec gestion de l'ajout au jour suivant si nécessaire
for jour in range(nb_jours):

    li_clients = []
    # On crée la liste des clients pour le jour courant
    for i in range(nb_client):
        li_clients.append(classes.Client(i+1, coordonnees[i + 1], demande[jour][i]))

    # On appelle la fonction angle_subdiv pour obtenir les zones de livraison, l'angle de départ pour le prochain jour et les clients non livrés
    zones, angle_depart, no_delivered = angle_subdiv(list(range(nb_client)), li_clients, P_max_camion, nb_camions, angle_depart)
    course[jour + 1] = []

    # On parcourt les zones pour créer les trajets optimisés pour chaque zone   
    for zone in zones:
        # zone[0] = liste des indices clients (0..N-1)
        if not zone[0]:  # zone vide, pas de camion affecté
            continue
        id_clients = [c + 1 for c in zone[0]]  # +1 car dépôt = index 0 dans mat
        trajet = [0] + id_clients + [0]
        trajet_opt = opti_cli(trajet, mat)
        course[jour + 1].append(trajet_opt)

    # Reporter les non-livrés au jour suivant (sauf dernier jour)
    if jour + 1 < nb_jours:
        for client_id in no_delivered:
            demande[jour + 1][client_id] += demande[jour][client_id]

print(course)
