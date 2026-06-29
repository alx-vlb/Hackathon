On a une liste de points (li_clients) gps ave un indice le client_id
Grâce au client_id on peut trouver la colonne du client dasn la matrice des commandes
on utilise alors li_poids qui est indexé comme li_clients mais avec ici le poids de la commande de chaque client

On va diviser l'espace en zones géographiques où un seul camion pourra faire toute la distribution

On crée N zones pour N clients
1 zone est définie par un centroide, un nombre de client, un poids total, et les coordonnées de chaque client

Tant qu'il y a une fusion possible
    On calcule la matrice de distance 
    on trie la liste des distances entre 2 points par ordre croissant'
    
    Tant qu'on a pas trouvé de fusion on prend la distance la plus petite entre 2 points
        on regarde si le poids cumulés de ces 2 zones est tjr < au poids max d'un camion
        si c'est le cas on fusionne et on modifie la liste zone et on repart au calcule  de la matrice des distances
        si ce n'est pas le cas on passe au couple de points suivant 
    si on a testé toutes les fusions et que aucune n'est possible alors on sort et c'est fini

