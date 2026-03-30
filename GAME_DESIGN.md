# Grille — Game Design Document

## 1. Overview

Grille is a daily browser-based car guessing game inspired by Wordle and Heardle. Each day, a new iconic car is selected as the answer. Players have up to 5 guesses to identify it. After each guess, colour-coded feedback is shown for six attributes: Make, Model, Year, Country, Horsepower, and Weight. A progressive image reveal rewards persistence — the longer you play, the more of the car's image you can see.

The game resets at midnight UTC. Progress is persisted in `localStorage` so players can close the tab and return. Statistics are tracked across sessions.

---

## 2. Core Gameplay Loop

1. The player opens the game and sees a hidden/silhouetted car image plus an empty 5-row guess grid.
2. The player types a car name into the search input and selects from the autocomplete dropdown.
3. The guess is submitted and a row of coloured feedback tiles is added to the grid.
4. The image progressively reveals itself based on how many guesses have been made.
5. The player continues guessing until they identify the car (win) or exhaust all 5 guesses (lose).
6. A post-game panel reveals the full car image, details, a fun fact, a Wikipedia link, and a share button.

---

## 3. Answer Selection

- Cars are stored in `data/cars.json` as a static array of ~375 vehicles (automatically refreshed via `scripts/fetch-cars.py`).
- The daily answer is determined deterministically: `cars[dayNumber % cars.length]`, where `dayNumber` is the number of days elapsed since the epoch `2025-01-01T00:00:00Z` in UTC.
- This ensures every player worldwide sees the same puzzle on the same UTC day, with no server required.
- As the car list grows, the cycle lengthens and past answers repeat less frequently.

---

## 4. Guess Feedback System

Each guess produces a `GuessFeedback` object with six fields. The feedback rules are:

| Field       | Correct         | Close                                  | Higher / Lower                        | Wrong          |
|-------------|-----------------|----------------------------------------|---------------------------------------|----------------|
| **Make**    | Exact match     | Same country of origin                 | —                                     | No match       |
| **Model**   | Exact match     | —                                      | —                                     | No match       |
| **Year**    | Exact match     | —                                      | Guess too low → **Higher** / too high → **Lower** | —     |
| **Country** | Exact match     | Same continent                         | —                                     | No match       |
| **HP**      | Exact match     | Within ±15% of answer                  | Guess too low → **Higher** / too high → **Lower** | —     |
| **Weight**  | Exact match     | Within ±10% of answer                  | Guess too low → **Higher** / too high → **Lower** | —     |

Visual encoding of feedback tiles:

| Result  | Colour        | Icon |
|---------|---------------|------|
| correct | Green (`bg-green-600`) | ✅ |
| close   | Yellow (`bg-yellow-500`) | 🟡 |
| higher  | Gray + arrow  | 🔼  |
| lower   | Gray + arrow  | 🔽  |
| wrong   | Gray          | ❌  |

A guess is fully correct (win condition) only when **all six** fields return `'correct'`.

---

## 5. Progressive Image Reveal

The car image changes based on the number of guesses submitted:

| Guesses Used | Image State  | Description                                  |
|--------------|--------------|----------------------------------------------|
| 0–1          | `none`       | No image — placeholder car emoji shown       |
| 2–3          | `silhouette` | Image rendered with `brightness(0) contrast(1)` — solid black silhouette |
| 4–5          | `blurred`    | Image rendered with `blur(12px)` — vague shape visible |
| 5 / solved / failed | `full` | Full colour image displayed               |

This mechanic rewards players who identify the car quickly, and provides a tension ramp as more guesses are used.

---

## 6. Autocomplete Search

- The `GuessInput` component provides a live-filtering dropdown.
- Matches any car where the combined `make + model + year` string contains the query (case-insensitive).
- Already-guessed cars are excluded from suggestions (filtered by `guessedIds`).
- Selecting an item emits a `guess` event with the formatted string `"Make Model (Year)"`.
- Pressing **Enter** auto-selects the first suggestion; pressing **Escape** clears the input.
- Up to 8 suggestions are shown at once.

---

## 7. Unit Toggle

- Weight can be displayed in **kg** or **lbs** (converted via `kg × 2.205`, rounded to nearest integer).
- The default unit is inferred from `navigator.language`: `en-US` → lbs, everything else → kg.
- The toggle button in the header switches between units and persists the setting in `localStorage` under the key `grille_settings`.
- The `useUnits` composable provides `unit`, `toggleUnit`, and `formatWeight(kg)`.

---

## 8. Persistence & State

All game state is stored client-side in `localStorage`. No backend is required.

| Key                          | Contents                          |
|------------------------------|-----------------------------------|
| `grille_state_YYYY-MM-DD`    | Today's `GameState` (guesses, results, solved/failed flags) |
| `grille_stats`               | Lifetime `StatsState` (played, wins, streaks, distribution) |
| `grille_settings`            | `SettingsState` (unit preference) |

- Game state keys are date-scoped so yesterday's progress does not interfere with today's puzzle.
- On load, `useStorage.loadGameState()` reads today's key; if missing, a fresh `defaultGameState` is returned.
- Stats are updated immediately when the game is won or lost.

---

## 9. Statistics & Sharing

**Statistics Modal** (opened via the 📊 button):
- Played, Win %, Current Streak, Best Streak
- Guess distribution bar chart (1–5 guesses)
- Bars are proportionally scaled to the maximum value; minimum bar width is 5%

**Share Text** (copied to clipboard via `navigator.clipboard`):
```
Grille #42 3/5

🟥🟥🟥🟥🟥🟥
🟥🟥🟥🟥🟥🟥
✅✅✅✅✅✅
⬜⬜⬜⬜⬜⬜
⬜⬜⬜⬜⬜⬜
```
- Winning row is shown as ✅✅✅✅✅✅; incorrect guesses as 🟥🟥🟥🟥🟥🟥; unused rows as ⬜⬜⬜⬜⬜⬜.
- If the player failed, the score is shown as `X/5`.

---

## 10. Deployment

The game is a fully static Nuxt 3 SPA deployed to **GitHub Pages** via GitHub Actions.

- `nuxt.config.ts` sets `ssr: false` (client-side rendering only) and `nitro.preset: 'github-pages'`.
- `app.baseURL` is set to `/grille/` to match the GitHub Pages subpath.
- The workflow (`.github/workflows/deploy.yml`) runs on every push to `main`:
  1. Checks out the repo
  2. Installs Node 22 and runs `npm ci`
  3. Configures GitHub Pages with `actions/configure-pages@v5`
  4. Runs `npm run generate` to produce a static site in `.output/public`
  5. Uploads the artifact and deploys via `actions/deploy-pages@v4`
- No server, database, or API is needed — the entire game runs in the browser.
