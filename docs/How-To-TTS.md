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
| **Lot Deck (30 cards)** | Phase cards |
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

## Game Setup (2-8 Players)

1. **Clear table**: Box select all > Delete (or Games > Classic > Custom)
2. **Spawn game**: Objects > Saved Objects > Hypertext
3. **Position decks**: Drag Main Deck and Lot Deck to center
4. **Click SHUFFLE** to shuffle the Main Deck
5. **Click DEAL 7** to deal 7 cards to each player
6. **Deal 1 Lot** to each player (hover Lot deck, press 1, repeat for each player)
7. **Flip 1 Lot** face-up to the center as the Board Phase
8. **Designate Sheol**: The red zone is for discards

---

## Turn Sequence

### 1. Draw
- Draw 1 card from the Tower (Main Deck)

### 2. Play
- **Free Activation**: Reveal the card you just drew to use its ability
- **Letter Activation**: Spend 1 Letter token to reveal a card from hand
- Activated cards go to Sheol (drag to red zone)

### 3. Record
- Play sets matching the Board Phase or your Lot
- **Board Phase**: Cards go to your Pages (face-up in front of you)
- **Lot**: Cards go to Sheol, gain 1 Letter (2 for 7-card Lots)

### 4. End
- Discard 1 card to Sheol
- Other players may call "Redeem!" to take your discard

---

## Chapter End

When a player empties their hand:

1. **Grace period**: Others may play to open phases
2. **Score**: Tally points for the chapter
3. **Convert Letters**: Each Letter = 5 points
4. **Hand penalty**: -1 point per card remaining
5. **Click NEW CHAPTER** and reset:
   - Collect Lots, reshuffle into Lot deck
   - Shuffle Sheol back into Tower
   - Deal new Lots and 7 cards each
   - Flip new Board Phase

---

## Scoring Reference

| Source | Points |
|--------|--------|
| 5-card Board Phase | 8 |
| 6-card Board Phase | 10 |
| 7-card Board Phase | 12 |
| Record Wreath (Alpha) | +2 |
| Empty Wreath (Omega) | +2 |
| Letter conversion | 5 each |
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
