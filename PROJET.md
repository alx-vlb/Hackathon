**Etapes de la reflexion :**

1/ Quadriller l'espace en petites zones puis dans chaque zone calculer la matrice de distance entre chaque client pour déterminer l'odre de livriaison.
2/ Faire plutôt comme un radar : le centre est le dépot et ensuite c'est une ligne qui tourne sur toute la zone et qui s'arrête quand le chargement est maximal. Si tous les colis n'ont pas pu être chargés la barre s'arrête est reprend là où elle s'est arrêtée le lendemain

**Affichage**

API/bibliothèèques utilisées
Récupération des données en coordonnées GPS.

**Difficultés rencontrées**

Conversion d'adresse en coordonnées GPS avec geopy car nous étions limité à une requête par seconde. Nous avons donc décidé que pour tester notre modèle nous genèrerions directement aléatoirement des coordonnées GPS proche de Paris.

**Notre organisation**

Nous avons découpé le problème en 3 parties : une partie acquisition des données, une partie optimisation une partie affichage. 
La partie acquisition des données s'occupe de faire le lien entre les deux parties, d'envoyer les données nécéssaires aux deux autre groupes sous le bon format, et de fusionner les codes ensuite.
La partie optimisation réfléchit au meilleur moyen de modéliser le problème, c'est à dire d'optimiser au mieux le temps de trajet, le coût en essence en maximisant le nombre de colis livrés par jour.
La partie affichage récupère la solution optimale et développe l'interface où on peut visualiser la course de chaque camion par jour, ainsi que l'odre de livraison dans chaque zone. 

**Ce que nous aurions pu faire avec plus de temps**
