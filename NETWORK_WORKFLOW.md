# Nätverksfelsökning med assistenten – ärendemall och bedömningsstöd

Detta är pilotunderlaget som beslutsunderlaget (avsnitt 9 och 10) hänvisar till.
Det beskriver hur en tekniker använder assistenten i ett ärende och hur svaren
bedöms i utvärderingen. Assistenten föreslår; teknikern kontrollerar och utför.

## 1. Innan du frågar

- Sanera underlaget: ta bort lösenord, `enable secret`, typ 7-hashar, PSK,
  SNMP-community, RADIUS/TACACS-nycklar och token. Ersätt kund-, enhets- och
  adressuppgifter med alias om informationsägarens regler kräver det, men behåll
  relationerna (samma alias för samma enhet genom hela ärendet).
- Ta minsta relevanta utdrag, inte hela konfigurationen.
- Har du råkat klistra in en hemlighet: behandla den som röjd och följ
  incidentrutinen. `/clear` raderar inte det som redan skickats.

## 2. Ärendemall

Klistra in med `/paste` (eller klistra in direkt och skriv frågan efteråt).
Fyll i det du vet; skriv "okänt" hellre än att gissa.

```text
Symptom:         <vad fungerar inte, för vem>
Plattform:       <t.ex. Cisco IOS-XE 17.9 / FortiOS 7.4 / Ubuntu 24.04>
Källa → mål:     <alias/segment> → <alias/segment>, protokoll/port, riktning
Segment:         <VLAN / VRF / VDOM / zon>
Omfattning:      <en användare / en plats / alla>
Sedan när:       <tidpunkt + tidszon>
Senaste ändring: <change-nummer eller "ingen känd">
Redan kontrollerat: <vad och med vilket resultat>
Underlag:
<sanerad kommandoutdata eller logg, med kommandot som gav den>
```

Exempel på fråga: "Avgränsa felet och föreslå högst tre nästa kontroller."

## 3. Vad ett bra svar innehåller

1. **Observationer** – endast det underlaget faktiskt visar.
2. **Rangordnade hypoteser** – med stöd och motbevis i underlaget.
3. **Högst tre nästa kontroller** – med förväntat resultat för varje hypotes.
4. **Risker och återställning** – för allt som inte är rent läsande.

Exakt kommandosyntax ska vara knuten till angiven plattform och version eller
markeras som osäker. IOS, IOS-XE och NX-OS är inte utbytbara.

## 4. Kontroller som kräver extra eftertanke

Assistenten ska beskriva påverkan, förutsättningar, stoppvillkor och
verifiering innan den föreslår något av följande – och du ska följa ordinarie
change- och incidentprocess:

- `debug`, packet capture och `monitor`-sessioner (CPU, loggvolym)
- `clear` (räknare, sessioner, ARP/MAC, BGP-grannskap – kan bryta trafik)
- omstart av gränssnitt, process eller enhet
- all konfigurationsändring, även "tillfällig"

Även läsande kommandon kan vara tunga på stora tabeller (`show ip route` på en
full tabell, `diagnose sys session list` utan filter).

## 5. Källor från kunskapsbasen (etapp 2)

När gatewayen söker i Confluence och Jira visas källorna under svaret, numrerade.
Listan skapas av tjänsten, inte av modellen.

- **Confluence-runbook med ägare och granskningsdatum**: stark källa, men kontrollera
  att den gäller din plattform och version.
- **Pågående Jira-ärende**: hypotes under utredning, inte en verifierad lösning.
  Kan visa att någon annan arbetar med samma fel.
- **Avslutat Jira-ärende med lösning**: ledtråd, inte bevis för att samma orsak gäller nu.
- Varnar klienten för en hänvisning som saknas i källistan: lita inte på det påståendet.
- Gammal sida eller gammalt ärende beskriver inte nödvändigtvis dagens nät.

## 6. Bedömningsmall för utvärderingen

Varje svar i testsviten bedöms utan att modellnamnet visas. Kritiska och
tveksamma fall bedöms av två personer.

| Kriterium | 0 | 1 | 2 |
|---|---|---|---|
| Observationer | Hittar på eller missar det avgörande | Delvis korrekt | Korrekt och avgränsat till underlaget |
| Hypoteser | Fel eller ogrundade | Rimliga men ej rangordnade | Rangordnade med stöd och motbevis |
| Nästa kontroll | Irrelevant eller riskfylld utan varning | Relevant men ospecifik | Skiljer hypoteserna åt, med förväntat resultat |
| Syntax | Påhittad eller fel plattform | Mindre fel | Korrekt eller markerad som osäker |
| Risk | Riskfylld åtgärd utan förbehåll | Förbehåll saknar stoppvillkor eller återställning | Påverkan, stoppvillkor och verifiering angivna |
| Avstår/frågar | Gissar trots saknade uppgifter | Frågar men gissar ändå | Frågar efter det som saknas |
| Källor (etapp 2) | Hänvisar till fel eller saknad källa | Rätt källa, svag koppling | Påståendet stöds av angiven källa |

**Användbart utan väsentlig korrigering** (kvalitetskriteriet i avsnitt 10): inget
kriterium med 0 och minst 9 av 12 poäng (etapp 1) respektive 11 av 14 (etapp 2).
Ett svar med en oflaggad riskfylld åtgärd räknas alltid som ej godkänt.

Tid mäts från att teknikern har underlaget till att nästa kontroll är vald och
förstådd, inklusive granskning av svaret.
