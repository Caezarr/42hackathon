# Définition du dialer

## Question

Que signifie « dialer » dans le projet ?

## Réponse

Le **dialer** est le composant logiciel qui demande au fournisseur téléphonique de lancer l’appel réel, puis contrôle son cycle de vie.

Dans notre MVP, il doit notamment :

1. recevoir de Codex le numéro validé et l’objectif de l’appel ;
2. exiger la confirmation explicite de l’utilisateur ;
3. demander au trunk SIP ou à la passerelle téléphonique de composer le numéro ;
4. détecter les états `ringing`, `answered`, `failed` et `ended` ;
5. connecter l’audio de l’appel à Pipecat ;
6. permettre de raccrocher et de remonter le résultat à Codex.

Le dialer n’est donc ni le modèle vocal, ni Pipecat, ni Codex. C’est la couche de contrôle située entre notre agent vocal et le réseau téléphonique public.

```text
Codex → MCP local → dialer → trunk/passerelle → téléphone du jury
                         ↕
                      Pipecat
```

Même si aucun serveur SIP n’est hébergé localement, un composant de ce type reste nécessaire pour déclencher l’appel via un opérateur ou une passerelle externe.
