from donnees import *
from opti import *
import classes
import math

def angle(x,y,angle_init): #Renvoie l'angle en coordonnées polaires par rapport à l'angle initial
    (x,y) = (x*math.cos(angle_init)+y*math.sin(angle_init),y*math.cos(angle_init)-x*math.sin(angle_init))
    if y>=0 :
        return math.acos(x/math.sqrt(x**2+y**2))
    else:
        return 2*math.pi-math.acos(x/math.sqrt(x**2+y**2))
    
def angle_subdiv(cli_id, Clients, P_max_camion, nb_camions, angle_init): #cli_id est une liste d'identifiants des clients
    coor_pol = [] #Une liste de couple (angle, identifiant) des clients
    zones = []
    for id in cli_id:
        (x,y) = Clients[id].coordonnées
        if (x,y) != (0,0) and Clients[id].demande > 0:
            coor_pol.append([angle(x,y,angle_init),id])
    coor_pol.sort(key=lambda x: x[0])
    cli_zone = []
    camion_act = 0 
    chargement = 0 #Chargement de la zone en cours
    nb_cli = 0 #Nombre de clients dans la zone en cours
    while camion_act < nb_camions:
        if coor_pol != [] and chargement + Clients[coor_pol[0][1]].demande < P_max_camion:
            cli_zone.append(coor_pol[0][1])
            chargement += Clients[coor_pol[0][1]].demande
            nb_cli += 1
            del coor_pol[0]
        else:
            zones.append([cli_zone,chargement,nb_cli])
            cli_zone = []
            chargement = 0
            nb_cli = 0
            camion_act +=1
    non_livré = []
    if coor_pol == []:
        angle_final = 0
    else:
        angle_final = coor_pol[0][0]
        for i in range(len(coor_pol)):
            non_livré.append(coor_pol[i][1])
    return zones, angle_final, non_livré 

#zones est une liste de zone qui contiennent la liste des identifiants des points, le chargement du camion et le nombre total de clients
#non_livré est une liste qui contient les identifiants des points non livrés