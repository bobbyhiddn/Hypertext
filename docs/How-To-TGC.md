# Hypertext TCG
## The Game Crafter Programmatic Staging Specification

| Attribute | Value |
|-----------|-------|
| Version | 1.0.0 |
| Date | December 28, 2025 |
| Author | Micah Longmire |
| Status | Draft |

---

## Executive Summary

This specification defines the integration between the Hypertext biblical word-study trading card game pipeline and The Game Crafter (TGC) print-on-demand service. The integration enables fully automated card staging from GitHub Actions, producing MTG sleeve-compatible physical cards without manual intervention.

The system will extend the existing Hypertext pipeline (GitHub Actions + Gemini API) to generate print-ready card images and programmatically upload them to TGC via their REST API. This creates a seamless path from card data generation to physical prototype ordering.

---

## Objectives

- Automate card image upload to The Game Crafter from CI/CD pipeline
- Maintain MTG standard card dimensions (2.5" × 3.5" / 63.5mm × 88.9mm) for sleeve compatibility
- Support parallel output: TTS deck sheets for digital playtesting and individual cards for print
- Enable one-click prototype ordering after pipeline completion
- Preserve existing Hypertext pipeline architecture and extend rather than replace

---

## Card Specifications

### Physical Dimensions

Target product: TGC Poker Deck (standard playing card size, MTG sleeve-compatible)

| Attribute | Value | Notes |
|-----------|-------|-------|
| Finished Size | 2.5" × 3.5" | 63.5mm × 88.9mm |
| Image Size | 825 × 1125 px | At 300 DPI |
| Bleed Area | 36 px (0.125") | All sides |
| Safe Zone | 753 × 1053 px | Keep text/icons here |
| Card Stock | S30/S33 | Standard or Premium |
| Corner Radius | 3.5mm | Standard rounded |

### Image Requirements

- Format: PNG (preferred) or JPEG
- Color Space: sRGB
- Resolution: 300 DPI minimum
- Bleed: Extend background/art 36px beyond cut line on all edges
- Safe Zone: Critical elements must be 36px inside cut line

### TTS Parallel Output

The pipeline will continue generating Tabletop Simulator deck sheets alongside individual print cards:

| TTS Output | TGC Output |
|------------|------------|
| 10×7 grid deck sheet (max 69 cards) | Individual 825×1125 card images |
| No bleed required | 36px bleed on all sides |
| JSON with deck metadata | API upload to TGC filesystem |

---

## TGC API Integration

### Authentication

TGC uses session-based authentication with API keys:

1. Register as developer in TGC profile settings
2. Generate API Key from Developer tab
3. Create session using API key + credentials
4. Use session_id for all subsequent requests

#### Session Creation

```
POST https://www.thegamecrafter.com/api/session
  api_key_id: <API_KEY>
  username: <USERNAME>
  password: <PASSWORD>
```

Response includes `session_id` and `user_id` for subsequent calls.

### Core API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/session` | POST | Create authenticated session |
| `/api/file` | POST | Upload image to user filesystem |
| `/api/folder` | POST/GET | Create/list folders |
| `/api/game` | POST/GET | Create/retrieve game projects |
| `/api/pokerdeck` | POST | Create Poker Deck component |
| `/api/pokercard` | POST | Add card to deck |
| `/api/deck/.../cards` | POST | Batch create up to 100 cards |

### File Upload Flow

1. Get user's `root_folder_id` from `/api/user/{user_id}`
2. Create project folder: `POST /api/folder` with `folder_id` and `name`
3. Upload card images as multipart/form-data to `POST /api/file`
4. Store returned `file_id` for each uploaded image
5. Create deck referencing uploaded `file_id`s

### Deck Creation Flow

1. Create or retrieve game: `POST /api/game`
2. Create Poker Deck component: `POST /api/pokerdeck` with `game_id`
3. Upload card back image, get `file_id`
4. Set deck back: `PATCH /api/pokerdeck/{deck_id}` with `back_id`
5. Batch create cards: `POST /api/deck/{deck_id}/cards` with `face_id` array

---

## Pipeline Architecture

### Current Hypertext Pipeline

```
Card Data (JSON) → Gemini API → Card Generation → TTS Deck Sheet → GitHub Release
```

### Extended Pipeline

```
Card Data (JSON)
       ↓
   Gemini API
       ↓
 Card Generation
    ↓      ↓
TTS Sheet  Print Cards (825×1125 + bleed)
    ↓           ↓
 GitHub     TGC API Upload
 Release         ↓
          TGC Game Project (staged)
```

### GitHub Actions Workflow Addition

New job to be added after card generation:

```yaml
tgc-staging:
  needs: generate-cards
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
    - name: Install dependencies
      run: pip install requests pillow
    - name: Upload to TGC
      env:
        TGC_API_KEY: ${{ secrets.TGC_API_KEY }}
        TGC_USERNAME: ${{ secrets.TGC_USERNAME }}
        TGC_PASSWORD: ${{ secrets.TGC_PASSWORD }}
      run: python scripts/tgc_upload.py
```

---

## Data Model

### Card Manifest Schema

The pipeline will generate a manifest file mapping card data to generated images:

```json
{
  "version": "1.0.0",
  "generated_at": "2025-12-28T10:30:00Z",
  "deck_name": "Hypertext Core Set",
  "cards": [
    {
      "id": "HT-001",
      "name": "Logos",
      "hebrew_word": "דָּבָר",
      "tts_position": { "sheet": 1, "row": 0, "col": 0 },
      "print_image": "cards/print/HT-001.png",
      "tgc_file_id": null
    }
  ],
  "card_back": "assets/card-back.png",
  "tgc_game_id": null,
  "tgc_deck_id": null
}
```

### TGC State Tracking

After upload, the manifest is updated with TGC identifiers:

- `tgc_file_id`: File ID for each uploaded card face
- `tgc_game_id`: Game project ID in TGC
- `tgc_deck_id`: Poker Deck component ID

This enables incremental updates—only upload changed cards on subsequent runs.

---

## Implementation Modules

### tgc_client.py — API Client

Wrapper class for TGC REST API:

- Session management with automatic refresh
- File upload with retry logic
- Folder management
- Game and deck CRUD operations
- Batch card creation

### image_processor.py — Print Preparation

Image transformation for print requirements:

- Add bleed margins (36px) by extending edge pixels
- Validate dimensions (825×1125)
- Convert color space to sRGB if needed
- Optimize file size while maintaining quality

### tgc_upload.py — Pipeline Orchestrator

Main script executed by GitHub Actions:

- Load card manifest from generation step
- Initialize TGC client with credentials from secrets
- Process images for print
- Upload to TGC (with diff detection for incremental updates)
- Create/update deck structure
- Update manifest with TGC IDs
- Commit updated manifest to repo (optional)

---

## Error Handling

### Retry Strategy

All API calls implement exponential backoff:

1. Initial retry after 1 second
2. Double delay on each subsequent failure
3. Maximum 5 retries before failing job
4. Log all failures with response details

### Partial Failure Recovery

If upload fails mid-batch:

- Manifest preserves successfully uploaded `file_id`s
- Next run resumes from last successful card
- Deck creation only proceeds after all cards uploaded
- GitHub Actions job marked failed with clear error message

### Validation Checks

- Image dimensions verified before upload (825×1125)
- File size checked (TGC limit: 50MB per file)
- Card count validated against deck limits
- API response codes checked for success (200/201)

---

## Security Considerations

### Credential Management

1. TGC credentials stored as GitHub repository secrets
2. API key, username, and password never logged
3. Session tokens expire and are not persisted
4. Secrets masked in GitHub Actions logs automatically

### Repository Secrets Required

| Secret Name | Description |
|-------------|-------------|
| `TGC_API_KEY` | API Key ID from TGC Developer settings |
| `TGC_USERNAME` | TGC account username |
| `TGC_PASSWORD` | TGC account password |

---

## Testing Strategy

### Unit Tests

- Image processor: bleed addition, dimension validation
- TGC client: API request formatting, response parsing
- Manifest handling: JSON schema validation, diff detection

### Integration Tests

- Upload single card to TGC sandbox (if available)
- Create minimal deck with 2-3 cards
- Verify deck appears correctly in TGC web interface

### Manual Verification

- Order test print of sample cards
- Verify physical dimensions and sleeve fit
- Check print quality, color accuracy, bleed handling

---

## Future Enhancements

1. **Automated ordering**: Trigger TGC order creation via API after staging
2. **Cost estimation**: Calculate per-run print costs from TGC pricing API
3. **Version tracking**: Tag TGC games with git commit SHA for traceability
4. **Multi-deck support**: Handle expansion sets as separate deck components
5. **Proof generation**: Download TGC proof images for visual QA in PR reviews
6. **Webhook notifications**: Alert on successful staging completion

---

## Appendix

### TGC API Documentation

- Developer Portal: https://www.thegamecrafter.com/developer
- API Reference: https://www.thegamecrafter.com/developer/Deck.html
- Python Example: https://www.thegamecrafter.com/developer/PythonExample.html
- Component Specs: https://help.thegamecrafter.com/article/85-cards

### Existing Tools Reference

- tgc-utils (Python): https://github.com/jukujala/tgc-utils
- nanDECK (with TGC integration): https://www.nandeck.com/

### Card Template Downloads

TGC provides official templates for Poker cards:

- Photoshop (.psd)
- Illustrator (.ai)
- PNG template with safe zone guides
- SVG for vector workflows

Available at: https://www.thegamecrafter.com → Components → Poker Deck → Templates