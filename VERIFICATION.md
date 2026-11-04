# Verifiering 2026-10-12

## Tillägg 2026-10-13: nätverksprofil och flerradig inmatning

- Klienten är nu 250 rader och har en fast systeminstruktion för Cisco IOS,
  FortiOS och Linux. Den tillför ingen åtkomst till nätutrustning.
- 29 tester passerar i Ubuntu/WSL efter tillägget: inkluderar bevarade indrag
  och radbrytningar, `/cancel`, EOF, tomma/för stora block och att `/clear`
  tar bort föregående ärende men behåller systeminstruktionen.
- Den slutliga Cisco-/FortiOS-formuleringen av instruktionen är statiskt
  kontrollerad. Ingen ny modellutvärdering av diagnoskvalitet har genomförts.
- POC.md version 1.4 och NETWORK_WORKFLOW.md beskriver önskat beteende och
  manuella labbfall. De är inte bevis för korrekt felsökning på faktisk utrustning.

## Ursprunglig klientverifiering 2026-10-12

- `chat.py`: 223 rader, Python AST parsas utan fel.
- Ubuntu 24.04 i WSL, Python 3.12.3: 25 unittest-tester passerar.
- Kontroller omfattar konfig/0600/ägare/symlänk/hårdlänk/FIFO, exakt allowlist,
  tokenprioritet och header-injektion, rå UTF-8 delad byte för byte, multiline-SSE,
  trasig/djupt nästlad JSON, avbrutet svar, storleksgränser, tidsgräns,
  verktygsanrop, HTTP-fel/redirect, terminalsanering och Rich utan OSC-länkar.
- CLI-flöde med riktig lokal HTTP-testserver: två turer, /clear, ny tur, /exit,
  piping och satt HTTP_PROXY. Testtransporten ändrar endast testserverns port.
- Riktig befintlig Ollama på Windows: `qwen3:8b`, anrop genom klientens
  `answer()` med streaming gav `HEJ` och normalt avslut. Ingen token skickades.
- Hela Linux-CLI:n mot Windows-Ollama via WSL-loopback misslyckades med
  anslutningsfel. Inga nätverksinställningar ändrades. Linux-rättigheter och
  verklig modellinferens är därför två separata verifieringar.
- WSL saknade python3-venv/ensurepip. Testberoenden installerades isolerat i
  `.test-deps` via Windows pip och de plattformsoberoende paketen användes med
  PYTHONPATH under Linux. Inga systempaket eller användarberoenden uppgraderades.
- Caddy, intern TLS-proxy och bubblewrap-mallen har inte driftsverifierats.
- Ingen verifierad seccomp/LSM-policy eller nätverksisolering har installerats.
  Detta är klientkod och driftsunderlag, inte ett intyg om färdig PoC-säkerhet.

Reproducerbart standardkommando efter installation av beroenden på Linux:
`python -B -m unittest discover -s tests -v`

Sluttest mot målmiljön: korrekt/fel token, betrodd/obetrodd CA, fel hostname,
proxyredirect, timeout, avbruten anslutning, verklig Markdown-TTY och sandboxens
fil-/nätverksbegränsningar. Detta kräver den riktiga proxyadressen och målmaskinen.
