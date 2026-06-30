from space_subdivision import space_subdiv
from opti import * 
from donnees import *

infos, demande = lire_scenario("mines_tms_instances/A_D_E_0.txt")
nb_client = infos[0]
nb_jours = infos[1]
li_client = generer_coordonnees(nb_client, delta=20 )[1:]
P_max_camion = infos[-1]


course = {}
for i in range(nb_jours):
    li_poids = demande[i]
    for j in range(len(space_subdiv(li_client, P_max_camion, li_poids))):
        coord_clients = space_subdiv(li_client, P_max_camion, li_poids)[j][3]
        id_clients = [k for k, v in Clients.items() if v in Clients]
        liste_opti_client = opti_cli(id_clients)
        course[i] = liste_opti_client

print(course)