import random
import numpy as np
from geopy.geocoders import Nominatim


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

'''print(infos)
print(demande)'''

#Générer graphe

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
'''infos, demande = lire_scenario("mines_tms_instances/A_D_E_4.txt")
nb_clients = infos[0]
coordonnees = generer_coordonnees(nb_clients)
print(coordonnees)'''

#Calcul de la distance entre 2 points 

def distance(a,b):
 x1 = a[0]
 y1 = a[1]
 x2 = b[0]
 y2 = b[1]

 d = np.sqrt((x1-x2)**2 + (y1-y2)**2)
 return d
 
'''a = coordonnees[0]
b = coordonnees[1]
print(distance(a,b))'''


#generation de coordonnées GPS autour de Paris

def generer_coordonnees_gps(nb_clients):    

    depot = (48.8566, 2.3522)  # Paris
    coordonnees = [depot]

    for _ in range(nb_clients):
        lat = depot[0] + random.uniform(-0.1, 0.1)
        lon = depot[1] + random.uniform(-0.1, 0.1)
        coordonnees.append((lat, lon))

    return coordonnees

#Test
'''nb_clients = infos[0]
print(generer_coordonnees_gps(nb_clients))'''


#generer adresses aleatoires puis conversion en coordonnées GPS

rues = [
    "Rue de Rivoli",
    "Rue Saint-Honoré",
    "Rue de Rennes",
    "Rue Mouffetard",
    "Rue Oberkampf",
    "Rue du Faubourg Saint-Honoré",
    "Rue du Faubourg Saint-Antoine",
    "Rue de Vaugirard",
    "Rue des Écoles",
    "Rue Soufflot",
    "Rue Monge",
    "Rue Gay-Lussac",
    "Rue Claude Bernard",
    "Rue Censier",
    "Rue Linné",
    "Rue Geoffroy-Saint-Hilaire",
    "Rue Buffon",
    "Rue d'Ulm",
    "Rue Saint-Jacques",
    "Rue des Martyrs",
    "Rue Lepic",
    "Rue Caulaincourt",
    "Rue Lamarck",
    "Rue Custine",
    "Rue Ordener",
    "Rue Championnet",
    "Rue Damrémont",
    "Rue des Abbesses",
    "Rue de Belleville",
    "Rue de Ménilmontant",
    "Rue des Pyrénées",
    "Rue de Bagnolet",
    "Rue de Charonne",
    "Rue de la Roquette",
    "Rue Keller",
    "Rue Sedaine",
    "Rue Amelot",
    "Rue de Turenne",
    "Rue Vieille-du-Temple",
    "Rue des Francs-Bourgeois",
    "Rue Beaubourg",
    "Rue Rambuteau",
    "Rue du Temple",
    "Rue Réaumur",
    "Rue Montorgueil",
    "Rue Étienne Marcel",
    "Rue du Louvre",
    "Rue Croix-des-Petits-Champs",
    "Rue de Richelieu",
    "Rue Vivienne",
    "Rue de la Paix",
    "Rue Royale",
    "Rue de Castiglione",
    "Rue Cambon",
    "Rue Tronchet",
    "Rue de Provence",
    "Rue La Fayette",
    "Rue du Faubourg Poissonnière",
    "Rue du Faubourg Montmartre",
    "Rue du Cardinal Lemoine",
    "Rue de Tolbiac",
    "Rue Nationale",
    "Rue de Patay",
    "Rue Jeanne d'Arc",
    "Rue Bobillot",
    "Rue des Peupliers",
    "Rue Brillat-Savarin",
    "Rue de la Glacière",
    "Rue d'Alésia",
    "Rue Didot",
    "Rue Raymond Losserand",
    "Rue du Chateau",
    "Rue Lecourbe",
    "Rue Cambronne",
    "Rue de Sèvres",
    "Rue de Babylone",
    "Rue du Bac",
    "Rue de Grenelle",
    "Rue Cler",
    "Rue Saint-Dominique",
    "Avenue des Champs-Élysées",
    "Avenue Montaigne",
    "Avenue Kléber",
    "Avenue Victor Hugo",
    "Avenue Foch",
    "Avenue de Wagram",
    "Avenue de Clichy",
    "Boulevard Saint-Germain",
    "Boulevard Saint-Michel",
    "Boulevard Haussmann",
    "Boulevard Voltaire",
    "Boulevard Richard-Lenoir",
    "Boulevard Beaumarchais",
    "Boulevard de Sébastopol",
    "Boulevard Magenta",
    "Boulevard Barbès",
    "Boulevard Ornano",
    "Place de la Bastille",
    "Place de la République",
    "Place de la Nation"
]
