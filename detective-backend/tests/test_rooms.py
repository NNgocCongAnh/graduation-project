"""Integration tests for the LAN co-op room server (/ws/rooms/{room_id})."""

import os

os.environ["DETECTIVE_LAN_DISCOVERY"] = "0"

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from main import app, room_manager
from rooms import MAX_PLAYERS_PER_ROOM, ROOM_FULL_CLOSE_CODE, sanitize_player_name, unique_name
from security import sign_request

client = TestClient(app)


def test_room_capacity_is_three():
    assert MAX_PLAYERS_PER_ROOM == 3


def test_join_receives_room_state_and_peers_get_presence():
    with client.websocket_connect("/ws/rooms/T-PRESENCE?name=An") as a:
        state_a = a.receive_json()
        assert state_a["type"] == "ROOM_STATE"
        assert state_a["you"] == "An"
        assert state_a["players"] == ["An"]

        with client.websocket_connect("/ws/rooms/T-PRESENCE?name=Binh") as b:
            state_b = b.receive_json()
            assert state_b["players"] == ["An", "Binh"]

            joined = a.receive_json()
            assert joined == {"type": "PLAYER_JOINED", "sender": "Binh", "players": ["An", "Binh"]}

        left = a.receive_json()
        assert left["type"] == "PLAYER_LEFT"
        assert left["sender"] == "Binh"
        assert left["players"] == ["An"]


def test_fourth_player_is_rejected_with_room_full():
    with client.websocket_connect("/ws/rooms/T-FULL?name=P1") as p1, \
         client.websocket_connect("/ws/rooms/T-FULL?name=P2") as p2, \
         client.websocket_connect("/ws/rooms/T-FULL?name=P3") as p3:
        for ws in (p1, p2, p3):
            ws.receive_json()

        with client.websocket_connect("/ws/rooms/T-FULL?name=P4") as p4:
            assert p4.receive_json()["type"] == "ROOM_FULL"
            with pytest.raises(WebSocketDisconnect) as exc:
                p4.receive_json()
            assert exc.value.code == ROOM_FULL_CLOSE_CODE

        headers = sign_request("GET", "/api/rooms/T-FULL")
        info = client.get("/api/rooms/T-FULL", headers=headers).json()
        assert info["is_full"] is True
        assert len(info["players"]) == 3


def test_late_joiner_gets_case_and_card_positions():
    with client.websocket_connect("/ws/rooms/T-STATE?name=Host") as host:
        host.receive_json()
        host.send_json({"type": "CASE_LOADED", "case_id": "CASE-2026-001"})
        host.send_json({"type": "CARD_MOVED", "card_id": "SUSP-01", "x": 12.5, "y": -40})
        host.send_json({"type": "CARD_MOVED", "card_id": "SUSP-01", "x": 20, "y": 5})

        with client.websocket_connect("/ws/rooms/T-STATE?name=Guest") as guest:
            state = guest.receive_json()
            assert state["case_id"] == "CASE-2026-001"
            assert state["cards"] == [{"card_id": "SUSP-01", "x": 20.0, "y": 5.0}]


def test_case_switch_resets_board():
    with client.websocket_connect("/ws/rooms/T-RESET?name=Host") as host:
        host.receive_json()
        host.send_json({"type": "CARD_MOVED", "card_id": "EV-1", "x": 1, "y": 1})
        host.send_json({"type": "CASE_LOADED", "case_id": "CASE-NEW"})
        with client.websocket_connect("/ws/rooms/T-RESET?name=Guest") as guest:
            state = guest.receive_json()
            assert state["case_id"] == "CASE-NEW"
            assert state["cards"] == []


def test_chat_sender_cannot_be_spoofed_and_is_relayed():
    with client.websocket_connect("/ws/rooms/T-CHAT?name=An") as a:
        a.receive_json()
        with client.websocket_connect("/ws/rooms/T-CHAT?name=Binh") as b:
            b.receive_json()
            a.receive_json()  # PLAYER_JOINED
            b.send_json({"type": "CHAT_MESSAGE", "sender": "An", "text": "  hung thủ là quản gia  "})
            msg = a.receive_json()
            assert msg["sender"] == "Binh"
            assert msg["text"] == "hung thủ là quản gia"


def test_duplicate_names_get_suffix():
    with client.websocket_connect("/ws/rooms/T-DUP?name=An") as a:
        a.receive_json()
        with client.websocket_connect("/ws/rooms/T-DUP?name=An") as b:
            assert b.receive_json()["you"] == "An 2"


def test_empty_room_is_removed():
    with client.websocket_connect("/ws/rooms/T-GONE?name=Solo") as ws:
        ws.receive_json()
    assert room_manager.get_room("T-GONE") is None


def test_name_helpers():
    assert sanitize_player_name("   ") == "Thám tử"
    assert len(sanitize_player_name("x" * 100)) == 24
    assert unique_name("A", ["A", "A 2"]) == "A 3"


def test_voice_frames_are_relayed_with_sender_header_and_not_echoed():
    pcm = (1234).to_bytes(2, "little", signed=True) * 160  # 10 ms of PCM16
    with client.websocket_connect("/ws/rooms/T-VOICE?name=An") as a:
        a.receive_json()
        with client.websocket_connect("/ws/rooms/T-VOICE?name=Bình") as b:
            b.receive_json()
            a.receive_json()  # PLAYER_JOINED
            b.send_bytes(pcm)
            frame = a.receive_bytes()
            name_len = frame[0]
            assert frame[1:1 + name_len].decode("utf-8") == "Bình"
            assert frame[1 + name_len:] == pcm

            # oversized / odd-length frames are dropped; text still flows afterwards
            b.send_bytes(b"\x00" * 9001)
            b.send_bytes(b"\x01\x02\x03")
            b.send_json({"type": "CHAT_MESSAGE", "text": "ok"})
            assert a.receive_json()["text"] == "ok"


def test_invalid_json_text_is_ignored():
    with client.websocket_connect("/ws/rooms/T-BADJSON?name=An") as a:
        a.receive_json()
        a.send_text("{not json")
        a.send_json({"type": "CARD_MOVED", "card_id": "C1", "x": 1, "y": 2})
        with client.websocket_connect("/ws/rooms/T-BADJSON?name=Binh") as b:
            state = b.receive_json()
            assert state["cards"] == [{"card_id": "C1", "x": 1.0, "y": 2.0}]
