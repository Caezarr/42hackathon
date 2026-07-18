# Moment 1 — Vision et roadmap de six heures

Date : 18 juillet 2026

> Mise à jour : l’architecture cloud décrite dans cette note a été remplacée par la contrainte entièrement locale et open source du [moment 4](./04-architecture-locale-open-source.md). La vision produit et les garde-fous restent valables.

## Vision

Permettre à un utilisateur de décrire un problème administratif à Codex. Codex prépare ensuite l’appel, obtient l’autorisation de l’utilisateur, lance un agent vocal mandaté et restitue le résultat.

Exemple :

> « Mon remboursement est bloqué. Appelle mon assurance pour comprendre pourquoi et dis-moi quelle est la prochaine étape. »

## Démonstration cible

1. L’utilisateur décrit son problème à Codex.
2. Codex collecte les informations strictement nécessaires.
3. Codex affiche un mandat d’appel structuré.
4. L’utilisateur confirme explicitement.
5. Un téléphone de démonstration sonne.
6. L’agent annonce qu’il est une IA et que sa voix est synthétique et autorisée.
7. L’agent mène la conversation sans dépasser son mandat.
8. Codex restitue le résultat et la prochaine action.

## Architecture MVP

```text
Utilisateur
    ↓
Codex
    ↓
CLI local admin-call
    ↓
Agent ElevenLabs
    ↓
Twilio
    ↓
Destinataire

Conversation → transcription/statut → Codex → synthèse utilisateur
```

## Roadmap

| Temps | Travail | Critère de sortie |
|---|---|---|
| 0:00–0:30 | Configurer les comptes, clés et numéro de test | Twilio et ElevenLabs accessibles |
| 0:30–1:15 | Relier le numéro Twilio à l’agent | Un appel de test arrive sur un téléphone |
| 1:15–2:00 | Créer et tester la voix synthétique autorisée | L’introduction est intelligible en français |
| 2:00–3:00 | Construire `admin-call` | Codex peut lancer un appel depuis le terminal |
| 3:00–4:00 | Ajouter mandat, variables et confirmation | Aucun appel ne part sans validation |
| 4:00–4:45 | Récupérer statut, transcription et résultat | Codex affiche une synthèse exploitable |
| 4:45–5:30 | Tester les cas difficiles | Refus, silence et question inconnue sont gérés |
| 5:30–6:00 | Geler le code et répéter la démonstration | Démo reproductible en moins de trois minutes |

## Garde-fous obligatoires

- Cloner uniquement la voix d’une personne ayant donné son consentement explicite.
- Annoncer dès le début qu’il s’agit d’un assistant automatisé.
- Dire que la voix est synthétique et utilisée avec autorisation.
- Ne jamais prétendre que l’agent est physiquement l’utilisateur.
- Ne jamais communiquer de mot de passe ou de code OTP.
- Interdire les paiements, contrats, changements bancaires et décisions juridiques.
- Prévoir une reprise humaine pour toute vérification d’identité forte.
- Désactiver l’enregistrement audio par défaut.

## Périmètre exclu du MVP

- Appel réel aux impôts pendant la démonstration.
- Dashboard complexe.
- Gestion multi-utilisateur.
- Base de données complète.
- Recherche automatique des numéros administratifs.
- Paiement ou signature de contrat.
- Transfert d’appel sophistiqué.

## Definition of done

Le MVP est terminé lorsque :

- Codex transforme une demande libre en mandat structuré ;
- une confirmation explicite est obligatoire ;
- un vrai téléphone sonne ;
- l’agent révèle sa nature artificielle ;
- la voix appartient à une personne consentante ;
- une conversation française de deux minutes fonctionne ;
- le résultat revient dans Codex ;
- une voix générique reste disponible comme solution de secours.

## Sources

- [ElevenLabs — appel sortant via Twilio](https://elevenlabs.io/docs/eleven-agents/api-reference/twilio/outbound-call)
- [OpenAI — modèle Realtime](https://developers.openai.com/api/docs/models/gpt-realtime)
- [ElevenLabs — Instant Voice Cloning](https://elevenlabs.io/docs/eleven-api/guides/how-to/voices/instant-voice-cloning)
- [CNIL — information en cas d’enregistrement](https://cnil.fr/fr/cnil-direct/question/enregistrement-ou-ecoute-des-conversations-telephoniques-faut-il-informer-ses)
- [Règlement européen sur l’IA](https://eur-lex.europa.eu/legal-content/en/TXT/?uri=CELEX%3A32024R1689)
