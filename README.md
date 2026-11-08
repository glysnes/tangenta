# Tangenta

Piano-øving for iPad: velg en sang, se notene på en notelinje med navnet under hver note, og følg den rosa streken. Tangenten du skal spille lyser på klaviaturet.

## Øvemåter

- **Hør**: appen spiller melodien mens streken går.
- **Vent på meg**: streken står stille til riktig tone er spilt (trykk på skjerm-tangenten, eller slå på «Lytt etter pianoet» og spill på det ekte pianoet).
- **Spill i takt**: innteller og metronom, streken går i tempo. Med mikrofonen på teller appen treff.

## Filer

- `src/tangenta.html` – selve appen. Samme fil publiseres som Claude-artefakt.
- `build.py` – bygger `docs/` (installerbar web-app med ikon og offline-støtte).
- `docs/` – det som legges på nett (GitHub Pages serverer denne mappa).

## Legge til sanger

Sanglista er `SONGS` øverst i skriptet i `src/tangenta.html`. Notespråket:

| Skriv | Betyr |
|---|---|
| `C4` | midtre C (tallet er oktaven, standard 4) |
| `:1 :2 :4 :8 :16` | hel, halv, fjerdedel (standard), åttendedel, sekstendedel |
| `G4:4.` | punktert |
| `F#4`, `Bb4` | kryss og b (B og H betyr begge den hvite tangenten under C) |
| `r`, `r:2` | pause |
| `\|` | taktstrek |

Sanger kan også legges inn i appen under **Mine sanger** (lagres på iPaden). «Kopier sangkode» gir en tekst som kan limes inn i lista her.

## Bygg

```bash
python3 build.py
```

## Legg den på iPaden

1. Åpne adressen i **Safari** på iPaden.
2. Trykk Del-knappen og velg **Legg til på Hjem-skjerm**.
3. Åpne Tangenta fra Hjem-skjermen. Den kjører i fullskjerm og virker uten nett etter første besøk.
