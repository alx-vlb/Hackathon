**Groupe 12 - Hackathon Mines Paris - Optimisation d'un réseau de livraison de colis**

Le but du sujet est d'optimiser un réseau de livraison de colis, les simulations sont fondées sur des scénarios plus ou moins difficiles fournis par notre encadrant. Les colis sont dispatchés par zones, leur livraison est ordonnée pour minimiser la distance parcourue par les camions, puis on affiche les résultats sur une interface graphique.

**Manuel d'utilisation**

-Installer les bibliothèques que nous avons utilisées avec : 

```pip install -r requirements.txt```

Ensuite cela dépends de ce que vous voulez faire : 

-Pour observer la répartition des zones et le remplissage des camions sur un scénario précis il faut utiliser le code test.py directement dans le terminal avec : 

```python test.py mines_tms_instances\C_D_H_0.txt```  pour tester le scénario C_D_H_0 (plus la première lettre est grande plus le scénario est grand (beaucoup de clients et de jour), la seconde correspond à la difficulté (S = Simple, D = Difficile)).

-Pour afficher les trajectoires des camions dans Paris pour l'ensemble des jours, il suffit de run le fichier livreur_app_pyside avec : 

```python livreur_app_pyside.py```

On obtient un input dans lequel on renseigne le scénario que l'on veut (sans le .txt), par exemple :  B_S_E_0 
Les scénarios se trouvent dans le fichier mines_tms_instances fourni par notre encadrant. 

L'interface se lance, on peut choisir d'afficher ou pas les livraisons de chaque journée en cochant les cases en question. 
