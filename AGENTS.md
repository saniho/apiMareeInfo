# AGENTS.md

## Release normale (ex: 2.1.7)

Toutes les étapes sont **obligatoires**. HACS ne détecte la mise à jour que si le tag git + release GitHub existent.

### Étape 1 — Bumper la version

Dans ces 3 fichiers, remplacer l'ancienne version par la nouvelle :
- `custom_components/apiMareeInfo/const.py` → `__VERSION__ = "2.1.7"`
- `custom_components/apiMareeInfo/manifest.json` → `"version": "2.1.7"`
- `README.md` → « Version actuelle » + entrée changelog

### Étape 2 — Commit + push

```bash
git add -A && git commit -m "chore: bump version to 2.1.7"
git push
```

### Étape 3 — Tag git

```bash
git tag 2.1.7
git push origin 2.1.7
```

### Étape 4 — Release GitHub

Récupérer le token dans `~/.config/gh/hosts.yml` (clé `oauth_token`).

```bash
curl -s -X POST \
  -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/saniho/apiMareeInfo/releases \
  -d '{"tag_name":"2.1.7","target_commitish":"master","name":"v2.1.7","body":"<notes>","draft":false,"prerelease":false}'
```

### Étape 5 — Clôturer l'issue

```bash
curl -s -X PATCH \
  -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/saniho/apiMareeInfo/issues/<NUMBER> \
  -d '{"state": "closed"}'
```

---

## Release beta (ex: 2.1.8beta1)

Même processus que la release normale, avec ces différences :

### Étape 1 — Bumper la version

**ATTENTION** : Home Assistant **rejette** les points dans la version bêta du manifest.
- ❌ `2.1.8.beta.1` → invalide, l'intégration ne se chargera pas
- ✅ `2.1.8beta1` → format correct

Dans ces 3 fichiers :
- `const.py` → `__VERSION__ = "2.1.8beta1"`
- `manifest.json` → `"version": "2.1.8beta1"`
- `README.md` → idem

### Étape 2 — Commit + push

Sur la **feature branch** (pas sur master) :
```bash
git add -A && git commit -m "chore: bump version to 2.1.8beta1"
git push
```

### Étape 3 — Tag git

```bash
git tag 2.1.8beta1
git push origin 2.1.8beta1
```

### Étape 4 — Release GitHub (pré-release)

Ajouter `"prerelease": true` :
```bash
curl -s -X POST \
  -H "Authorization: token <TOKEN>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/saniho/apiMareeInfo/releases \
  -d '{"tag_name":"2.1.8beta1","target_commitish":"feature/xxx","name":"v2.1.8beta1","body":"<notes>","draft":false,"prerelease":true}'
```

### Étape 5 — Clôturer l'issue

Identique à la release normale.

> **Note** : Pour voir les bêtas dans HACS, l'utilisateur doit activer « Show beta versions » dans les paramètres HACS.

---

## Checklist rapide

Avant de valider une release, vérifier :

- [ ] Version bumpée dans `const.py`
- [ ] Version bumpée dans `manifest.json`
- [ ] README.md mis à jour (version + changelog)
- [ ] Commit + push
- [ ] Tag git créé + poussé
- [ ] Release GitHub créée avec le bon `prerelease` (false pour stable, true pour beta)
- [ ] Issue GitHub clôturée
