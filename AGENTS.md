# AGENTS.md

## Actions à mener lors d'une release

1. **Bumper la version** dans :
   - `custom_components/apiMareeInfo/const.py` (`__VERSION__`)
   - `custom_components/apiMareeInfo/manifest.json` (`version`)
2. **Mettre à jour le README.md** (version actuelle + entrée changelog)
3. **Commit + push** sur `master`
4. **Créer le tag git** : `git tag <version> && git push origin <version>`
5. **Créer la release GitHub** via l'API (token dans `~/.config/gh/hosts.yml`) :
   ```bash
   curl -s -X POST \
     -H "Authorization: token <token>" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/saniho/apiMareeInfo/releases \
     -d '{"tag_name":"<version>","target_commitish":"master","name":"v<version>","body":"<notes>","draft":false,"prerelease":false}'
   ```
6. **Clôturer l'issue GitHub** associée via l'API :
   ```bash
   curl -s -X PATCH \
     -H "Authorization: token <token>" \
     -H "Accept: application/vnd.github+json" \
     https://api.github.com/repos/saniho/apiMareeInfo/issues/<number> \
     -d '{"state": "closed"}'
   ```

**Important** : HACS utilise le tag git + la release GitHub pour détecter les nouvelles versions. Sans ces deux étapes, HACS ne verra pas la mise à jour.
