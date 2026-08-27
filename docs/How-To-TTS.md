# Hypertext: Tabletop Simulator Guide

## Setup

### 1. Export the Game

```bash
python -m hypertext.lots.exporter \
  --series series/2026-Q1 \
  --target tabletopsimulator \
  --cards-source demo_cards \
  --limit 90 \
  --url-base "https://raw.githubusercontent.com/bobbyhiddn/Hypertext/main/series/2026-Q1/exports/tabletopsimulator"
```

### 2. Sync to TTS

Run the sync script:
```bash
./scripts/tts_sync.sh
```

Or manually copy:
```
series/2026-Q1/exports/tabletopsimulator/Hypertext.json
```
to:
```
Documents/My Games/Tabletop Simulator/Saves/Saved Objects/
```

Note: On OneDrive, the path may be:
```
C:\Users\<USERNAME>\OneDrive\Documents\My Games\Tabletop Simulator\Saves\Saved Objects\
```

### 3. Load in TTS

1. Open Tabletop Simulator
2. Start a game: **Games** > **Classic** > **Custom**
3. Spawn Hypertext: **Objects** > **Saved Objects** > **Hypertext**

---

## Components

When you spawn Hypertext, you get:

| Component | Description |
|-----------|-------------|
| **Main Deck (90 cards)** | The Tower - main playing cards |
| **Lot Deck (30 cards)** | Chapter Lot and Portion Lot recipes |
| **24 Letter Tokens** | Blue chips for tracking Letters |
| **2 Wreath Tokens** | Gold Alpha (Record) and Omega (Empty) wreaths |
| **Sheol Zone** | Red-tinted discard area |
| **DEAL 7 Button** | Deals 7 cards to each player |
| **SHUFFLE Button** | Shuffles the main deck |
| **NEW CHAPTER Button** | Announces new chapter |

---

## Controls

### Camera
| Key | Action |
|-----|--------|
| **Middle Mouse** | Pan camera |
| **Scroll Wheel** | Zoom in/out |
| **Tab** | Zoom out to see whole table |
| **Spacebar** | Hold to lift objects higher while dragging |

### Selecting Objects
| Key | Action |
|-----|--------|
| **Left Click** | Select/grab object |
| **Box Select** | Hold left mouse and drag to select multiple |
| **Delete** | Delete selected objects |

### Cards
| Key | Action |
|-----|--------|
| **F** | Flip card (face up/down) |
| **Q / E** | Rotate left/right |
| **G** | Group selected cards into a deck |
| **R** | Shuffle (while hovering over deck) |
| **1-9** | Deal that many cards (while hovering over deck) |

### Inspecting
| Key | Action |
|-----|--------|
| **Alt + Hold** | Zoom/magnify card |
| **Alt + Shift** | Zoom and flip to see back |
| **Right-click** > **Peek** | Secretly look at facedown card |

### Hands
| Key | Action |
|-----|--------|
| **H** | Toggle hand zone visibility |
| **Drag to hand zone** | Add card to your hand |
| **Drag from hand** | Play card to table |

### Decks
| Action | How |
|--------|-----|
| **Draw** | Click and drag top card |
| **Deal** | Hover deck, press number key (1-9) |
| **Deal to all** | Right-click > Deal |
| **Search** | Right-click > Search |
| **Shuffle** | Right-click > Shuffle (or R) |

### Other
| Key | Action |
|-----|--------|
| **L** | Lock/unlock object |
| **Ctrl+Z** | Undo |
| **F1** | Game menu |

---

## Solo/Hotseat Setup (Multiple Players, One Computer)

To test or play solo with multiple player seats:

1. **Open Game**: Games > Classic > Custom
2. **Open Menu**: Click the **Menu** button (top right) or press **Esc**
3. **Game Settings**: Options > Game
4. **Enable Hotseat**: Check "Hotseat Mode" (allows switching between seats)
5. **Add Players**:
   - Top of screen shows player seats (colored circles)
   - Click a seat color to "sit" in that position
   - Right-click empty seats > "Promote to Player" to add AI seats
6. **Switch Players**: Click different colored seats to control different hands

### Hand Zones
Each player color has their own hand zone:
- Cards in your hand zone are hidden from other players
- In hotseat mode, switch seats to see each player's perspective

---

## Game Setup (2-8 Players)

1. **Clear table**: Box select all > Delete (or Games > Classic > Custom)
2. **Spawn game**: Objects > Saved Objects > Hypertext
3. **Position decks**: Drag Main Deck and Lot Deck to center
4. **Shuffle**: Right-click Main Deck > Shuffle (or hover and press R)
5. **Deal 7 to each player**:
   - Hover over Main Deck
   - Press **7** to deal 7 cards
   - Cards go to the current player's hand
   - Switch seats and repeat for each player
6. **Deal 2 Lot candidates** to each player:
   - Hover Lot deck, press **2**
   - Each player keeps one as their Portion Lot (face-up in their area) and returns the other to the Lot deck
7. **Flip 1 Lot** face-up to the center as the Chapter Lot (press F to flip)
   - Also flip the top card of the Tower into Sheol to seed it
8. **Designate Sheol**: The red zone is for discards

---

## Turn Sequence

### 1. Reveal
- Reveal the top card of the Tower (Main Deck)
- Either **Draw-Activate** it (see below) or **Pass**: take it into hand and draw 1 more

### 2. Activate
- **Draw Activation**: Activate the card you just revealed (0 Letters + printed cost)
- **Hand Activation**: Spend 1 Letter token plus the printed cost to activate a card from hand
- Activated cards and their costs go to Sheol (drag to red zone)

### 3. Record
- Play exact sets matching the Chapter Lot or any Portion Lot
- **Chapter Lot**: Cards go to your Pages (face-up in front of you); the Page scores its Chapter Value at Chapter end
- **Your Portion Lot**: Cards go to Sheol, gain Owner Letters
- **Another player's Portion Lot**: Cards go to Sheol, gain Visitor Letters
- See [rules.md](rules.md) for the value table

### 4. End
- Discard 1 card to Sheol
- Other players may call "Redeem!" to take your discard

---

## Chapter End

When a player empties their hand:

1. **Grace period**: Each other player, clockwise, gets one final Record stage
2. **Score Pages**: Each Page scores its Chapter Value (8 / 10 / 14)
3. **Convert Letters**: Each remaining Letter = 3 points; add Wreaths
4. **Hand penalty**: -1 point per card remaining
5. **Click NEW CHAPTER** and reset:
   - Set the finished Chapter Lot aside (it does not repeat); return Portion Lots to the Lot deck
   - Gather all 90 Word Cards (hands, Tower, Sheol, Pages) and shuffle a fresh Tower
   - Deal 2 Lot candidates and 7 cards each
   - Flip the new Chapter Lot and seed Sheol

---

## Scoring Reference

| Source | Points |
|--------|--------|
| 5-card Page | 8 |
| 6-card Page | 10 |
| 7-card Page | 14 |
| Record Wreath (Alpha) | +2 |
| Empty Wreath (Omega) | +2 |
| Letter conversion | 3 each |
| Hand penalty | -1 per card |

---

## Tips

- **Lock important objects**: Right-click > Toggle Lock (or L) to prevent accidents
- **Save your game**: Games > Save Game to resume later
- **Flip the table**: Don't. But if you do, just reload from Saved Objects
- **Voice chat**: TTS has built-in voice - check Audio settings

---

## Troubleshooting

### Cards not loading / showing blank
The sprite sheet images need to be accessible. Make sure:
1. The exports are committed and pushed to GitHub
2. The URL base in the export matches your repo

### Buttons not working
The Lua scripts may not have loaded. Try:
1. Right-click the button > Scripting > Execute
2. Or re-spawn the game from Saved Objects

### Can't find Saved Objects
Path varies by system:
- **Standard**: `Documents/My Games/Tabletop Simulator/Saves/Saved Objects/`
- **OneDrive**: `OneDrive/Documents/My Games/Tabletop Simulator/Saves/Saved Objects/`
- **Steam**: Check Steam userdata folder

---

## Re-exporting

After making changes to cards or the exporter:

```bash
# Regenerate export
python -m hypertext.lots.exporter \
  --series series/2026-Q1 \
  --target tabletopsimulator \
  --cards-source demo_cards \
  --limit 90 \
  --url-base "https://raw.githubusercontent.com/bobbyhiddn/Hypertext/main/series/2026-Q1/exports/tabletopsimulator"

# Sync to TTS
./scripts/tts_sync.sh

# In TTS: Clear table, re-spawn from Saved Objects
```
