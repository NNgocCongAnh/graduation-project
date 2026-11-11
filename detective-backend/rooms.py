"""Co-op room server for LAN play (max 3 detectives per room).

Protocol (JSON text frames over /ws/rooms/{room_id}?name=<player>):

Server -> joining client
    ROOM_STATE     {you, players, case_id, cards:[{card_id,x,y}]}
    ROOM_FULL      sent right before closing with code 4001
Server -> everyone else
    PLAYER_JOINED  {sender, players}
    PLAYER_LEFT    {sender, players}
Client -> server -> other peers (sender is always rewritten by the server)
    CARD_MOVED     {card_id, x, y}       board position, remembered for late joiners
    CASE_LOADED    {case_id}             a player switched case; resets the board
    CHAT_MESSAGE   {text}
    anything else  relayed as-is

Voice (binary frames, push-to-talk audio):
    client -> server   raw PCM16 mono 16 kHz bytes
    server -> peers    [1 byte name length][sender name UTF-8][PCM16 bytes]
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from fastapi import WebSocket

logger = logging.getLogger("detective-rooms")

MAX_PLAYERS_PER_ROOM = 3
ROOM_FULL_CLOSE_CODE = 4001
MAX_NAME_LENGTH = 24
MAX_CHAT_LENGTH = 500
# 16 kHz * 2 bytes * 0.25 s: generous for 20-60 ms frames, rejects abuse.
MAX_AUDIO_FRAME_BYTES = 8000
DEFAULT_PLAYER_NAME = "Thám tử"


@dataclass
class Room:
    room_id: str
    peers: Dict[WebSocket, str] = field(default_factory=dict)
    case_id: Optional[str] = None
    cards: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    @property
    def player_names(self) -> List[str]:
        return list(self.peers.values())

    def snapshot_for(self, you: str) -> dict:
        return {
            "type": "ROOM_STATE",
            "you": you,
            "players": self.player_names,
            "case_id": self.case_id,
            "cards": [{"card_id": cid, "x": x, "y": y} for cid, (x, y) in self.cards.items()],
        }


def sanitize_player_name(raw: Optional[str]) -> str:
    name = (raw or "").strip()[:MAX_NAME_LENGTH]
    return name or DEFAULT_PLAYER_NAME


def unique_name(requested: str, taken: List[str]) -> str:
    if requested not in taken:
        return requested
    suffix = 2
    while f"{requested} {suffix}" in taken:
        suffix += 1
    return f"{requested} {suffix}"


class RoomManager:
    """Tracks rooms, enforces capacity and keeps the shared board state."""

    def __init__(self, max_players: int = MAX_PLAYERS_PER_ROOM):
        self.max_players = max_players
        self.rooms: Dict[str, Room] = {}

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    async def join(self, room_id: str, websocket: WebSocket, requested_name: Optional[str]) -> Optional[str]:
        """Accept the socket. Returns the assigned player name, or None if the room is full."""
        await websocket.accept()
        room = self.rooms.setdefault(room_id, Room(room_id))

        if len(room.peers) >= self.max_players:
            await websocket.send_json({"type": "ROOM_FULL", "players": room.player_names})
            await websocket.close(code=ROOM_FULL_CLOSE_CODE, reason="ROOM_FULL")
            logger.info(f"Rejected player from full room '{room_id}'")
            return None

        name = unique_name(sanitize_player_name(requested_name), room.player_names)
        room.peers[websocket] = name
        await websocket.send_json(room.snapshot_for(name))
        await self.broadcast(room, {"type": "PLAYER_JOINED", "sender": name, "players": room.player_names}, exclude=websocket)
        logger.info(f"'{name}' joined room '{room_id}' ({len(room.peers)}/{self.max_players})")
        return name

    async def leave(self, room_id: str, websocket: WebSocket) -> None:
        room = self.rooms.get(room_id)
        if room is None or websocket not in room.peers:
            return
        name = room.peers.pop(websocket)
        logger.info(f"'{name}' left room '{room_id}'")
        if not room.peers:
            del self.rooms[room_id]
            return
        await self.broadcast(room, {"type": "PLAYER_LEFT", "sender": name, "players": room.player_names})

    async def handle_message(self, room_id: str, websocket: WebSocket, message: dict) -> None:
        room = self.rooms.get(room_id)
        if room is None or websocket not in room.peers or not isinstance(message, dict):
            return

        msg = dict(message)
        msg["sender"] = room.peers[websocket]
        msg_type = msg.get("type")

        if msg_type == "CARD_MOVED":
            card_id = msg.get("card_id")
            try:
                x, y = float(msg.get("x", 0.0)), float(msg.get("y", 0.0))
            except (TypeError, ValueError):
                return
            if not card_id:
                return
            room.cards[str(card_id)] = (x, y)
        elif msg_type == "CASE_LOADED":
            if not msg.get("case_id"):
                return
            room.case_id = str(msg["case_id"])
            room.cards.clear()
        elif msg_type == "CHAT_MESSAGE":
            text = str(msg.get("text") or "").strip()[:MAX_CHAT_LENGTH]
            if not text:
                return
            msg["text"] = text

        await self.broadcast(room, msg, exclude=websocket)

    async def relay_audio(self, room_id: str, websocket: WebSocket, pcm: bytes) -> None:
        """Forward a push-to-talk audio frame to the other players, tagged with the sender name."""
        room = self.rooms.get(room_id)
        if room is None or websocket not in room.peers:
            return
        if not pcm or len(pcm) > MAX_AUDIO_FRAME_BYTES or len(pcm) % 2 != 0:
            return
        name = room.peers[websocket].encode("utf-8")[:255]
        frame = bytes([len(name)]) + name + pcm

        dead = []
        for peer in list(room.peers):
            if peer is websocket:
                continue
            try:
                await peer.send_bytes(frame)
            except Exception:
                dead.append(peer)
        for peer in dead:
            room.peers.pop(peer, None)

    async def broadcast(self, room: Room, message: dict, exclude: Optional[WebSocket] = None) -> None:
        dead = []
        for peer in list(room.peers):
            if peer is exclude:
                continue
            try:
                await peer.send_json(message)
            except Exception:
                dead.append(peer)
        for peer in dead:
            room.peers.pop(peer, None)
