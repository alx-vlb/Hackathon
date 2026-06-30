from space_subdivision import space_subdiv
from opti import * 
from donnees import *

infos, demande = lire_scenario("mines_tms_instances/A_D_E_0.txt")
nb_client = infos[0]
nb_jours = infos[1]
li_client = generer_coordonnees(nb_client, delta=20 )[1:]
P_max_camion = infos[-1]
li_poids = demande[0]

clients = {}
for i in range(len(li_client)):
    clients[i+1] = li_client[i]
print(clients)    