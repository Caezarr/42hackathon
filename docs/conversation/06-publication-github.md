# Moment 6 — Publication vers GitHub

Date : 18 juillet 2026

## Demande

Publier les notes Markdown créées pendant la conversation dans le dépôt :

- [Caezarr/42hackathon](https://github.com/Caezarr/42hackathon)

## Périmètre retenu

Seuls les fichiers de `docs/conversation/` doivent être publiés.

Les documents appartenant aux autres projets du workspace, notamment `ETUDE_HOME_ASSISTANT.md` et `life-assistant/ROADMAP.md`, restent exclus.

## État constaté

- Le dépôt Git local ne contient encore aucun commit.
- La branche locale est `master`.
- Aucun remote Git n’est configuré.
- GitHub CLI (`gh`) n’est pas installé.

## Blocage

La publication nécessite l’installation et l’authentification de GitHub CLI avant de pouvoir vérifier l’accès au dépôt, créer une branche dédiée, committer uniquement les notes et pousser en sécurité.

## Workflow prévu après authentification

1. Vérifier l’accès à `Caezarr/42hackathon`.
2. Connecter ou cloner le dépôt sans inclure les autres fichiers du workspace.
3. Créer une branche `agent/add-conversation-docs` si nécessaire.
4. Ajouter uniquement `docs/conversation/*.md`.
5. Créer un commit `add hackathon conversation docs`.
6. Pousser la branche.
7. Ouvrir une pull request en brouillon, sauf demande explicite de publication directe sur la branche par défaut.

