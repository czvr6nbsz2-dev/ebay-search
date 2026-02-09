# Apple Shortcut: "Zoek Fotoapparatuur"

## Snelle setup (5 minuten)

### Stap 1: Open de Shortcuts-app op je iPhone of Mac

### Stap 2: Maak een nieuwe Shortcut met de naam "Zoek Fotoapparatuur"

### Stap 3: Voeg deze acties toe (in volgorde):

---

**Actie 1: Vraag om invoer**
- Type: Tekst
- Vraag: "Wat zoek je?"

**Actie 2: URL**
- `https://api.github.com/repos/czvr6nbsz2-dev/ebay-search/actions/workflows/search.yml/dispatches`

**Actie 3: Haal inhoud van URL op**
- Methode: POST
- Headers:
  - `Authorization`: `Bearer JOUW_GITHUB_PAT_HIER`
  - `Accept`: `application/vnd.github+json`
- Request body: JSON
  - `ref`: `main`
  - `inputs`: woordenboek met key `description`, waarde: **Opgegeven invoer** (van stap 1)

**Actie 4: Wacht**
- 90 seconden

**Actie 5: URL**
- `https://api.github.com/repos/czvr6nbsz2-dev/ebay-search/issues?labels=zoekresultaten&sort=created&direction=desc&per_page=1`

**Actie 6: Haal inhoud van URL op**
- Methode: GET
- Headers:
  - `Authorization`: `Bearer JOUW_GITHUB_PAT_HIER`
  - `Accept`: `application/vnd.github+json`

**Actie 7: Haal waarde op uit woordenboek**
- Sleutel: eerste item uit de lijst
- Dan: Haal `body` op uit dat item

**Actie 8: Maak notitie**
- Inhoud: de body uit stap 7
- Map: Notities

---

### Stap 4: Klaar!
Tik op "Zoek Fotoapparatuur" in de Shortcuts-app, typ wat je zoekt, en na ~90 seconden verschijnt het resultaat in je Apple Notities.
