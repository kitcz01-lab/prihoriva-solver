# 🔥 Přihořívá Solver

Autonomní sémantická aplikace a vyhledávač pro automatické luštění a hádání tajného slova dne na portálu **[prihorivahori.cz](https://prihorivahori.cz/)** a jeho sesterských mutacích (Slovensko, Polsko, Chorvatsko, Německo).

---

## 🌟 Funkce

- **Dvojí režim použití**:
  - **Moderní webové rozhraní (Web UI)**: Živý dashboard, animovaný teploměr sémantické shody (Zima ❄️ až Hoří 🏆), interaktivní tabulka s filtrováním, zvukové efekty syntetizované přes Web Audio API a ruční testovací vstup.
  - **Terminálový režim (CLI)**: Vhodný pro rychlé spuštění v konzoli, skriptování nebo automatizaci přes Cron.
- **Inteligentní sémantická heuristika**:
  - **1. Fáze (Kotevní průzkum)**: Testuje klíčové sémantické dimenze (člověk, věc, příroda, kov, dřevo, hudba, stavba, jídlo atd.).
  - **2. Fáze (Aktivace klastrů)**: Podle nejteplejších kotevních bodů aktivuje příslušné tematické domény.
  - **3. Fáze (Cílené prohledávání)**: Systematicky prochází prioritizované kandidáty.
  - **4. Fáze (Slovníková expanze)**: Fallback na korpus 28 000+ ověřených běžných českých podstatných jmen v jednotném čísle a 1. pádě. Všechna nesplňující slova (plurály, slovesa, pády 2–7) jsou striktně vyřazena.
- **Kompletní podpora jazyků a režimů**:
  - Jazyky: `cs` (Čeština), `sk` (Slovenčina), `pl` (Polština), `hr` (Chorvatština), `de` (Němčina)
  - Režimy: `daily` (denní slovo) a `mega` (týdenní mega-slovo)
- **Automatická registrace výhry**: Po odhalení slova (100% shoda) aplikace odešle potvrzení vítězství na oficiální herní backend (`/increment_correct_guesses`).
- **Nulové externí závislosti**: Čistý standardní Python 3 (není potřeba instalovat žádné `pip` balíčky).

---

## 🚀 Rychlé spuštění

### 1. Spuštění z Plochy (Desktop Launcher)
Dvojklikem na ikonu **Přihořívá Solver** na ploše (nebo v aplikačním menu):
- Automaticky spustí server na pozadí a otevře webový prohlížeč na `http://localhost:8080`.
- Pravým kliknutím na ikonu můžete vybrat další akce:
  - *Spustit v terminálu (CLI)* – otevře interaktivní řešič v okně Konsole
  - *Zastavit webový server* – ukončí běžící server na pozadí
  - *Otevřít složku projektu* – otevře adresář projektu ve správci souborů

### 2. Spuštění Webového rozhraní z terminálu
V kořenovém adresáři projektu spusťte:

```bash
python3 app.py
```

Poté otevřete ve svém prohlížeči adresu:
👉 **`http://localhost:8080`** (nebo port specifikovaný parametrem `--port`)

### 3. Spuštění v terminálu (CLI)
Pro okamžité odehrání a vypsání průběhu přímo v konzoli:

```bash
# Denní slovo v češtině
python3 app.py --cli

# Týdenní mega-hra v polštině
python3 app.py --cli --mode mega --lang pl

# Nastavení maximálního počtu pokusů a prodlevy
python3 app.py --cli --max 50 --delay 0.3
```

---

## 📁 Struktura projektu

```text
prihoriva-solver/
├── app.py              # Hlavní server (SSE streaming API & CLI rozhraní)
├── solver.py           # Algoritmus řešitele a komunikace s herním API
├── data/
│   ├── clusters.json   # Sémantické klastry a spouštěcí kotvy (vše v sg. nom.)
│   └── words_cs.json   # Frekvenčně řazená česká podstatná jména v 1. pádě sg. (28 000+ slov)
├── web/
│   ├── index.html      # Moderní HTML5 rozhraní s glassmorphismem
│   ├── style.css       # Kompletní designový systém (tmavý režim, gradienty)
│   └── app.js          # Reaktivní frontend, SSE příjem a audio syntezátor
└── README.md           # Tato dokumentace
```
