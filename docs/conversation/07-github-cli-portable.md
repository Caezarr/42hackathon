# Moment 7 — GitHub CLI portable sans Winget

Date : 18 juillet 2026

## Contrainte

Winget n’est pas disponible sur la machine.

## Solution mise en place

La distribution portable officielle de GitHub CLI a été téléchargée dans le workspace, sans installation système :

```text
.tools/gh/bin/gh.exe
```

Version téléchargée : `2.96.0` pour Windows AMD64.

## Vérifications GitHub

- Le connecteur GitHub de Codex peut lire `Caezarr/42hackathon`.
- Le fichier `README.md` du dépôt est accessible.
- Le connecteur ne possède pas les droits d’écriture : la création de branche retourne une erreur HTTP 403.
- La publication doit donc passer par le GitHub CLI portable authentifié avec le compte utilisateur.

## État actuel

Une fenêtre PowerShell interactive a été ouverte pour exécuter :

```text
gh auth login --hostname github.com --git-protocol https --web
```

La publication reprendra dès que l’autorisation GitHub aura été validée.

