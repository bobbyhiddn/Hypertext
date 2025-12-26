# Hypertext FAQ

## General Questions

### What is Hypertext?
Hypertext is a word-study trading card project that explores Biblical vocabulary through collectible cards. Each card features a word from Scripture with its Greek and Hebrew forms, contextual artwork, and educational content.

### How often are new cards released?
During active production, we aim for one new card per day or every other day. Cards are compiled into quarterly decks.

### What's in each card?
- The word in English with a gloss (short definition)
- Original language forms (Greek and Hebrew with transliterations)
- Scripture references from Old and New Testaments
- Custom artwork depicting the word's meaning
- Stats for game mechanics (Lore, Context, Complexity)
- An ability tied to the word's meaning
- Trivia bullets with interesting facts

## Card Types

### What do the card types mean?
- **NOUN**: Person, place, thing, or concept
- **VERB**: Action or state of being
- **ADJECTIVE**: Descriptive word
- **NAME**: Proper name (person or place)
- **TITLE**: Special/wild card that can count as other cards

### What do the rarities mean?
- **COMMON** (white circle): Frequently occurring words with simple abilities
- **UNCOMMON** (green square): Less common words with suit-based abilities
- **RARE** (gold hexagon): Notable words with stat-referencing abilities
- **MYTHIC** (orange rhombus): Significant theological terms with unique abilities

## Stats

### What does each stat represent?
- **LORE** (1-5): Meta-narrative alignment. How central is this word to the overarching Biblical story?
- **CONTEXT** (1-5): Occurrence bucket. Roughly how often does this word appear in Scripture?
- **COMPLEXITY** (1-5): Grammar depth. How complex are the linguistic features of this word?

## Technical

### What format are cards stored in?
Each card has:
- `meta.yml`: Author-facing metadata
- `card.json`: Full card data for image generation
- `outputs/`: Rendered images at various resolutions

### How are images generated?
Card.json files are used as prompts for image generation models. The JSON contains complete styling, layout, and content instructions.

### Can I contribute?
Check the repository for contribution guidelines. Word suggestions and corrections are welcome via issues.

## Printing

### Will physical cards be available?
Yes! Each quarter, completed cards are compiled into a print-ready deck. Subscribers ($25/month) receive quarterly deck prints.

### What size are printed cards?
Standard playing card size: 2.5 x 3.5 inches (63.5 x 88.9 mm).

### What's the print quality?
Cards are printed at 300+ DPI on quality cardstock, suitable for handling and gameplay.
