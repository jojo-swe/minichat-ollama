# Minichat – lokal textassistent

En liten Linux-klient för Ollamas OpenAI-kompatibla streaming-API. Modellen
producerar bara text. Klienten har inga verktyg, subprocesser, shellfunktioner,
filuppladdningar, webbläsning eller diskhistorik. Modellens kommandoförslag
granskas och kopieras manuellt av användaren.

## Kom igång på Linux

Stödd bas: Python 3.11+ på Ubuntu/Debian med CA-bundle på
`/etc/ssl/certs/ca-certificates.crt`. Windows stöds inte av själva CLI:n eftersom
0600-kontrollen ska vara riktig. Kör i Linux eller WSL, med en server som är
nåbar från den miljön. Windows och WSL kan ha olika loopback-nätverk.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Valfri Markdown:
.venv/bin/python -m pip install -r requirements-markdown.txt
umask 077
mkdir -p "$HOME/.config/minichat"
cp config.example.json "$HOME/.config/minichat/config.json"
chmod 600 "$HOME/.config/minichat/config.json"
```

Installationen skriver filer; den körande klienten gör inga applikationsskrivningar.
På Debian/Ubuntu kan paketet python3-venv behövas. Installera beroenden på en
godkänd byggmaskin inför offlineutrullning. Kravfilerna låser direkta versioner,
men är inte en fullständig hash-låst leveranskedja; IT ska låsa och granska även
transitiva wheels inför distribution. Använd `-B` för att förhindra Python-cache.

## Steg 1: konfiguration och rättigheter

Ändra `model` i konfig till ett exakt modellnamn från `ollama list` på servern.
Inga modeller laddas ner av klienten. Exempel för lokaltest:

```json
{
  "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
  "model": "qwen3:8b"
}
```

```sh
.venv/bin/python -B chat.py --config "$HOME/.config/minichat/config.json" --local-test --check
```

Förväntat: `Konfiguration OK. Ingen anslutning gjord.` Ändra till 0644 och
kör igen: klienten ska vägra. Återställ sedan 0600. Den kräver en vanlig fil
med aktuell användare som ägare, exakt 0600 och en hårdlänk; slutlig symlänk
avvisas. Lägg konfigen i en katalog som andra användare inte kan ändra.

## Steg 2: riktig streaming

Starta Ollama separat om den inte redan kör: `ollama serve`. Lokaltest kräver
loopback-adressen ovan, flaggan `--local-test` och **ingen token**, inte ens i
miljön. Klienten vägrar skicka en Bearer-token över detta HTTP-undantag.

```sh
unset OLLAMA_API_KEY
.venv/bin/python -B chat.py --config "$HOME/.config/minichat/config.json" --local-test
```

Skriv en rad och tryck Enter. `/clear` tömmer dialoghistoriken; `/exit`, EOF
eller Ctrl+C avslutar. Vid API-/streamingfel avslutas klienten med kod 1;
Ctrl+C ger 130. Inga automatiska återförsök görs. Vanlig avslutning ger 0.

För piping skickas varje icke-tom rad som ett eget meddelande, sekventiellt:

```sh
printf 'Vad gör pwd?\nOch ls?\n/exit\n' |
  .venv/bin/python -B chat.py --config "$HOME/.config/minichat/config.json" --local-test
```

## Steg 3: Markdown och granskning

```sh
.venv/bin/python -B chat.py --config "$HOME/.config/minichat/config.json" --local-test --markdown
.venv/bin/python -B -m unittest discover -s tests -v
# Valfritt test som faktiskt kör en redan installerad modell:
.venv/bin/python -B tests/smoke_ollama.py qwen3:8b
```

Markdownläget streamar först texten och skriver därefter ut en formaterad kopia
av det färdiga svaret. Vid piping används bara text, även med `--markdown`.
Inga länkar öppnas eller bilder hämtas. ANSI/OSC-kontrolltecken, bidi-kontroller
och andra Unicode-kontrolltecken filtreras från servertext före utskrift.
Rich får skapa sina egna färgsekvenser, men inga klickbara terminallänkar.
Sanering skyddar terminalprotokollet, inte mot vilseledande råd från modellen.

## Produktion: hårdkodad adress + personlig nyckel

Produktionsallowlisten levereras **tom**. IT måste redigera `ALLOWED_ENDPOINTS`
i `chat.py`, granska ändringen och distribuera skrivskyddad kod, exempelvis:

```python
ALLOWED_ENDPOINTS = frozenset({
    "https://ollama.company.internal/v1/chat/completions",
})
```

Använd er faktiska interna adress, inte exemplet. Inga wildcard, query-parametrar
eller alternativa stavningar matchas. Konfig kan aldrig utöka allowlisten.
Ta bort lokaltestundantaget ur en produktionsdistribution om det inte behövs.

```json
{
  "endpoint": "https://ollama.company.internal/v1/chat/completions",
  "model": "ERT_INSTALLERADE_MODELLNAMN",
  "token": "PERSONLIG_NYCKEL_FRAN_IT"
}
```

Token i 0600-konfigen är det filbaserade alternativet; ingen separat tokenfil
öppnas. `OLLAMA_API_KEY` har företräde om den är satt. Lägg aldrig token på
kommandoraden eller i Git. En tom miljövariabel räknas som en tom token.
Konfigurationen skrivs aldrig ut. HTTP-felkroppar, nycklar och råa undantag
skrivs inte heller ut. CLI:n loggar ingenting själv.

Installera intern CA i systemets CA-bundle via IT. TLS och hostname-validering
kan inte stängas av. `SSL_CERT_FILE`, `SSL_CERT_DIR`, `HTTP_PROXY`, `HTTPS_PROXY`
och `.netrc` används inte. Ingen redirect följs. Kör utan `--local-test`:

```sh
.venv/bin/python -B chat.py --config "$HOME/.config/minichat/config.json" --markdown
```

Konfig: högst 16 KiB. Indatarad: cirka 8 Ki tecken. Svar: 64 Ki tecken,
SSE-rad/händelse: 64 KiB, rå ström: 1 MiB. Historik inklusive reserverat
svarsutrymme: 128 Ki tecken. Max 2048 genererade token per anrop; ett svar som
tar slut på tokenbudget markeras som ofullständigt och sparas inte i historiken.
Historik kapas aldrig tyst; använd `/clear` när dialogen blir lång.
Anslutningstimeout 5 s, nätverksinaktivitet 30 s. Efter 180 s avbryts strömmen
vid nästa mottagna paket (en pågående läsning kan lägga till upp till 30 s).
Ett normalt `finish_reason: stop` följt av `[DONE]` krävs för att spara rundan.

## Proxy, isolering och PoC-gränser

`examples/Caddyfile` är en **ej driftsverifierad mall för en pilotnyckel**.
Den begränsar sökväg/metod, tar bort Authorization mot Ollama och stänger av
buffring för streaming. Tom nyckel ska inte ge åtkomst. Tilldela miljövariabeln
`OLLAMA_PILOT_TOKEN` via skyddad driftkonfiguration; använd en lång slumpnyckel.
Kontrollera med `caddy validate --config examples/Caddyfile --adapter caddyfile`
och prova saknad, tom, felaktig och korrekt token innan användning.

Mallen är inte PoC:ns kompletta autentiserings-/auditlösning: personliga
identiteter, nyckelrotation, rate-limit, central korrelation och fullständig
promptloggning måste införas och granskas separat. Caddys vanliga accesslogg
är inte promptloggning. Aktivera inte loggning av autentiseringshemligheter.

Ollama ska endast lyssna på localhost bakom proxyn. Spärra serverns internet
och produktionsnät i brandvägg. Klienten spärrar modellnamn med `cloud`, men
det bevisar inte att en server eller ett modellalias inte använder molntjänster.
Påståendet att all data stannar internt kräver även server- och nätverkskontroll.

`examples/SANDBOX.md` innehåller en separat Linux-mall och dess begränsningar.
Att inte anropa filsystemet är inte samma sak som att sakna OS-rättigheter.
Runtime, bibliotek, CA-certifikat och terminal kräver åtkomst. Ingen verifierad
OS-sandbox levereras som färdig driftinstallation. Minne kan också hamna i
swap/core dumps; terminalen kan spela in utdata. `/clear` är inte säker radering.

## Källor

- [Ollamas OpenAI-kompatibilitet](https://docs.ollama.com/api/openai-compatibility)
- [HTTPX och miljöinställningar](https://www.python-httpx.org/environment_variables/)
- [HTTPX TLS](https://www.python-httpx.org/advanced/ssl/)
- [Rich Markdown](https://rich.readthedocs.io/en/latest/reference/markdown.html)
- [Caddy reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [Caddy matchers](https://caddyserver.com/docs/caddyfile/matchers)
