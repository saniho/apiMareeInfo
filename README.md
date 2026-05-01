# apiMareeInfo

Intégration Home Assistant pour récupérer les informations de marée et de météo marine.

## Version actuelle
**v2.0.0** - Refonte majeure avec support météo complet

## 📝 Changelog

### v2.0.0
- 🚀 **Entité Weather** : Ajout d'une plateforme météo complète (`weather`) native pour Home Assistant.
- 🎨 **Compatibilité Carte Météo-France** : Capteurs harmonisés pour fonctionner avec la carte Lovelace personnalisée Météo-France.
- 📈 **Prévisions de pluie** : Support de la pluie dans l'heure avec graphique et détection de la prochaine pluie.
- 🌬️ **Pression atmosphérique** : Ajout d'un capteur de pression et de ses prévisions (hPa). Compatible avec la carte [content-card-pressure-forecast](https://github.com/saniho/content-card-pressure-forecast).
- 🌓 **Gestion Jour/Nuit** : Icônes dynamiques basées sur la position du soleil (`sun.sun`).
- ⚡ **Rafraîchissement optimisé** : Passage à un intervalle de mise à jour de 15 minutes pour plus de précision sur les prévisions.
- 🛠️ **Refonte technique** : Migration vers des dictionnaires standards pour les attributs et nettoyage complet du code.

### v1.5.2
- ✅ **Correction de l'erreur 403** : Résolution des problèmes de requête à l'API MeteoMarine
- ✅ **Headers HTTP optimisés** : Ajout des headers de sécurité (sec-*) et User-Agent Chrome à jour
- ✅ **Gestion SSL améliorée** : Support SSL désactivé pour plus de compatibilité
- ✅ **Support async/await** : Gestion correcte des coroutines asyncio pour les tests

### Versions antérieures
Consultez l'historique git pour les détails des versions précédentes.

## Installation

1. Copiez le dossier `custom_components/apiMareeInfo` dans votre dossier `config/custom_components/`.
2. Redémarrez Home Assistant.

## Configuration

⚠️ **La configuration via le fichier `configuration.yaml` n'est plus supportée.** Tout se fait désormais via l'interface utilisateur.

1. Allez dans **Paramètres** -> **Appareils et services**.
2. Cliquez sur le bouton **Ajouter une intégration** en bas à droite.
3. Recherchez et sélectionnez **apiMareeInfo**.
4. **Étape 1 : Recherche** - Entrez le nom de la ville ou du port que vous souhaitez suivre (ex: "Saint-Malo").
5. **Étape 2 : Sélection** - Choisissez le port exact dans la liste déroulante qui s'affiche, puis validez.

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

Données fournies par Météo Consult.

## Avertissement

Cette intégration est développée de manière indépendante et n'est affiliée ni à Météo Consult.
