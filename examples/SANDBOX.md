# Linux-isolering – driftsmall, inte verifierad här

Klienten har inga anrop för att exekvera kommandon eller skriva användardata.
Det är inte en OS-sandbox. Kör aldrig klienten som root. IT ska äga klientkod,
beroenden och allowlist; användaren ska bara äga sin konfig (0600).

För Ubuntu/Debian med bubblewrap och user namespaces kan IT utgå från nedan.
Installera det granskade programpaketet med sin Linux-venv under /opt/minichat.
Detta är ett separat startkommando för operatören, inte en funktion i klienten.
Katalogen /opt/minichat får inte innehålla andra hemligheter.

```sh
bwrap --unshare-all --share-net --die-with-parent --new-session \
  --cap-drop ALL \
  --ro-bind /usr /usr \
  --ro-bind /lib /lib \
  --ro-bind-try /lib64 /lib64 \
  --ro-bind /etc/ssl/certs /etc/ssl/certs \
  --ro-bind /etc/resolv.conf /etc/resolv.conf \
  --ro-bind /etc/hosts /etc/hosts \
  --ro-bind /etc/nsswitch.conf /etc/nsswitch.conf \
  --ro-bind /opt/minichat /app \
  --ro-bind "$HOME/.config/minichat/config.json" /config.json \
  --proc /proc --dev /dev \
  --clearenv --setenv PATH /usr/bin --setenv LANG C.UTF-8 \
  --chdir /app \
  /app/.venv/bin/python -I -B /app/chat.py --config /config.json --markdown
```

Värdens hemkatalog och andra användarfiler monteras inte in. Konfig, program,
bibliotek och CA-certifikat är skrivskyddade. /proc och /dev är pseudo-filsystem;
detta är inte ett påstående om noll öppna filbeskrivare eller noll skrivbara enheter.
Stdin/stdout/stderr måste finnas för terminaldialogen.

Nätverket delas för att HTTPS och DNS ska fungera. Brandväggen måste separat
begränsa utgående trafik till den interna proxyn/DNS. URL-allowlisten ersätter
inte en nätverkspolicy. Mallen installerar inte seccomp och hindrar inte en
komprometterad Pythonprocess från att exekvera läsbara program i /usr. Ett
absolut OS-förbud mot efterföljande exec kräver en separat granskad seccomp- eller
LSM-policy. Klienten själv startar aldrig en subprocess.

Verifiera på målmaskinen: konfig kan läsas, privat provfil i hemkatalogen inte
kan läsas, applikationskatalogen inte kan skrivas, TLS fungerar och utgående
trafik till andra destinationer spärras. Driftsätt inte mallen som bevisad
sandbox innan dessa kontroller gjorts. Swap, core dumps och terminalens egen
scrollback/inspelning är också värdens ansvar.

Källa: https://github.com/containers/bubblewrap
