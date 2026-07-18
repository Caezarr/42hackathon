# Telephony transports

Agent Call does not manufacture access to the public phone network. Each operator connects a transport they own.

## Comparison

| Transport | Public phone calls | External dependency | Status |
| --- | --- | --- | --- |
| Browser/WebRTC | No | None on a local network | First development target |
| User SIP trunk | Yes | Operator's SIP carrier | Primary PSTN target |
| GSM/LTE-to-SIP | Yes | Operator's SIM and cellular network | Preferred zero-API SIM path |
| Android Bluetooth | Yes | Operator's Android phone, SIM, Linux, BlueZ | Experimental |

## Browser/WebRTC

The browser transport proves the realtime audio and local inference loop without telecom cost. It cannot dial a public phone number.

## User-owned SIP

LiveKit SIP connects to credentials supplied by the operator. Caller identity must be a number the carrier has verified for that account. SIP remains the cleanest production transport.

The reproducible topology depends on the carrier:

- a registered outbound trunk may tolerate NAT, but RTP must still return to the advertised address;
- a direct SIP peer normally needs a stable public IP or an operator-owned public edge;
- SIP commonly uses UDP/TCP 5060 or TLS 5061;
- the planned LiveKit SIP RTP range is UDP 10000–20000;
- the planned LiveKit RTC media range is separate, for example UDP 50000–60000;
- HTTPS/WSS and any SIP TLS endpoint need valid certificates;
- Postgres, Valkey, workers, and inference endpoints are never exposed publicly.

A laptop behind CGNAT may need an operator-owned Linux edge linked to the private machine over WireGuard. The project does not provide a shared edge. The judged hackathon topology uses exactly this model: the reference Mac runs the control and inference path, while one team-owned public Linux edge terminates LiveKit/SIP and connects back over WireGuard.

Reference deployment documentation:

- [LiveKit self-hosting](https://docs.livekit.io/transport/self-hosting/deployment/)
- [LiveKit SIP server](https://docs.livekit.io/transport/self-hosting/sip-server/)

## GSM/LTE-to-SIP gateway

The operator inserts a SIM into a local gateway that exposes SIP on the LAN:

```text
LiveKit SIP -> LAN gateway -> operator SIM -> cellular network
```

This removes a cloud telephony API but not the cellular network. The gateway must be isolated from the public internet, use a changed administrator password, and pass codec, DTMF, answer, and hangup tests.

When LiveKit SIP and the GSM gateway share the operator's LAN, SIP signaling and RTP stay LAN-only. The gateway itself is the cellular boundary and should not expose an administrator interface to the WAN.

## Android Bluetooth bridge

Asterisk's `chan_mobile` can use a Bluetooth phone as an FXO device and dial through it:

```text
LiveKit SIP -> Asterisk -> Dial(Mobile/device/number)
            -> Bluetooth HFP/SCO -> Android phone -> SIM
```

Requirements and limitations:

- Linux and BlueZ;
- a paired Android phone owned by the operator;
- direct Bluetooth and D-Bus access;
- normally one active phone per Bluetooth adapter;
- narrow-band and device-dependent SCO audio;
- more fragile reconnection than SIP.

This transport should run natively on Linux or on a small user-owned Linux bridge, not inside an ordinary unprivileged container.

Official Asterisk references:

- [Introduction to the Mobile Channel](https://docs.asterisk.org/Configuration/Channel-Drivers/Mobile-Channel/Introduction-to-the-Mobile-Channel/)
- [Mobile Channel Features](https://docs.asterisk.org/Configuration/Channel-Drivers/Mobile-Channel/Mobile-Channel-Features/)
- [Mobile Channel Requirements](https://docs.asterisk.org/Configuration/Channel-Drivers/Mobile-Channel/Mobile-Channel-Requirements/)

## Identity and destination policy

Caller-ID spoofing is not a transport and is outside project scope. Agent Call presents only the real SIM number or a carrier-verified SIP identity.

Every live transport must block emergency, premium-rate, short-code, and prohibited destinations before any side effect. A transport is not ready until a consented test call confirms bidirectional audio, DTMF, hangup, and event reporting.
