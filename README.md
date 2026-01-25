# apiMareeInfo

Intégration Home Assistant pour récupérer les informations de marée et de météo marine.

## Installation

1. Copiez le dossier `custom_components/apiMareeInfo` dans votre dossier `config/custom_components/`.
2. Redémarrez Home Assistant.

## Configuration

⚠️ **La configuration via le fichier `configuration.yaml` n'est plus supportée.** Tout se fait désormais via l'interface utilisateur.

1. Allez dans **Paramètres** -> **Appareils et services**.
2. Cliquez sur le bouton **Ajouter une intégration** en bas à droite.
3. Recherchez **apiMareeInfo**.
4. Remplissez le formulaire :
   - **Provider** : Choisissez votre source de données.
     - *Maree Info* : Utilise les données de Météo Consult (recommandé pour la France).
     - *Stormglass.io* : Couverture mondiale (nécessite une clé API).
   - **Latitude / Longitude** : Les coordonnées géographiques du port souhaité.
   - **Nom (Optionnel)** : Un nom personnalisé pour l'intégration.

Si vous choisissez **Stormglass.io**, une seconde étape vous demandera votre clé API.

## Capteurs (Sensors)

Cette intégration utilise les standards de nommage récents de Home Assistant. Un appareil (Device) est créé pour chaque port configuré (ex: `Maree Saint-Malo`), et les capteurs sont associés à cet appareil.

Voici les entités disponibles (exemple pour le port de Saint-Malo) :

| Entité | ID (exemple) | Description |
| :--- | :--- | :--- |
| **Marée** | `sensor.maree_saint_malo` | Capteur principal. L'état indique le statut actuel. Contient tous les détails en attributs. |
| **Prochaine Haute** | `sensor.maree_saint_malo_prochaine_haute` | Heure et hauteur de la prochaine marée haute. |
| **Prochaine Basse** | `sensor.maree_saint_malo_prochaine_basse` | Heure et hauteur de la prochaine marée basse. |
| **Température Eau** | `sensor.maree_saint_malo_temperature_eau` | Température de l'eau (si disponible). |

### Migration depuis une ancienne version

Si vous utilisiez une version précédente configurée en YAML :
1. Supprimez les lignes correspondantes dans votre `configuration.yaml`.
2. Redémarrez Home Assistant.
3. Ajoutez l'intégration via l'interface comme décrit ci-dessus.
4. Pensez à mettre à jour vos cartes Lovelace avec les nouveaux noms d'entités (les anciens noms du type `sensor.myport_...` ne sont plus utilisés par défaut).

## Crédits

Données fournies par Météo Consult ou Stormglass.io selon la configuration.

## Avertissement

Cette intégration est développée de manière indépendante et n'est affiliée ni à Météo Consult, ni à Stormglass.io.