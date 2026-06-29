On a une liste de points gps ave un indice le client_id
Grâce au client_id on peut trouver la colonne du client dasn la matrice des commandes
et alors on peuttoruver le nombre de colis par client pr chaque jour


On va choisir un poids par région P_max_i
on va diviser en très petites zones géographiques un grand espace e
On va tout mettre dans une liste de régions qui sont encore à fusionner 
pour chacune de ces régions on calcule le poids totale dans la région
s'il y'a déjà des P_i>P_max_i, on divise par 2 la surface des régions...

Donc là on a une liste de régions avec P_i<P_max_i

#Il faut avoir une matrice de distance d'un clients à l'autre et avoir une fonction(n)
qui donne la liste de n voisins

Ensuite on teste la fusion avec les n voisins et dès qu'il y a une fusion qui donne un nouveau P_i<P_max_i
