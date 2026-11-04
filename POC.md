# Beslutsunderlag: Proof of Concept – lokal AI för nätverksdrift och felsökning

**Version:** 1.4 – inriktning mot nätverksdrift  
**Datum:** 2026-10-13  
**Klassning:** Intern  
**Målgrupp:** Ledning, IT-säkerhetsansvarig, IT-drift och dataskyddsansvarig  
**Status:** För beslut. Föreslagna mål och säkerhetsåtgärder är inte redan uppnådda.  
**Hårdvaruinriktning:** NVIDIA DGX Spark eller jämförbar dedikerad maskin; slutligt val efter kapacitetstest och offert.

## 1. Sammanfattning och föreslaget beslut

Vi föreslår en avgränsad PoC på 6–8 veckor för att undersöka om en lokal språkmodell kan hjälpa nätverkstekniker vid felsökning och felavhjälpning. Den ska tolka godkända utdrag av loggar och kommandoutdata, skilja möjliga orsaker åt och föreslå nästa kontroll. Linux, kommandoförklaringar och teknisk dokumentation ingår där de stödjer nätverksarbetet. Användaren samlar själv in underlaget, granskar svaret och utför eventuella åtgärder.

Målet är att kunna använda godkänd intern information utan att skicka den till externa AI-tjänster. Att informationen stannar inom den beslutade interna miljön ska verifieras genom konfiguration, nätverkskontroller och tester. Det är ett godkännandekriterium, inte ett antagande om att en lokalt installerad modell automatiskt är isolerad.

Vi börjar med en ren textassistent bakom ett autentiserat HTTPS-API. Ingen agent, automatisk kommandokörning, webbsökning eller MCP ingår. Sökning i interna dokument med RAG blir en separat etapp som endast startar efter ett nytt beslut.

**Beslut som efterfrågas:** godkänn etapp 1, utse ansvariga och reservera en preliminär hårdvaruram på 70–100 kSEK samt 120–200 arbetstimmar. Beloppen är planeringsramar. Inköp kräver aktuell offert och ett dokumenterat kapacitetsunderlag; arbetstiden omfattar inte en fullständig RAG-lösning eller produktionssättning.

Efter vecka 8 fattas beslut om att avveckla, förlänga med tydligt avgränsade frågor eller förbereda nästa etapp. PoC:n får inte övergå till permanent drift utan ett uttryckligt beslut.

## 2. Vad vi vill lära oss

Det finns två sätt att misslyckas: lösningen kan vara osäker, eller så kan den vara så svag och långsam att ingen vill använda den. Därför mäter vi både nytta och säkerhet.

PoC:n ska besvara följande frågor:

- Hjälper assistenten nätverkstekniker att snabbare välja rätt nästa kontroll, avgränsa felet och återställa tjänsten, inklusive tiden för att granska svaret?
- Skiljer den mellan vad underlaget visar, vad som är en hypotes och vad som krävs för att bekräfta en rotorsak?
- Är svenska svar tydliga och tekniskt korrekta även när frågan är ofullständig?
- Fungerar tjänsten vid den samtidighet vi faktiskt behöver?
- Kan vi verifiera åtkomstkontroll, intern databehandling och en hanterbar driftkostnad?
- Finns tillräcklig nytta för att motivera intern dokumentsökning i nästa etapp?

En intern lösning förväntas inte ensam eliminera skugg-AI. Användarnas upplevelse och orsaker till att de väljer bort tjänsten ska ingå i utvärderingen.

## 3. Omfattning och avgränsningar

**Etapp 1: textassistent, 6–8 veckor.** Föreslagen pilot omfattar 5–10 nätverkstekniker. Primär plattform är **Cisco IOS**, följt av **FortiOS** och i mindre omfattning **Linux**. Modeller och exakta OS-versioner inventeras före teststart. IOS, IOS-XE och NX-OS ska hållas isär; syntax får inte antas vara utbytbar. Följande fall används för att välja pilotuppgifter, inte som ett löfte om färdig expertis inom alla områden:

| Arbetsområde | Exempel på hjälp utifrån manuellt insamlat underlag |
|---|---|
| Länk, VLAN och switching | Tolka portstatus, felräknare, VLAN/trunk och STP; föreslå observationer som skiljer möjliga orsaker |
| Routing och segmentering | Resonera om routeval, BGP/OSPF-status, VRF och fram-/returväg |
| Brandvägg, NAT och VPN | Tolka godkända policy-, sessions- och tunnelutdrag; skilja observation från förmodad blockering |
| DNS, DHCP och åtkomst | Avgränsa namnuppslagning, adressutdelning och klientåtkomst; vid behov WLAN och 802.1X |
| Prestanda och intermittenta fel | Jämföra tidpunkter, räknarförändringar, förlust, latens och MTU-relaterade hypoteser |
| Överlämning och change | Sammanfatta verifierade fynd, återstående frågor, föreslagen åtgärd, verifiering och återställning |

Assistenten ska efterfråga relevant plattform/version, trafikens källa och destination, protokoll/port, riktning, segment/VRF eller VDOM, omfattning, tidpunkt/tidszon och senaste förändring när detta saknas. Den ska prioritera ett fåtal riktade nästa steg framför långa generiska checklistor. Cisco-fallen prioriterar switching, routing och ACL:er; FortiOS-fallen prioriterar policy, NAT, sessioner och VPN. Linux används främst som klient-/serverperspektiv i felsökningen.

Tjänsten får inte ansluta till produktionssystem, läsa användarnas filer, hämta webbinnehåll, köra kommandon eller fatta operativa beslut. Lösenord, nycklar, åtkomsttoken och uppgifter som inte omfattas av pilotens databeslut får inte matas in.

Ingen SSH, SNMP, NETCONF, RESTCONF, nätverksskanning, automatisk ping/traceroute eller hämtning från övervakning/ärendehantering byggs in. Assistenten kan föreslå en mänskligt utförd kontroll och tolka dess inklistrade resultat. Binära packet captures laddas inte upp eller parsas av klienten.

**Etapp 2: RAG.** Kräver separat omfattning, budget och godkännande för dokumentkällor, behörigheter och informationshantering.

**Utanför PoC:n:** fine-tuning, agenter, MCP, automatisk felavhjälpning, bild-/ljudfunktioner, klustring och stresstest med extremt kvantiserade stora modeller. Sådana funktioner tas inte in för att de råkar finnas i en modell eller produkt.

## 4. Arkitektur och tillåtna dataflöden

Normalflödet är:

**CLI → intern HTTPS-proxy/API-policy → Ollama på localhost → lokal modell.**

Ollama kör headless på en dedikerad maskin i ett separat VLAN. Endast proxyn exponeras för pilotanvändarna. Ett begränsat API-policylager införs om den valda proxyn inte själv kan verkställa de beslutade gränserna. Det ska inte ha agentfunktioner.

| Flöde | Avsikt och begränsning |
|---|---|
| Pilotklient → proxy | HTTPS till bestämd intern adress och port; personlig autentisering |
| Proxy/API-policy → Ollama | Endast lokalt och endast de inferensanrop som behövs |
| Administrationszon → värd | Separat, begränsad administrativ åtkomst; inget administratörsgränssnitt för piloter |
| Värd → interna stödtjänster | Endast uttryckligen godkända DNS-, tids- och loggmottagare |
| Godkänd införsel → värd | Kontrollerad import av granskade modeller, paket och uppdateringar |
| Värd → internet/produktion | Nekas som standard; inga generella undantag |

En central loggmottagare utanför AI-VLAN:et måste ligga inom den godkända interna informationsmiljön. Dess åtkomst, säkerhetskopior och gallring omfattas också av PoC:n. Miljön är nätverkssegmenterad, inte ett helt frånkopplat system utan tillåtna interna flöden.

## 5. Säkerhetsgränser och behörigheter

Assistenten producerar text. Klienten saknar funktioner för verktygsanrop, kommandokörning och åtkomst till användardokument. Detta ska hållas isär från processens faktiska OS-rättigheter: Python, bibliotek, certifikat och terminal behöver viss åtkomst. Begränsningen av övrig filåtkomst måste verifieras i en separat sandbox-/OS-policy.

Klient, proxy och inferensserver körs med minsta möjliga behörighet. Klientkod och beroenden distribueras skrivskyddat för pilotanvändaren. Kryptering av lagring, hantering av swap/core dumps, patchning och fysisk åtkomst ingår i värdens härdning.

Klientens allowlist är ett extra skydd, men servern får inte lita på att användaren kör just vår klient. Servern ska själv verkställa:

- personliga identiteter/nycklar med spärrning och rotation;
- tillåtna modeller, endpoints och HTTP-metoder;
- gränser för indatastorlek, kontext, genererade token, samtidighet och kö;
- rate-limit per identitet och en global kapacitetsgräns;
- avvisning av funktioner och meddelandetyper som ligger utanför textassistenten.

Administrativa Ollama-endpoints ska inte vara nåbara genom proxyn. TLS-certifikat och hostname ska verifieras av klienten. Omdirigeringar ska inte följas och nycklar får inte förekomma i vanliga loggar.

Ollamas molnfunktioner ska stängas av med `OLLAMA_NO_CLOUD=1`, utöver nätverksspärren. Ollama dokumenterar att inställningen stänger av molnmodeller och webbsökning. [1]

## 6. Information, loggning och dataskydd

Vi skiljer mellan teknisk spårbarhet och insamling av innehåll för kvalitetsanalys.

**Audit för varje anrop:** internt användar-ID, request-ID, tidsstämpel, beslutad modellversion/konfiguration, status, latens och tillgängliga resursmått. Nycklar och autentiseringsheaders får inte loggas. Ett request-ID används för att följa anropet genom komponenterna.

**Kvalitetsmaterial:** godkända testuppgifter och särskilt beslutade pilotexempel, med prompt och svar när det behövs för bedömningen. Fullständig innehållsloggning för all fri användning är inte standard. En vanlig proxyaccesslogg uppfyller inte i sig behovet av kvalitetsanalys.

Som startförslag behålls auditmetadata högst 30 dagar och insamlade pilotkonversationer högst 14 dagar. Dessa tider är förslag, inte lagkrav. Informationsägare och dataskyddsansvarig ska före pilotstart fastställa ändamål, tillåtet innehåll, åtkomst, lagringstid, rättsliga förutsättningar och eventuellt behov av konsekvensbedömning. Lokal drift tar inte bort dataskyddsansvaret. [2]

Piloterna får tydlig information om vad som sparas och vilka som kan läsa det. Det ska finnas en rutin för felaktigt inmatade hemligheter eller personuppgifter. Terminalens scrollback, inspelning, swap och säkerhetskopior ingår i informationsbedömningen; avsaknad av klienthistorik på disk är inte samma sak som att innehåll aldrig kan lagras någonstans.

För nätverksunderlag används minsta relevanta utdrag i stället för hela konfigurationer. Ta bort exempelvis SNMP-communitysträngar, RADIUS/TACACS-hemligheter, VPN-nycklar och autentiseringsmaterial. Adressplaner, topologier, kundnamn och enhetsnamn kan också vara skyddsvärda. Ersätt dem konsekvent med alias enligt informationsägarens regler och behåll de relationer som felsökningen kräver. Klienten har ingen automatisk maskering; sanering och godkännande sker före inklistring. Om saneringen tar bort avgörande kontext ska assistenten ange begränsningen, inte gissa.

## 7. Hårdvaruval och inköpsunderlag

Vi börjar utvärderingen på redan tillgänglig utrustning med syntetiska eller uttryckligen godkända data. Resultaten används för att välja vilken dedikerad maskin som ska lånas, provas eller köpas. Känsligt pilotmaterial flyttas inte till en vanlig utvecklingsdator utan godkännande.

DGX Spark är en relevant kandidat när CUDA, Linux och möjlighet att prova flera modellstorlekar väger tungt. NVIDIA anger 128 GB unified memory, 273 GB/s minnesbandbredd och Arm-processor. Arm innebär att den exakta kombinationen av paket, containrar och inferensmotor måste verifieras. [3]

| Alternativ | Varför det ska jämföras | Vad som måste provas |
|---|---|---|
| DGX Spark 128 GB | NVIDIA-stack och stort gemensamt minne | Latens, samtidighet, Arm-kompatibilitet och faktisk modellkonfiguration |
| DGX Spark 64 GB | Lägre annonserat ingångspris | Tillgänglighet och minnesmarginal för kontext och samtidiga anrop |
| Mac Studio M5 Max/Ultra | Alternativ plattform med stort unified memory | Exakt Ollama-konfiguration, prestanda och hur macOS passar driften |
| Dedikerad GPU-workstation | Jämförelse för modeller i den aktuella storleksklassen | GPU-minne, kontextutrymme, energibehov, support och totalkostnad |

NVIDIAs öppnade amerikanska butikssida visade **6 950 USD** för DGX Spark 128 GB vid kontrollen. DGX Spark 64 GB är annonserad från **4 999 USD**, med tillgänglighet från tillverkarpartner den **23 oktober 2026**; den är alltså ännu inte lanserad vid detta dokuments datum. [4][5]

Apple har lanserat Mac Studio med M5 Max och M5 Ultra, med upp till 128 respektive 512 GB unified memory. Kapacitet och leverantörens prestandapåståenden ersätter inte ett test av vårt arbetsflöde. [6]

Modellvikter, KV-cache, runtime och parallella förfrågningar ska tillsammans rymmas med marginal. Ollama dokumenterar att parallella förfrågningar ökar kontextens minnesbehov. [1] Valet ska därför bygga på uppmätt kapacitet, svensk offert, garanti, leveranstid och support – inte enbart antal parametrar som uppges få plats.

## 8. Modeller och reproducerbara konfigurationer

Vi jämför högst tre modeller i huvudtestet. En mindre, snabb modell blir referens och jämförs med en eller två större kandidater. Ingen modell utses till vinnare före utvärderingen.

| Roll | Kandidat | Beslutsgrund |
|---|---|---|
| Primär testkandidat | Qwen3.8-27B, granskad Q4-variant | Svenska tekniska uppgifter, korrekthet, latens och runtime-stöd |
| Alternativ | Gemma 4 31B eller 26B-A4B | Samma uppgifter och samma belastningsprofil |
| Snabb referens | En redan tillgänglig, godkänd lokal modell omkring 8–14B | Om den större modellen ger tillräcklig extra nytta |
| RAG, separat etapp | bge-m3 jämfört med Qwen3-Embedding; pröva reranker | Sökprecision och latens på de egna svenska dokumenten |

Qwen3.8-27B finns med Apache 2.0-licens. Modellkortets starka kodresultat kommer delvis från agentbaserade benchmarkmiljöer; de visar inte automatiskt hur bra en Q4-version fungerar i vår svenska textassistent. Modellkortet anger också thinking som standard. Vi ska uttryckligen välja och testa svarsläge, tokenbudget och kompatibilitet i den installerade Ollama-versionen. [7]

Google listar bland annat Gemma 4 31B och 26B-A4B. Exakt variant och licens ska registreras för de nedladdade artefakterna. [8] Qwen3-Embedding och Qwen3-Reranker är jämförelsekandidater för RAG, inte beslutade ersättare för befintliga alternativ. [9]

För varje test sparas modell-ID, artefakthash, ursprung, licens, kvantisering, inferensversion, chat-template, kontextgräns, sampling och thinking-inställning. Hashar verifieras mot en betrodd referens. Beroenden och uppdateringar införs kontrollerat; flytande modelltaggar används inte som enda versionsangivelse.

## 9. Klient och användarupplevelse

CLI:n är en ren HTTP-klient med streaming, hårdkodad endpoint-allowlist, TLS-validering och dialoghistorik i minnet. Bearer-token hämtas från skyddad konfiguration eller miljövariabel. Filbaserade hemligheter kräver verifierade Linux-behörigheter.

Klienten har en fast nätverksinstruktion och stöd för flerradig inklistring med `/paste`, följt av `/end` för att skicka eller `/cancel` för att kasta blocket. Ett ärende hålls i en egen dialog; `/clear` börjar om utan föregående ärendes kontext. Ingen extra filåtkomst behövs.

Önskat svarsmönster är: **observationer → rangordnade hypoteser med stöd/motbevis → högst tre nästa kontroller och förväntade resultat → risker och eventuell återställning**. Exakt kommandosyntax ska knytas till känd plattform/version eller markeras som osäker. Även läsande kommandon kan vara resurskrävande. Debug, capture, clear/reset, omstart och konfigurationsändringar ska beskrivas med påverkan, förutsättningar, stopvillkor och verifiering innan de rekommenderas.

Nätverksinstruktionen styr önskat modellbeteende men är inte en säkerhetsgräns eller garanti för korrekt diagnos. Ett fungerande reservförfarande och ordinarie change-/incidentprocess gäller även när modellen föreslår en åtgärd. Tillfällig återställning och bekräftad rotorsak ska redovisas separat.

Valfri Markdown-rendering får inte öppna länkar, hämta bilder eller exekvera kod. Servertext ska saneras mot terminalkontrollsekvenser. Avbrutna och ofullständiga svar ska markeras som sådana. Klienten ska ge begripliga fel utan att skriva ut nycklar eller råa serverfel.

Användaren ska enkelt kunna börja om, avbryta och förstå tjänstens begränsningar. Återkoppling samlas genom ett separat internt formulär eller en bestämd pilotkanal; klienten skickar inte automatiskt konversationer någon annanstans.

Den framtagna Python-klienten är en startpunkt. Dess enhetstester och separata inferenstest ersätter inte ett godkänt end-to-end-test med faktisk HTTPS-proxy, identitet, målmodell och OS-isolering. Caddy- och sandboxexemplen i repot är driftsunderlag, inte en färdiginstallerad säkerhetslösning.

## 10. Testplan och föreslagna godkännandekriterier

Innan modelljämförelsen börjar fastställs 50–100 representativa testuppgifter med bedömningsmall och förväntade fakta. Testerna ska innehålla svenska frågor, felaktiga antaganden, ofullständig information, riskfyllda kommandoförslag och uppgifter där assistenten bör avstå eller ställa följdfrågor.

Minst två tredjedelar av uppgifterna ska komma från nätverksdrift. Använd syntetiska labbfall eller godkända, sanerade incidenter med känt facit. Ta med både ett fel åt gången och fall med flera möjliga orsaker: fel VLAN, saknad returväg, VRF-förväxling, DNS kontra transportproblem, nekad policy, tunnelproblem, MTU och intermittenta länksymtom. Detta är scenarier att utforma och validera, inte förifyllda diagnoser. Lägg till leverantörs-/versionsförväxling, gammal kommandoutdata, motstridiga observationer och inbäddade instruktioner i loggtext.

Bedöm även valet av nästa kontroll, påhittad kommandosyntax, om riskfyllda ändringar föreslås för tidigt och om modellen skiljer återställd tjänst från fastställd rotorsak. Mät tid till korrekt avgränsning i labb; använd inte en liten pilots resultat som ett bevisat mått på förbättrad MTTR i produktion. [Praktisk ärendemall och bedömningsstöd](NETWORK_WORKFLOW.md) ingår i pilotunderlaget.

Jämför med hur uppgifterna löses idag. Bedöm svar utan att visa modellnamnet när det är praktiskt möjligt. Granska kritiska och tveksamma fall med två bedömare. Mät tid till ett användbart resultat, inklusive användarens kontroll och korrigering, inte bara modellens genereringstid.

Följande är föreslagna startmål som ska beslutas före huvudtestet:

| Område | Kriterium |
|---|---|
| Kvalitet | Minst 80 % av testuppgifterna får ett användbart svar utan väsentlig korrigering enligt den fördefinierade bedömningsmallen |
| Tidsnytta | Minst 20 % lägre mediantid för de tidsmätta uppgifterna jämfört med dagens arbetssätt, inklusive granskning |
| Respons | Vid varm modell och tre samtidiga användare: p95 högst 5 sekunder till första synliga svarstext, exklusive separat thinking-text |
| Svarstid | För fast testprofil med högst 8k indatatoken och 300 genererade token: p95 högst 60 sekunder till färdigt svar |
| Belastning | Test vid 1, 3 och 5 samtidiga användare; kö, avvisning, minne och latens redovisas, även när målen inte nås |
| Säkerhet | Inga observerade kritiska åtkomst-, exekverings- eller dataläckagefel i den beslutade testsviten |
| Användbarhet | Minst 70 % av piloterna vill fortsätta för minst ett definierat användningsfall; antal svar och bortfall redovisas |

Kallstart, långa sessioner och olika thinking-lägen mäts separat. Otillräckligt antal mätningar redovisas som osäkert underlag. Noll upptäckta fel i en testsvit är inte bevis för att alla risker är eliminerade.

Säkerhetstesterna omfattar felaktig/spärrad nyckel, obetrodd CA, fel hostname, redirect, överstora anrop, kööverlast, avbruten streaming, terminalkontrollsekvenser, kringgående med annan HTTP-klient och försök till otillåten nätverkstrafik. Verifiera även att klientprocessen inte kan läsa skyddade provfiler och att förbjuden exekvering stoppas av den valda OS-policyn.

## 11. RAG och eventuell framtida MCP

RAG används i nästa etapp för att hämta relevanta dokumentutdrag till modellen. Fine-tuning ingår inte; behovet är åtkomst till aktuella, spårbara fakta.

Före RAG-start ska följande vara beslutat och testbart:

- godkända dokumentkällor, informationsägare och tillåtna användargrupper;
- autentiserad identitet hela vägen till sökningen, utan att lita på klientangivna behörigheter;
- behörighetskontroll innan dokumentinnehåll lämnas till modellen;
- versioner, källhänvisningar, indexuppdatering, radering och hantering av ändrade behörigheter;
- isolering av dokument, cache, konversationer och loggar mellan användare;
- tester av felaktiga källor, uteblivna träffar och instruktioner gömda i dokument.

Prioritera versionsmärkta runbooks, godkända standardkonfigurationer och sanerade incidentrapporter. Ange leverantör, produkt, OS-version, dokumentägare och granskningsdatum som metadata. Historiska topologier eller konfigurationer får inte presenteras som aktuellt nätläge. Automatisk anslutning till övervakning, CMDB eller utrustning ligger fortsatt utanför och kräver eget beslut.

Dokument ska behandlas som opålitlig data. RAG och en instruktion i systemprompten eliminerar inte prompt injection. Behörigheter ska upprätthållas av applikationen, inte av modellens bedömning. OWASP beskriver särskilda risker och kontroller för RAG. [10]

MCP är ett protokoll, inte en säkerhetsklassning. Även läsande verktyg kan hämta otillåten information eller påverka svar. Modellstyrda verktygsanrop kräver en egen riskbedömning och ett separat beslut; de ingår inte automatiskt efter godkänd RAG.

## 12. Drift, ansvar och incidenter

Före pilotstart utses en beslutsägare, tjänsteägare, driftansvarig, säkerhetsansvarig, informationsägare och ansvarig för kvalitetsutvärdering. Dataskyddsansvarig involveras i informationshanteringen. En person kan ha flera roller, men ansvar får inte lämnas implicit.

Driftplanen ska omfatta patchning, kontrollerad modelluppdatering, regressionstester, nyckelrotation, övervakning, återställning och möjlighet att gå tillbaka till en tidigare godkänd version. Loggkedjan ska övervakas; fel i den får inte passera obemärkt. För pilotstart krävs fungerande audit. Vid auditbortfall pausas tjänsten tills spårbarheten är återställd.

Ett kritiskt fynd leder till omedelbar paus av berörd funktion, spärrning av relevanta nycklar och dokumenterad incidenthantering. Felaktigt inmatade hemligheter behandlas som potentiellt röjda; enbart radering av konversationen räcker inte.

Tjänsten är en pilot utan produktions-SLA och får inte bli ett nödvändigt beroende för ordinarie drift.

## 13. Tidplan och budget

| Period | Leverans och beslut |
|---|---|
| Vecka 1 | Fastställ uppgifter, mätmål, informationsregler och ansvar; börja jämföra på befintlig utrustning |
| Vecka 2 | Kapacitetsprov, aktuell offert och beslut om dedikerad hårdvara; leveranstid kan påverka kalendern |
| Vecka 3–4 | Sätt upp isolering, autentisering, servergränser och audit; genomför tekniskt acceptanstest |
| Vecka 5–6 | Begränsad användarpilot och blindad kvalitets-/tidsutvärdering |
| Vecka 7–8 | Åtgärda avgränsade brister, repetera relevanta tester och sammanställ beslutsunderlag |

Preliminär hårdvaruram är **70–100 kSEK**, med momsstatus, leverans, garanti och support uttryckligen angivna i offerten. Ingen svensk slutkostnad härleds enbart från amerikanska listpriser.

Planeringsramen **120–200 arbetstimmar** avser etapp 1 med tydlig avgränsning. Den ska brytas ned på implementation, säkerhet, drift, test och pilotstöd. Redovisa separat piloternas tid, internt timpris, löpande förvaltning och eventuella licens-/supportkostnader. RAG och produktionssättning kräver egen kalkyl.

Om budget eller tid inte räcker minskas omfattningen eller så fattas ett nytt beslut. Säkerhetskraven tas inte bort för att hålla en demonstrationsdeadline.

## 14. Stoppkriterier och avveckling

Piloten pausas direkt vid observerat kritiskt dataläckage, obehörig åtkomst, otillåten exekvering eller förlorad kontroll över autentisering och audit. Berörd funktion återstartas först efter åtgärd och verifiering.

Projektet föreslås avvecklas eller omprövas om kvalitets-/nyttomålen inte nås efter den avtalade förbättringsomgången, om nödvändig kapacitet överskrider budgeten eller om ingen kan ta långsiktigt driftansvar.

**Avveckling på en arbetsdag** betyder att användaråtkomst stoppas, nycklar spärras, tjänster stängs och berörda nätverksregler avvecklas. Det betyder inte att alla säkerhetskopior kan garanteras fysiskt raderade samma dag. Index, loggar, konfigurationer och eventuella säkerhetskopior hanteras enligt dokumenterad gallring, med ansvarig och sista datum. En avvecklingsrapport bekräftar vad som är borttaget och vad som tillfälligt måste behållas.

## 15. Beslutspunkter

| Grind | Underlag som krävs | Möjliga beslut |
|---|---|---|
| Start av etapp 1 | Godkänd omfattning, ansvariga, mål och planeringsram | Starta eller återremittera |
| Hårdvaruinköp | Kapacitetsunderlag, aktuell offert och driftkompatibilitet | Köpa, låna/prova vidare eller avstå |
| Start av användarpilot | Godkända säkerhetstester, databeslut, audit och användarinformation | Öppna begränsad pilot eller åtgärda |
| Slut på etapp 1 | Redovisad kvalitet, tidsnytta, säkerhet, kostnad och användarrespons | Avveckla, förlänga avgränsat eller planera nästa etapp |
| Start av RAG | Egen plan för källor, behörigheter, tester, drift och budget | Starta separat etapp eller avstå |

**Rekommendation:** genomför en avgränsad assistentpilot och låt resultaten styra fortsatt investering. Behåll mänsklig granskning, serverkontroller och verifierad isolering som fasta krav genom hela försöket.

## Källor och kontrollstatus

Leverantörskällorna nedan kontrollerades 2026-10-12. Pris och tillgänglighet kan förändras. Källorna styrker produktuppgifter och dokumenterade funktioner; de styrker inte att vår miljö redan uppfyller kraven eller att en viss modell vinner våra tester.

1. [Ollama FAQ – lokal drift, molnavstängning och samtidighet](https://docs.ollama.com/faq)
2. [IMY – vägledning om GDPR och AI](https://www.imy.se/verksamhet/dataskydd/innovationsportalen/vagledning-om-gdpr-och-ai/)
3. [NVIDIA – DGX Spark och tekniska specifikationer](https://www.nvidia.com/en-us/products/workstations/dgx-spark/)
4. [NVIDIA Marketplace – DGX Spark 128 GB](https://marketplace.nvidia.com/en-us/enterprise/personal-ai-supercomputers/dgx-spark/)
5. [NVIDIA, 2 oktober 2026 – DGX Spark 64 GB, annonserad till 23 oktober](https://blogs.nvidia.com/blog/local-ai-dgx-spark-64gb-sync/)
6. [Apple, 25 augusti 2026 – Mac Studio med M5 Max och M5 Ultra](https://www.apple.com/newsroom/2026/08/apple-introduces-new-mac-studio-with-m5-max-and-m5-ultra/)
7. [Qwen – officiellt modellkort för Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)
8. [Google DeepMind – Gemma 4](https://deepmind.google/models/gemma/gemma-4/)
9. [Qwen – officiellt projekt för Qwen3-Embedding och Qwen3-Reranker](https://github.com/QwenLM/Qwen3-Embedding)
10. [OWASP – RAG Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html)
