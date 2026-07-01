class Camion:
    def __init__(self, id_camion, capacite_max):
        self.id_camion = id_camion      
        self.capacite_max = capacite_max
        self.marchandises = [] #Pour chaque jour, on ajoute la liste des identifiants des colis dans l'ordre ainsi que la capacité du camion

class Client:
    def __init__(self, id_client, coordonnées, demande):
        self.id_client = id_client 
        self.coordonnées = coordonnées
        self.demande = demande