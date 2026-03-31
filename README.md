# 🚗 Grille

**Grille** is a daily car guessing game — think Wordle, but for cars. Every day a new car is chosen. You have 5 guesses to identify it using colour-coded feedback on Make, Model, Year, Country, Horsepower, and Weight. The car image progressively reveals itself the more guesses you use.

Play it live → **[GitHub Pages](https://everchanger.github.io/grille/)**

---

## Features

- 🗓 **Daily puzzle** — same car for everyone worldwide, resets at midnight UTC
- 🔍 **Autocomplete search** — type any make, model, or year to find a car
- 🎨 **Progressive image reveal** — blurred → clearer → full colour
- 📊 **Statistics** — track wins, streaks, and guess distribution
- 📋 **Share** — copy a spoiler-free emoji grid to your clipboard
- ⚖️ **Unit toggle** — switch between kg and lbs (auto-detected from browser locale)
- 💾 **No account needed** — all state stored locally in your browser

---

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Framework   | [Nuxt 3](https://nuxt.com) (SPA, SSR disabled) |
| Styling     | [Tailwind CSS](https://tailwindcss.com) via `@nuxtjs/tailwindcss` |
| Language    | TypeScript                        |
| Data        | Static JSON (`data/cars.json`)    |
| State       | `localStorage` (no backend)       |
| Deployment  | GitHub Pages via GitHub Actions   |

---

## Project Structure

```
grille/
├── app.vue                   # Root component
├── pages/
│   └── index.vue             # Main game page
├── components/
│   ├── CarImage.vue          # Progressive image reveal
│   ├── ClueGrid.vue          # 5-row guess grid
│   ├── GrilleLogo.vue        # Animated SVG logo
│   ├── GuessInput.vue        # Autocomplete search input
│   ├── GuessRow.vue          # Single feedback row
│   ├── HowToPlay.vue         # How-to-play instructions overlay
│   ├── ResultDetails.vue     # Win/lose reveal panel
│   └── StatsModal.vue        # Statistics overlay
├── composables/
│   ├── useGame.ts            # Core game logic
│   ├── useStorage.ts         # localStorage persistence
│   └── useUnits.ts           # kg/lbs toggle
├── data/
│   ├── cars.json             # Car database (~375 cars)
│   └── cars-wikidata.json    # Raw Wikidata fetch output
├── types/
│   └── index.ts              # TypeScript interfaces
├── utils/
│   ├── carLabel.ts           # Car display label helper
│   └── useAssetUrl.ts        # Asset URL resolution
├── tests/
│   ├── carLabel.test.ts
│   ├── dateNavigation.test.ts
│   ├── useAssetUrl.test.ts
│   ├── useGame.test.ts
│   ├── useStorage.test.ts
│   └── useUnits.test.ts
├── scripts/
│   ├── fetch-cars.py         # Wikipedia car data fetcher
│   ├── seed-cars.py          # Curated seed car data
│   ├── test_fetch_cars.py    # Tests for fetch-cars.py
│   └── test_seed_cars.py     # Tests for seed-cars.py
├── public/
│   └── cars/                 # Car images (.webp)
├── nuxt.config.ts
├── tailwind.config.ts
├── vitest.config.ts
└── .github/workflows/
    ├── deploy.yml            # CI/CD → GitHub Pages
    └── fetch-cars.yml        # Automated car data refresh
```

---

## Getting Started

### Prerequisites

- Node.js 22+
- npm 10+

### Install & Run

```bash
npm install
npm run dev
```

Open [http://localhost:3000/grille/](http://localhost:3000/grille/)

### Build & Generate

```bash
# Static site generation (for deployment)
npm run generate

# Preview the generated output
npm run preview
```

### Run Tests

```bash
# TypeScript tests
npx vitest run

# Python script tests
python -m pytest scripts/test_fetch_cars.py scripts/test_seed_cars.py -v
```

---

## Adding Cars

Cars are sourced automatically via `scripts/fetch-cars.py` which pulls data from Wikipedia. To add cars manually, edit `data/cars.json`:

```jsonc
{
  "id": 11,
  "make": "Honda",
  "model": "NSX (NA1)",
  "year": 1990,
  "country": "Japan",
  "horsepower": 270,
  "weight_kg": 1370,
  "engine": "V6",
  "drivetrain": "RWD",
  "image": "/cars/honda-nsx-na1.webp",
  "fact": "...",
  "wiki": "https://en.wikipedia.org/wiki/Honda_NSX"
}
```

Place the corresponding `.webp` image in `public/cars/`. The daily puzzle cycle automatically extends.

---

## Deployment

The site deploys automatically to GitHub Pages on every push to `main` via the workflow in `.github/workflows/deploy.yml`. To set up on your fork:

1. Go to **Settings → Pages** in your repository
2. Set source to **GitHub Actions**
3. Update `app.baseURL` in `nuxt.config.ts` to match your repo name if different from `/grille/`
4. Push to `main`

---

## Game Design

See [GAME_DESIGN.md](./GAME_DESIGN.md) for the full design document covering answer selection, feedback rules, image reveal states, persistence, and sharing.