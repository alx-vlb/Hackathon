from space_subdivision import space_subdiv
from opti import *
from donnees import *

# Lecture du scénario
infos, demande = lire_scenario("mines_tms_instances/A_D_E_0.txt")

nb_client = infos[0]
nb_jours = infos[1]
nb_camions = infos[2]
P_max_camion = infos[3]

# Génération des coordonnées 
li_client = coordonnées[1:]

course = {}

for jour in range(nb_jours):

    li_poids = demande[jour]
    zones = space_subdiv(li_client, P_max_camion, li_poids, nb_camions)
    course[jour + 1] = []

    for zone in zones:

        # Coordonnées des clients de la zone
        coord_clients = zone[3]

        # Conversion identifiants
        id_clients = [Clients[coord].id_client for coord in coord_clients]
        # Ajout du dépôt au début et à la fin
        trajet = [0] + id_clients + [0]

        # Optimisation de la tournée
        trajet_opt = opti_cli(trajet)
        course[jour + 1].append(trajet_opt)

print(course)
