# Moment 13 — Passage aux commits directs sur main

Date : 18 juillet 2026

## Décision

Le workflow par pull request est abandonné à la demande de l’équipe.

À partir de maintenant, les modifications validées sont commitées puis poussées directement sur :

```text
Caezarr/42hackathon:main
```

## Permission

Le compte GitHub connecté `cristalineIOI` possède désormais la permission `WRITE` sur `Caezarr/42hackathon`.

## Contrôle avant publication

Avant le premier push direct :

- `upstream/main` est toujours au commit initial `3b8d603` ;
- notre branche est en avance et n’est pas en retard sur `main` ;
- le push peut donc être effectué en fast-forward ;
- aucun force-push n’est nécessaire.

## Travail du coéquipier détecté

Une branche distincte existe maintenant :

```text
upstream/agent/document-hackathon-build
```

Derniers commits observés :

- `7cec4f9` — Document the self-hosted hackathon build ;
- `6f207f3` — Clarify the judged deployment path ;
- `9074864` — Remove unrelated Agent Call branding.

Cette branche n’est pas fusionnée automatiquement. Elle reste intacte pour une comparaison et une intégration contrôlées.

## Règle de sécurité Git

Pour chaque push direct :

1. récupérer `upstream/main` ;
2. vérifier l’absence de divergence ;
3. intégrer les changements distants sans force-push ;
4. vérifier les fichiers stagés ;
5. committer ;
6. pousser sur `main`.

La pull request #1 sera fermée après confirmation que les documents sont présents directement sur `main`.

## Résultat

- Le travail du coéquipier a été fusionné sur `main` via la PR #2.
- Les commits documentaires ont été rebasés au-dessus de ce merge sans conflit.
- Le push direct vers `Caezarr/42hackathon:main` a réussi au commit `37258d8`.
- La pull request #1, devenue inutile, a été fermée.
- Le checkout local actif suit désormais directement `upstream/main`.
