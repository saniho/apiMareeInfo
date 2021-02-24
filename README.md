# apimareeInfo

Objectif, recuperer le contenu les informations de marée, exemple ici le port de SGXV( Saint Gilles Croix de Vie ).

pour declarer le sensor dans HA : 
un code pour le port, et ces coordonnées GPS

```yaml
- platform: apiMareeInfo
  code: 124
  latitude: 46.7711
  longitude: -2.05306
  scan_interval: 120
```
Pour information, ce sensor est compatible avec la card

vous permetant d'obetnir ainsi ce genre de résultat :


<img src="https://raw.githubusercontent.com/saniho/apimareeInfo/main/img/imgCard.png" height="300"/>

Releases Notes :

v 1.0.1.1

ajout de nouvelles informations, vitesse du vent, temperature de l'eau, de l'air

v 1.0.1.0

Warning : changement service, dans le sensor il faut ajouter maintenant les coordonnées GPS du port