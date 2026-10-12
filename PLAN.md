# Minimal PoC-klient

Godkänd riktning: användaren gav fria tyglar efter designförslaget. Implementeras
direkt i denna session, utan ytterligare godkännandesteg eller delegering.

Mål: Linux, Python 3.11+, cirka 150–250 rader klientkod, HTTPX och valfritt Rich.
JSON-konfiguration med exakt endpoint, obligatorisk modell och valfri token.
Konfigfilen är enda applikationsdatafilen; kräver ägare + exakt 0600, inga symlänkar.
Ingen produktionsadress hittas på. Endast uttryckligt loopbacktest är aktiverat.
Inga verktyg, shellanrop, dokumentläsning eller diskhistorik.

1. chat.py: konfigkontroll, tokenval, CLI --check; config.example.json och kravfiler.
   Testa felaktiga rättigheter, symlänk, ägare, URL, token och Linuxkrav.
2. chat.py: begränsad SSE-parser, HTTP-status/timeout, transaktionell historik.
   Testa delade UTF-8-paket, multiline-SSE, avbrott, storleksgränser, tool calls,
   redirect utan tokenläckage och avstängd miljöproxy.
3. Valfri Markdown efter streaming, terminalsanering, README, Caddy och sandbox.
   Testa terminalkontroller, piping, CLI med lokal protokollserver och Linux.

Verifiering: unittest i WSL; riktig Ollama bara om server/modell redan finns.
Redovisa protokolltester separat från riktig inferens och driftsatt proxy/sandbox.
