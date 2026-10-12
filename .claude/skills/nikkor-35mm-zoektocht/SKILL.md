---
name: nikkor-35mm-zoektocht
description: Wekelijkse zoektocht naar een schone Nikkor 35mm f/1.4 AI of AI-S (de lens, ook als combinatie met FM2, FE2, FM3a, D700, D850, D200 of D80) bij particulieren, Nederlandse winkels, eBay en Marktplaats, met een gebrekcontrole op de advertentietekst. Gebruik dit bij "zoek de Nikkor 35mm", "wekelijkse zoektocht" of "35/1.4 check".
---

# Nikkor 35mm f/1.4 AI / AI-S zoektocht

## Doel

Een schone Nikkor 35mm f/1.4 AI of AI-S vinden tegen een effectieve prijs onder €595, het bedrag dat een Duitse handelaar met een jaar garantie vraagt. Liefst in Nederland, zodat de lens zelf tegen het licht kan worden gehouden.

## Harde regels

- **Zoek de lens, niet de camera.** Camera's worden alleen meegerekend als de lens erbij wordt aangeboden.
- **Geen nevel, schimmel of balsemscheiding.** Die vallen af, met de letterlijke zin erbij. Lichte krassen of een stofje zijn acceptabel.
- **Verzendt naar Nederland.** Het filter doet dat via `deliveryCountry:NL`.
- **Verkocht is geen voorraad.** Fotohandel Delfshaven laat verkochte artikelen online staan met "Price: Sold". Die vallen eruit.
- **Geen andere f/1.4-lenzen.** Uitsluiten: 5 cm, 5,8 cm, Nikkor-S, rangefinder, Z-mount, TTArtisan, Voigtländer en de andere merken uit de lijst hieronder.
- **Pre-AI is geen AI.** Nikkor-N Auto en N.C Auto passen niet veilig op een FE2 of D700 zonder conversie. Noem dat erbij als ze langskomen.

## Stap 1: zoekopdracht starten

Verstuur deze aanvraag met de GitHub-client. De vijf velden na `||` zijn: titel, zoektermen, verplichte termen, uitsluitingen, en de EN-eis.

```bash
cat > /tmp/zoek.json <<'JSON'
{"ref":"claude/nikon-fe2-price-comparison-CHETT","inputs":{"description":"Nikkor 35mm f1.4 AI - wekelijks || nikkor 35mm 1.4, nikkor 35mm 1:1.4, nikon 35mm 1.4 ai, nikkor 35mm f1.4 ais, nikon fm2 35mm 1.4, nikon fe2 35mm 1.4, nikon 35mm 1.4 weitwinkel || 35mm, 35 mm, /35 || 24mm, 28mm, 50mm, 55mm, 58mm, 85mm, 105mm, 135mm, 180mm, 200mm, 20mm, 18mm, 45mm, 5cm, 5.8cm, 3.5cm, 50, 55, 58, rangefinder, eye level, nikkor-s, s.c, s auto, 24-70, 35-70, 35-105, 28-105, 28-85, 35-80, 70-300, zoom, f/2, f2, 1:2, 2.0, 2,0, f/2.8, f2.8, 1:2.8, 2.8, 2,8, f/1.8, 1:1.8, 1.8, f/3.5, 1:3.5, 3.5, af-s, afs, af-d, 1.4g, g ed, nano, nikon z, nikkor z, z-mount, z mount, voigtlander, nokton, thypoch, simera, zeiss, distagon, ttartisan, ttartisans, canon, sony, sigma, tamron, minolta, pentax, olympus, leica, contax, konica, m42, fujifilm, samyang, viltrox, 7artisans, mir, helios, jupiter, filter, hood, gegenlicht, sonnenblende, deckel, cap, tasche, huelle, case, adapter, akku, batter, boek, book, buch, anleitung, prospekt, katalog, gezocht, gesucht, defect, defekt, parts, spares, broken, kaputt, repair, junk, fungus, schimmel, pilz, haze, nebel, dunst, kratzer, scratch || 35mm | 35 mm | /35 ; 1.4 | 1:1.4 | f/1.4 | f1.4 | 1,4"}}
JSON

gh api -X POST repos/czvr6nbsz2-dev/ebay-search/actions/workflows/search.yml/dispatches --input /tmp/zoek.json
```

De branch `claude/nikon-fe2-price-comparison-CHETT` is belangrijk. Daar staan de code voor Marktplaats, Kleinanzeigen en de winkels. Op `main` staat die niet.

## Stap 2: wachten

Wacht ongeveer vier minuten met een achtergrond-sleep. Gebruik geen herhaald pollen.

## Stap 3: resultaat ophalen

Het resultaat verschijnt als nieuwe comment op issue 5. Haal alleen de laatste op:

```bash
N=$(gh api repos/czvr6nbsz2-dev/ebay-search/issues/5 --jq '.comments')
gh api "repos/czvr6nbsz2-dev/ebay-search/issues/5/comments?per_page=1&page=$N" --jq '.[0].body' > /tmp/resultaat.md
```

Lees het bestand niet in zijn geheel. Het bevat honderden eBay-regels. Filter op regels die beginnen met `| Marktplaats`, `| Kleinanzeigen` of `| Fotohandel`, plus alle Europese regels onder €595. De kolommen zijn: Regio | Land | Prijs | Staat | Verkoper | FB% | Gebreken | Titel | URL.

## Stap 4: beoordelen

1. **Is het echt een 35/1.4 AI of AI-S?** Veel ruis: f/2, f/2.8, Nikkor Z, en camera's met een andere f/1.4-lens.
2. **Gebreken.** Staat er nevel, schimmel of balsemscheiding in de kolom Gebreken? Dan afkeuren, met de letterlijke zin uit de sectie "Gevonden gebreken" onderaan het bestand.
3. **Camera-combinaties.** Trek de waarde van de body van de vraagprijs af en noem de effectieve lensprijs. Referentiewaarden, gemeten in oktober 2026:
   - Nikon D700: €250. De gebruiker betaalt er hooguit €300 voor.
   - Nikon D850: €1400. De mediaan ligt op €1679; alles daaronder is scherp.
   - Nikon D200: €100. Mediaan €208, maar regelmatig voor €60–99.
   - Nikon D80: €80. Mediaan €183 wordt opgedreven door kits.
   - Nikon FM2: €250. FE2: €250. FM3a: €800. F3: €200.
   - Andere body's (D750, D800, D90, Z-serie en dergelijke): nul. Die wil de gebruiker niet.
4. **Prijs.** Effectief onder €595, schoon, en liefst in Nederland.

## Stap 5: rapporteren

Nederlands, kort en zakelijk, zonder opsmuk.

- **Iets schoons gevonden:** een compacte tabel met prijs, land, verkoper, gebreken en titel, plus de volledige URL. Voeg twee zinnen toe over of het de moeite waard is tegenover €595 bij een handelaar. Bij een combinatie: noem de effectieve lensprijs en welke body erbij zit.
- **Niets gevonden:** één of twee zinnen. Geen tabel met ruis. Dat is de meeste weken normaal.
- **Verkocht bij Fotohandel Delfshaven:** "niets leverbaar: alle N treffers staan als verkocht". Dat is geen storing en hoeft niet gemeld te worden.

## Storingen versus geen treffers

Onderscheid die twee altijd.

- **Geen treffers, geen storing:** "geen /s-anzeige/-links" met een lege-resultatenpagina, "niets leverbaar: alle N treffers staan als verkocht", of een lege WooCommerce-zoekpagina.
- **Echte storing:** "geen productlinks herkend" bij een pagina die wel resultaten lijkt te bevatten, "geen /s-anzeige/-links op de pagina" zonder een lege-resultatentekst, of "geen 'listings' in JSON". Meld die expliciet, met de bron en de letterlijke diagnose, zodat de scraper gerepareerd kan worden.

## Bekende beperkingen

- Kleinanzeigen en Fotohandel Delfshaven zijn vanuit de sessie-omgeving soms niet bereikbaar. Dan is de uitkomst "niet op te halen", niet "niets gevonden".
- De gebrekcontrole werkt op de tekst van de verkoper. Een foto tegen het licht blijft nodig voordat er gekocht wordt.
