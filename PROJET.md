**Etapes de la reflexion :**

1/ Quadriller l'espace en autant de zones qu'il y a de camion puis dans chaque zone calculer l'ordre de livraison qui minimise la distance total parcourue par le camion.
2/ Faire plutôt comme un radar : le centre est le dépot et ensuite c'est une ligne qui tourne sur toute la zone et qui s'arrête quand le chargement est maximal. Si tous les colis n'ont pas pu être chargés la barre s'arrête est reprend là où elle s'est arrêtée le lendemain

**Affichage**

API/bibliothèques utilisées : 
-PySide6 pour l'interface graphique (faire des widgets en Python)
-OSRM (Open Source Routing Machine) est une API qui permet de gérer de nombreuses choses sur les cartes. On lui donne deux points, puis elle nous renvoie plein d'autres points qui suivent la route entre nos deux points initiaux pour avoir un parcours réaliste. L'API nous permet aussi d'obtenir la matrice des distances entre l'ensemble des clients en se déplaçant en voiture et en suivant les routes. 
-Colorsys qui nous permet de convertir des couleurs HSV (Hue Saturation Value), plus pratique pour générer des couleurs différentes en RGB pour l'affichage. 

Récupération des données en coordonnées GPS : 
Pour ce faire, on place aléatoirement nos clients dans une grille classique de 40 par 40 centrée en (0,0), le centre représente le dépôt. On fait le calcul des trajectoires les plus optimales, puis on translate les résultats sur Paris en plaçant le dépôt sur l'Hôtel de ville et en appliquant un facteur 0.06 aux coordonnées. 

**Difficultés rencontrées**

Conversion d'adresse en coordonnées GPS avec geopy car nous étions limité à une requête par seconde. Nous avons donc décidé que pour tester notre modèle nous genèrerions directement aléatoirement des coordonnées GPS proche de Paris.

**Notre organisation**

Nous avons découpé le problème en 3 parties : une partie acquisition des données, une partie optimisation une partie affichage. 
La partie acquisition des données s'occupe de faire le lien entre les deux parties, d'envoyer les données nécéssaires aux deux autre groupes sous le bon format, et de fusionner les codes ensuite.
La partie optimisation réfléchit au meilleur moyen de modéliser le problème, c'est à dire d'optimiser au mieux le temps de trajet, le coût en essence en maximisant le nombre de colis livrés par jour.
La partie affichage récupère la solution optimale et développe l'interface où on peut visualiser la course de chaque camion par jour, ainsi que l'odre de livraison dans chaque zone. 

**Ce que nous aurions pu faire avec plus de temps**
