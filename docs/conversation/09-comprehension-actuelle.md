# Moment 9 — Compréhension actuelle du projet

> Mise à jour : Codex CLI local est retenu et la démonstration doit joindre le vrai téléphone du jury. Voir le [moment 10](./10-codex-cli-appel-jury.md).

Date : 18 juillet 2026

## Vision comprise

Le projet est une fonctionnalité de Codex qui prend en charge des appels administratifs pour le compte de l’utilisateur.

L’utilisateur explique son problème en langage naturel. Codex prépare un mandat précis, obtient une confirmation explicite, déclenche un agent vocal local utilisant une voix synthétique autorisée, suit l’appel, puis rend un compte rendu et les prochaines actions.

Le produit n’est pas un centre d’appels, un outil de prospection ou une application vocale indépendante. C’est une extension personnelle de Codex destinée à réduire la friction des démarches administratives.

## Parcours cible

```text
Problème exprimé dans Codex
        ↓
Collecte des informations manquantes
        ↓
Mandat structuré et limité
        ↓
Aperçu de ce qui sera dit et transmis
        ↓
Confirmation explicite
        ↓
Appel vocal
        ↓
Suivi du statut dans Codex
        ↓
Résumé, engagements et prochaines étapes
```

## Contraintes verrouillées

- La fonctionnalité vit dans Codex.
- Elle est distribuée comme un plugin Codex avec une skill et un serveur MCP local.
- Tous les traitements IA tournent localement.
- Tous les composants logiciels utilisés sont open source.
- Les échantillons vocaux, dossiers et transcriptions restent locaux.
- Aucun appel ne part sans confirmation explicite.
- Le clone vocal provient uniquement d’une voix consentante.
- L’agent annonce qu’il est automatisé et que sa voix est synthétique.
- L’agent ne communique jamais de mot de passe ou de code OTP.
- Il ne peut pas effectuer de paiement, accepter un contrat ou modifier des coordonnées bancaires.
- Il doit demander une reprise humaine pour une authentification forte ou un engagement sensible.

## Architecture comprise

```text
Codex
  └── Plugin administrative-calls
        ├── Skill : workflow et collecte du mandat
        └── Serveur MCP local
              ├── prepare_call
              ├── preview_call
              ├── confirm_call
              ├── start_call
              ├── get_call_status
              ├── get_call_result
              └── stop_call
                    ↓
              Pipeline vocal local
                    ├── STT local
                    ├── LLM local
                    ├── TTS/clonage local
                    └── orchestration audio
                          ↓
                    Asterisk / SIP
```

Les règles critiques sont codées dans le serveur MCP et dans la policy locale. Elles ne reposent pas seulement sur le prompt du modèle.

## Téléphonie

Deux modes sont distingués :

### Démonstration du hackathon

- Asterisk local ;
- appel SIP local ;
- softphone sur ordinateur ou téléphone du réseau local ;
- aucune dépendance cloud pendant la démonstration.

### Appel vers un vrai numéro

- le traitement IA reste local ;
- seul le transport audio passe par un trunk SIP ou une passerelle GSM avec carte SIM ;
- un opérateur reste physiquement nécessaire pour atteindre le réseau téléphonique public.

## MVP de six heures compris

Le MVP ne cherche pas à régler un vrai dossier fiscal complexe. Il doit prouver une boucle complète :

1. demande dans Codex ;
2. mandat et confirmation ;
3. appel SIP local ;
4. conversation française courte ;
5. voix synthétique autorisée ;
6. compte rendu dans Codex.

Une voix générique locale reste le fallback si le clonage temps réel est trop lent.

## Ce qui n’est pas encore figé

### 1. Surface Codex de démonstration

Le plugin est la cible produit. Codex CLI avec un fournisseur local est le chemin techniquement garanti pour une démonstration sans inférence cloud. Le comportement équivalent dans l’application desktop doit encore être vérifié.

### 2. Modèle local

Le choix dépend du matériel disponible. Les candidats documentés sont `gpt-oss-20b`, Qwen3 8B et Qwen3 4B.

### 3. Moteur de clonage vocal

Chatterbox Multilingual et OpenVoice V2 sont les candidats principaux. Le choix final dépendra de la qualité française, de la licence effective des poids et de la latence sur la machine.

### 4. Orchestration

Pipecat minimal offre plus de contrôle. Dograh peut accélérer la mise en route si son installation locale fonctionne immédiatement. Le spike ne doit pas dépasser trente minutes.

## Risque principal

Le risque n’est pas la logique Codex ou le mandat. Le risque est la latence cumulée STT → LLM → TTS sur le matériel disponible.

La stratégie est donc de sécuriser la boucle dans cet ordre :

1. outils visibles dans Codex ;
2. appel SIP local ;
3. STT et réponse texte ;
4. voix locale générique ;
5. clonage vocal.

## Niveau de compréhension

- Vision produit : élevé.
- Parcours utilisateur : élevé.
- Contraintes de confidentialité et de sécurité : élevé.
- Architecture Codex : élevé.
- Pile exacte de modèles : encore à valider sur le matériel.
- Téléphonie publique : volontairement hors MVP initial.
