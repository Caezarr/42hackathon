# Moment 8 — Publication par fork et pull request

Date : 18 juillet 2026

## Authentification

GitHub CLI portable est authentifié avec le compte `cristalineIOI`.

## Permission constatée

Le compte connecté possède le droit `READ` sur `Caezarr/42hackathon`, mais pas le droit de pousser directement une branche dans ce dépôt.

## Flux retenu

Le flux GitHub standard est utilisé :

1. création du fork `cristalineIOI/42hackathon` ;
2. création d’une branche dédiée dans le fork ;
3. commit des fichiers `docs/conversation/*.md` uniquement ;
4. push vers le fork ;
5. ouverture d’une pull request vers `Caezarr/42hackathon:main`.

## Fork

- [cristalineIOI/42hackathon](https://github.com/cristalineIOI/42hackathon)

Ce mécanisme permet à l’équipe propriétaire de relire puis fusionner les documents sans accorder de droit d’écriture direct supplémentaire.

