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



Detail des attributs 


```
Attributs
Version 1.1.1 ==> version de l'applciation
Horaire 0 3 ==> horaire de la 3ème marée du jour courant
Coeff 0 3 => coéfficient de la 3ème marée du jour courant
Etat 0 3 ==> BM/PM de la 3ème marée du jour courant
Hauteur 0 3 ==> Hauteur de la 3ème marée du jour courant
Horaire 1 3 ==> horaire de la 3ème marée du jour suivant
Nb maree 3 ==> nombre de marée du jour J + 4
etc...
```
```
NomPort ==> nom du port utilisé
Copyright ==> données fournies par SHOM
DateCourante ==> date courante zéro
TimeLastCall ==> dernier mis à jour
Prevision
- datetime: '2022-12-17T22:00:00+01:00' ==> prevision à 22 le 17/12
forcevnds: 8 ==> force du vent en noeuds
rafvnds: 12 ==> rafale de vent
dirvdegres: 105 ==> direction du vents
dateComplete: '2022-12-17T22:00:00'
nuagecouverture: 5 ==> couverture nuageuses 
precipitation: 0 ==> precipitation prévue en mm
teau: 9 ==> températeur de l'eau
t: -3 ==> température de l'air
risqueorage: 0 ==> risque d'orage
dirhouledegres: 195 ==> direction de la houle
hauteurhoule: 0.4 ==> hauteur de la houle
periodehoule: 9 ==> frequence de la houle 
hauteurmerv: 0.1 ==> hauteur de la merc
periodemerv: 1 ==> periode
hauteurvague: 0.5 ==> hauteur max de la vague
etc ...
```

```
Message ==> message résumé de la prochaine marée
Last update ==> derniere mise à jour
Last http update ==> derniere mise à jour de données fournies par le provider
```