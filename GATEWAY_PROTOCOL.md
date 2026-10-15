# Protokoll mellan klient och gateway

Klienten pratar Ollamas OpenAI-kompatibla streaming-API. Gatewayen (som ännu inte
är byggd) ligger mellan proxyn och Ollama och lägger till två tillägg med prefixet
`x_`. Mot ren Ollama fungerar klienten som tidigare: tilläggen används bara när
gatewayen skickar dem.

## Förfrågan: klient → gateway

`POST /v1/chat/completions` med `Authorization: Bearer <personlig nyckel>`.

| Fält | Värde | Gatewayens ansvar |
|---|---|---|
| `model` | Modellnamn från konfig | Valideras mot allowlist eller skrivs över |
| `messages` | `user`/`assistant`, aldrig `system` från klienten | Avvisar `system` och andra roller; lägger in systemprompten |
| `stream` | `true` | Avvisar annat |
| `max_tokens` | 2048 | Begränsar till serverns tak |
| `x_kb` | Utelämnas normalt; `false` efter `/kb av` | Hoppar då över sökningen; loggas i audit |

Alla andra fält (`tools`, `tool_choice`, `functions`, `response_format`, `options`
m.fl.) ska avvisas med HTTP 400. Gatewayen räknar token för systemprompt,
historik, källutdrag och svarsbudget mot det konfigurerade kontextfönstret och
svarar **413** om det inte ryms. Inget kortas tyst.

## Svar: gateway → klient

`text/event-stream`, okomprimerat. Ordinarie Ollama-händelser passeras igenom.
Gatewayen får dessutom skicka **en** källhändelse, före `[DONE]`:

```text
data: {"choices": [], "x_sources": [
  {"n": 1, "kind": "confluence", "title": "BGP – felsökning av grannskap",
   "url": "https://confluence.intern/pages/123456", "version": "v12",
   "updated": "granskad 2026-09-03"},
  {"n": 2, "kind": "jira", "title": "NET-4812 BGP-flapp mot ISP-B",
   "url": "https://jira.intern/browse/NET-4812", "status": "Pågående",
   "updated": "2026-10-15 09:12"}
]}
```

| Fält | Krav (klienten avvisar hela svaret annars) |
|---|---|
| `n` | Heltal 1–10, unikt |
| `kind` | `confluence`, `jira` eller `dokument` |
| `title` | Sträng, 1–300 tecken |
| `url` | `https://`, högst 2048 tecken, inga mellanslag eller kontrolltecken |
| `status`, `updated`, `version` | Valfria strängar, högst 300 tecken |
| Övrigt | Okända nycklar, fler än 10 källor eller två källhändelser avvisas |

Klienten sanerar alla textfält, visar listan under svaret med rubriken
"Källor (hämtade av tjänsten, inte genererade av modellen)", öppnar aldrig länkar
och varnar om svaret hänvisar till ett `[n]` som saknas i listan.

Gatewayen ska själv kontrollera hänvisningarna innan källhändelsen skickas och
bara ta med källor som användaren har behörighet till enligt beslutad modell
(etapp 2a). Klientens kontroll är ett andra skydd, inte det primära.

## Fel

| Status | Betydelse | Klientens text |
|---|---|---|
| 400 | Otillåtet fält eller format | API-anrop misslyckades |
| 401 / 403 | Ogiltig eller spärrad nyckel / ej behörig | Ogiltig token / Åtkomst nekad |
| 413 | Ryms inte i kontextfönstret | Frågan är för stor |
| 429 | Rate-limit eller kö full | För många anrop |
| 5xx | Serverfel | API-anrop misslyckades |

Felkroppar visas aldrig för användaren. Ingen automatisk retry görs.
