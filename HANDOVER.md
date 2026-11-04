# HANDOVER.md

Överlämning mellan agenter och sessioner. Läs innan du börjar, uppdatera innan du slutar.

## Aktuellt läge

*Senast inventerat 2026-11-04 av Claude (Cowork).*

Projekt: En liten Linux-klient för Ollamas OpenAI-kompatibla streaming-API. Modellen producerar bara text. Klienten har inga verktyg, subprocesser, shellfunktioner, filuppladdningar, webbläsning eller diskhistorik. Modellens kommandoförslag granskas och kopieras manuellt av användaren.

- Huvudbranch: `main`
- Senaste commit på `main`: 2026-11-01 `33c7fac` Add privacy guard checks (#1)
- Öppna PR:er: 0
- Andra brancher på remote: 2

## Pågående arbete

| Agent/vem | Branch | Status | Beskrivning |
|-----------|--------|--------|-------------|
| Cursor | `cursor/privacy-guard-02f2` | branch utan PR, senaste commit 2026-11-01 | Add privacy guard checks |
| Claude | `pilotkrav-paste-kallor` | branch utan PR, senaste commit 2026-10-15 | Use English command names |

## Nästa steg

- Gå igenom brancher utan PR: öppna PR, merga eller radera (fråga användaren innan radering).
- Fyll på "Bygga och testa" i AGENTS.md om något saknas eller är fel.

## Kända problem

- Inga dokumenterade ännu.

## Senaste commits

- 2026-11-01 `33c7fac` Add privacy guard checks (#1)
- 2026-10-15 `3bc0ee9` Use English command names
- 2026-10-15 `5924c79` Add multi-line paste, knowledge-base sources and pilot documents
- 2026-10-12 `d71b58e` Add minimal Ollama streaming CLI with security checks and tests

## Logg

| Datum | Agent | Vad som gjordes |
|-------|-------|-----------------|
| 2026-11-04 | Claude (Cowork) | Lade till AGENTS.md, HANDOVER.md och CLAUDE.md; inventerade PR:er, brancher och commits. |
