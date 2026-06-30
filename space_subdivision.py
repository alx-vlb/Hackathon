
from opti import matrice_distance
from donnees import lire_scenario, generer_coordonnees

def space_subdiv(li_clients, P_max_camion, li_poids, nb_camions):
    zones = [] 
    for i in range(len(li_clients)):
        zones.append([li_clients[i],1,li_poids[i],[li_clients[i]]]) 
    fusion_possible=True

    while fusion_possible and len(zones)>nb_camions:
        mat_dist = matrice_distance([z[0] for z in zones])
        li_dist=[]
        for i in range(len(zones)):
            for j in range (i+1, len(zones)):
                li_dist.append([mat_dist[i][j],i,j]) #on crée une liste des distances avec le numéro des zones reliées
        
        li_dist.sort(key=lambda x: x[0])
        fusion_found=False
        i=0
        while not fusion_found and i<len(li_dist):
            if zones[li_dist[i][1]][2]+zones[li_dist[i][2]][2]<=P_max_camion:
                fusion_found=True
                x = (zones[li_dist[i][1]][0][0]*zones[li_dist[i][1]][1] + zones[li_dist[i][2]][0][0]*zones[li_dist[i][2]][1]) / (zones[li_dist[i][1]][1]+zones[li_dist[i][2]][1])
                y = (zones[li_dist[i][1]][0][1]*zones[li_dist[i][1]][1] + zones[li_dist[i][2]][0][1]*zones[li_dist[i][2]][1]) / (zones[li_dist[i][1]][1]+zones[li_dist[i][2]][1])
                nv_centroide = (x, y)
                nv_zone=[nv_centroide, zones[li_dist[i][1]][1]+zones[li_dist[i][2]][1], zones[li_dist[i][1]][2]+zones[li_dist[i][2]][2], zones[li_dist[i][1]][3]+zones[li_dist[i][2]][3]]
                zones.pop(li_dist[i][2])
                zones.pop(li_dist[i][1])
                zones.append(nv_zone)
            else:
                i+=1
        if fusion_found==False:
            fusion_possible=False

    return zones    #zones est une liste de zones, chaque zone est une liste contenant le centroïde, le nombre de clients, le poids total et la liste des clients

            