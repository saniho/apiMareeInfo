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
  stormio_key: kdjsqhdksqhjk
```
Pour information, ce sensor est compatible avec la card

vous permetant d'obtenir ainsi ce genre de résultat :

<img src="https://github.com/saniho/apiMareeInfo/raw/master/img/imgCard.png" height="300"/>

Releases Notes :


v 1.1.0

cette nouvelle car necessite de s'inscrire sur le site de stormio( inscription gratuite )

https://stormglass.io/

v 1.0.1.1

ajout de nouvelles informations, vitesse du vent, temperature de l'eau, de l'air

v 1.0.1.0

Warning : changement service, dans le sensor il faut ajouter maintenant les coordonnées GPS du port