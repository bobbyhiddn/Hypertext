"""The Game Crafter API client."""

import os
import time
import logging
from pathlib import Path
from typing import Optional
import requests

# Load .env file if present
try:
    from dotenv import load_dotenv
    # Look for .env in current dir and project root
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on environment variables

logger = logging.getLogger(__name__)

TGC_API_BASE = "https://www.thegamecrafter.com/api"


class TGCError(Exception):
    """TGC API error."""
    pass


class TGCClient:
    """Client for The Game Crafter REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Initialize TGC client.

        Args:
            api_key: TGC API key (or TGC_API_KEY env var)
            username: TGC username (or TGC_USERNAME env var)
            password: TGC password (or TGC_PASSWORD env var)
        """
        self.api_key = api_key or os.environ.get("TGC_API_KEY")
        self.username = username or os.environ.get("TGC_USERNAME")
        self.password = password or os.environ.get("TGC_PASSWORD")

        if not all([self.api_key, self.username, self.password]):
            raise TGCError(
                "Missing credentials. Set TGC_API_KEY, TGC_USERNAME, TGC_PASSWORD "
                "environment variables or pass them to constructor."
            )

        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.root_folder_id: Optional[str] = None
        self._session = requests.Session()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        files: Optional[dict] = None,
        retry_count: int = 5,
    ) -> dict:
        """Make API request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/session")
            data: Request data
            files: Files for multipart upload
            retry_count: Number of retries on failure

        Returns:
            JSON response dict
        """
        url = f"{TGC_API_BASE}{endpoint}"

        # Add session_id to data if we have one (except for session creation)
        if self.session_id and data is not None and endpoint != "/session":
            data["session_id"] = self.session_id

        delay = 1
        last_error = None

        for attempt in range(retry_count):
            try:
                if method == "GET":
                    params = data or {}
                    if self.session_id:
                        params["session_id"] = self.session_id
                    response = self._session.get(url, params=params)
                elif method == "POST":
                    if files:
                        response = self._session.post(url, data=data, files=files)
                    else:
                        response = self._session.post(url, data=data)
                elif method == "PUT":
                    response = self._session.put(url, data=data)
                elif method == "DELETE":
                    params = {"session_id": self.session_id} if self.session_id else {}
                    response = self._session.delete(url, params=params)
                else:
                    raise TGCError(f"Unknown HTTP method: {method}")

                result = response.json()

                # Check for API errors
                if "error" in result:
                    error_msg = result.get("error", {}).get("message", str(result))
                    raise TGCError(f"API error: {error_msg}")

                return result.get("result", result)

            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Request failed (attempt {attempt + 1}/{retry_count}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(delay)
                    delay *= 2
            except TGCError:
                raise

        raise TGCError(f"Request failed after {retry_count} attempts: {last_error}")

    def authenticate(self) -> None:
        """Create authenticated session with TGC."""
        logger.info("Authenticating with TGC...")

        result = self._request("POST", "/session", data={
            "api_key_id": self.api_key,
            "username": self.username,
            "password": self.password,
        })

        self.session_id = result.get("id")
        self.user_id = result.get("user_id")

        if not self.session_id:
            raise TGCError("Failed to get session_id from authentication")

        logger.info(f"Authenticated as user {self.user_id}")

        # Get root folder
        user_info = self._request("GET", f"/user/{self.user_id}")
        self.root_folder_id = user_info.get("root_folder_id")
        logger.info(f"Root folder: {self.root_folder_id}")

    def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> str:
        """Create a folder in user's filesystem.

        Args:
            name: Folder name
            parent_folder_id: Parent folder (defaults to root)

        Returns:
            Created folder ID
        """
        parent = parent_folder_id or self.root_folder_id

        result = self._request("POST", "/folder", data={
            "name": name,
            "folder_id": parent,
        })

        folder_id = result.get("id")
        logger.info(f"Created folder '{name}': {folder_id}")
        return folder_id

    def get_or_create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> str:
        """Get existing folder or create new one.

        Args:
            name: Folder name
            parent_folder_id: Parent folder (defaults to root)

        Returns:
            Folder ID
        """
        parent = parent_folder_id or self.root_folder_id

        # List folders in parent
        result = self._request("GET", "/folder", data={
            "folder_id": parent,
            "_include_related_objects": "folders",
        })

        folders = result.get("folders", {}).get("items", [])
        for folder in folders:
            if folder.get("name") == name:
                logger.info(f"Found existing folder '{name}': {folder['id']}")
                return folder["id"]

        return self.create_folder(name, parent)

    def upload_file(
        self,
        file_path: Path,
        folder_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        """Upload file to TGC filesystem.

        Args:
            file_path: Local file path
            folder_id: Destination folder (defaults to root)
            name: Override filename

        Returns:
            Uploaded file ID
        """
        folder = folder_id or self.root_folder_id
        filename = name or file_path.name

        with open(file_path, "rb") as f:
            result = self._request("POST", "/file",
                data={
                    "folder_id": folder,
                    "name": filename,
                    "session_id": self.session_id,
                },
                files={"file": (filename, f, "image/png")},
            )

        file_id = result.get("id")
        logger.info(f"Uploaded '{filename}': {file_id}")
        return file_id

    def create_game(self, name: str, description: str = "") -> str:
        """Create a new game project.

        Args:
            name: Game name
            description: Game description

        Returns:
            Game ID
        """
        result = self._request("POST", "/game", data={
            "name": name,
            "description": description,
        })

        game_id = result.get("id")
        logger.info(f"Created game '{name}': {game_id}")
        return game_id

    def get_games(self) -> list:
        """List user's games.

        Returns:
            List of game objects
        """
        result = self._request("GET", "/user/{}/games".format(self.user_id))
        return result.get("items", [])

    def get_or_create_game(self, name: str, description: str = "") -> str:
        """Get existing game or create new one.

        Args:
            name: Game name
            description: Game description

        Returns:
            Game ID
        """
        games = self.get_games()
        for game in games:
            if game.get("name") == name:
                logger.info(f"Found existing game '{name}': {game['id']}")
                return game["id"]

        return self.create_game(name, description)

    def create_poker_deck(
        self,
        game_id: str,
        name: str,
        back_file_id: str,
        quantity: int = 1,
    ) -> str:
        """Create a Poker Deck component in a game.

        Args:
            game_id: Parent game ID
            name: Deck name
            back_file_id: File ID for card back image
            quantity: Number of decks

        Returns:
            Deck ID
        """
        result = self._request("POST", "/pokerdeck", data={
            "game_id": game_id,
            "name": name,
            "back_id": back_file_id,
            "quantity": quantity,
        })

        deck_id = result.get("id")
        logger.info(f"Created poker deck '{name}': {deck_id}")
        return deck_id

    def add_card_to_deck(
        self,
        deck_id: str,
        face_file_id: str,
        quantity: int = 1,
    ) -> str:
        """Add a single card to a deck.

        Args:
            deck_id: Deck ID
            face_file_id: File ID for card face image
            quantity: Number of copies

        Returns:
            Card ID
        """
        result = self._request("POST", "/pokercard", data={
            "deck_id": deck_id,
            "face_id": face_file_id,
            "quantity": quantity,
        })

        card_id = result.get("id")
        logger.debug(f"Added card to deck: {card_id}")
        return card_id

    def add_cards_batch(
        self,
        deck_id: str,
        face_file_ids: list[str],
        quantities: Optional[list[int]] = None,
    ) -> list[str]:
        """Batch add cards to a deck (up to 100 at a time).

        Args:
            deck_id: Deck ID
            face_file_ids: List of file IDs for card faces
            quantities: List of quantities (defaults to 1 each)

        Returns:
            List of card IDs
        """
        if quantities is None:
            quantities = [1] * len(face_file_ids)

        card_ids = []

        # TGC allows up to 100 cards per batch
        batch_size = 100
        for i in range(0, len(face_file_ids), batch_size):
            batch_faces = face_file_ids[i:i + batch_size]
            batch_qtys = quantities[i:i + batch_size]

            # Build batch data
            data = {"deck_id": deck_id}
            for j, (face_id, qty) in enumerate(zip(batch_faces, batch_qtys)):
                data[f"cards[{j}][face_id]"] = face_id
                data[f"cards[{j}][quantity]"] = qty

            result = self._request("POST", f"/deck/{deck_id}/cards", data=data)

            items = result.get("items", [])
            card_ids.extend([item.get("id") for item in items])

            logger.info(f"Added batch of {len(batch_faces)} cards to deck")

        return card_ids

    def get_deck_cards(self, deck_id: str) -> list:
        """List cards in a deck.

        Args:
            deck_id: Deck ID

        Returns:
            List of card objects
        """
        result = self._request("GET", f"/deck/{deck_id}/cards")
        return result.get("items", [])

    def delete_card(self, card_id: str) -> None:
        """Delete a card from a deck.

        Args:
            card_id: Card ID to delete
        """
        self._request("DELETE", f"/pokercard/{card_id}")
        logger.debug(f"Deleted card: {card_id}")

    def clear_deck(self, deck_id: str) -> None:
        """Remove all cards from a deck.

        Args:
            deck_id: Deck ID
        """
        cards = self.get_deck_cards(deck_id)
        for card in cards:
            self.delete_card(card["id"])
        logger.info(f"Cleared {len(cards)} cards from deck")
