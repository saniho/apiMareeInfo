# apimareeInfo

Objectif, recuperer le contenu de la page web maree.info pour avoir les informations sur les horaires de marées, depuis le site : http://maree.info/
exemple : http://maree.info/124

pour declarer le sensor dans HA : 

```yaml
- platform: apiMareeInfo
  code: 124
  scan_interval: 1800
```
