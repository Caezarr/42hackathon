# Moment 11 — Push Git après chaque modification

Date : 18 juillet 2026

## Règle de travail

À partir de maintenant, chaque modification apportée au projet doit être publiée sur Git avant la fin du tour de travail.

Le cycle obligatoire est :

```text
modification
→ vérification
→ staging ciblé
→ commit
→ push
→ compte rendu utilisateur
```

## Portée

- Aucun changement local terminé ne doit rester uniquement dans le workspace.
- Seuls les fichiers appartenant au projet sont stagés.
- Les fichiers des autres projets restent exclus.
- Les commits doivent être courts et décrire la modification.
- Les pushes continuent sur la branche active de la pull request tant qu’elle n’est pas fusionnée.
- En cas d’échec du push, le blocage doit être annoncé explicitement avant de terminer le tour.

## Branche actuelle

```text
cristalineIOI:agent/add-conversation-docs
```

Pull request cible :

- [Caezarr/42hackathon#1](https://github.com/Caezarr/42hackathon/pull/1)

