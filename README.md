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


v 1.0.1.0

Warning : changement service, dans le sensor il faut ajouter maintenant les coordonnées GPS du port