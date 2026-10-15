# Verifiering 2026-10-15 (flerradsläge och källor)

- `chat.py`: 429 rader, Python AST parsas utan fel.
- Linux, Python 3.13: 35 unittest-tester passerar (25 tidigare + 10 nya).
- Nya kontroller: `/paste` med fråga, `/end`, `/cancel`, tomt block, för stort
  block, EOF före `/end`; att `/clear` och sökvägar inuti ett block följer med
  som data; okända kommandon skickas inte men `/var/log/…`-frågor gör det;
  för långa rader avvisas utan att sessionen avslutas; `/kb av` ger `x_kb: false`
  och `/kb på` tar bort fältet; källhändelse valideras (schema, `https`, kontroll-
  tecken, dubbletter, max tio, två händelser) och visas separat; varning för
  hänvisning utanför källistan; kodstaket längre än backticks i underlaget.
- Automatisk upptäckt av inklistring testad mot riktig pseudoterminal (pty),
  dels i enhetstest av radläsaren, dels end-to-end: hela klienten startad i en
  pty mot lokal SSE-testserver, tre loggrader inklistrade utan `/paste` och en
  fråga skriven efteråt gav **ett** anrop med frågan och kodstaketet, samt
  korrekt visad Jira-källa.
- Gatewayen i `GATEWAY_PROTOCOL.md` är inte byggd. Källhändelsen är testad mot
  testserver, inte mot en riktig gateway. Systemprompten i `prompts/` är inte
  utvärderad mot målmodellen.
- Upptäckten av inklistring bygger på att raderna redan väntar i terminal-
  bufferten (150 ms mellan rader). Över långsamma SSH-förbindelser kan ett block
  delas; `/paste` är reservvägen. Verifieras i målmiljön.

# Verifiering 2026-10-12 (första versionen)

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
