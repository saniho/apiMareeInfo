# apiMareeInfo

Intégration Home Assistant pour récupérer les informations de marée et de météo marine.

## Version actuelle
**v2.1.7-beta1** - CI/CD complet

## 📝 Changelog

### v2.1.7-beta1
- 🔧 **CI/CD complet** : Pipeline unifié avec lint (ruff), typecheck (mypy), tests (pytest + coverage), CodeQL et HACS validation (issue #57).
- 🧹 **Nettoyage** : Suppression des workflows obsolètes remplacés par un seul `ci.yml`.
- 🗑️ **Fichiers legacy supprimés** : `testMareeInfo.py` et `test_search.py`.

### v2.1.6
- 🌊 **Nouveau capteur** : `sensor.prochaine_grande_maree` — affiche la date/heure de la prochaine grande marée (coefficient >= 100) avec les attributs `coefficient`, `type`, `hauteur`, `delai`, `horaire` (issue #47).
- 📊 **Prévisions étendues** : Les données MeteoConsult sont maintenant exploitées sur 15 jours au lieu de 6, permettant de détecter les grandes marées à venir.
- ⚠️ **Comportement morte-eau** : Le capteur affiche `unavailable` en période de morte-eau (aucun coefficient >= 100 dans les 15 jours). C'est normal : les grandes marées ne surviennent que lors des périodes d'équinoxe (2-4 fois par mois).

### v2.1.5
- 🏷️ **Constantes centralisées** : `DEFAULT_MAX_HOURS`, `DEFAULT_SCAN_INTERVAL`, `CONF_STORM_KEY` déplacés dans `const.py` (issue #55).
- 🔤 **Nommage FR→EN** : Les méthodes publiques de `ApiMareeInfo` ont été renommées en anglais (`get_port_name()`, `get_tide_data()`, `has_error()`, etc.) (issue #55).
- 🔤 **Noms de classes PascalCase** : `manageSensorState` → `SensorStateManager` (issue #55).
- 🔤 **Variables snake_case** : `_sAM` → `_sensor_manager` dans `sensor.py` (issue #55).

### v2.1.4
- 🏷️ **Typage complet** : Ajout de TypedDict pour les structures de données (`TideData`, `ForecastData`, `LiveForecastItemRaw`, etc.) avec hints sur tous les attributs et méthodes (issue #53).

### v2.1.2
- 🔧 **Refactor HTTP** : Extraction du helper HTTP partagé (`http_utils.py`) supprimant la duplication de code entre `ListePorts` et `MeteoMarine` (issue #48).
- ✅ **Tests unitaires** : Ajout d'une suite de tests complète avec pytest + couverture.
- 🤖 **CI GitHub Actions** : Ajout du workflow `tests.yml` pour exécuter les tests automatiquement.
- 📦 **Dépendances de test** : Ajout de `requirements-test.txt` et `pyproject.toml`.

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
| **Prochaine Grande Marée** | `sensor.maree_saint_malo_prochaine_grande_maree` | Date/heure de la prochaine marée avec coefficient >= 100. Indisponible en morte-eau. |

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
