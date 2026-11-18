"""
call.py — Live voice-call module (1:1 live voice with the bot).

Two implementation paths are supported:

A) TELEGRAM-NATIVE VOICE CHAT (simplest MVP)
   Telegram supports voice chats in groups/supergroups via:
     - voice_chat_started / voice_chat_ended updates
     - voice_chat_participants_invited
   You join the group's voice chat and the bot can speak alongside you.
   This is group-scoped and bot-as-participant.

B) WEBRTC 1:1 VOICE RELAY (true 1:1)
   A signaling server (WebSocket relay) bridges two Telegram users'
   voice streams. The bot emits a per-user token; the client connects
   peer-to-peer (WebRTC) to a TURN/ICE relay.

This module exposes a clean API; the concrete transport is injected
via a Transport class. For the MVP, we ship the Telegram-native path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

# ---- Transport interface ----
class Transport:
    """Abstract transport for the live call. Subclass per platform."""

    def start_call(self, user_id: int) -> str:
        raise NotImplementedError

    def end_call(self, user_id: int) -> None:
        raise NotImplementedError

    def send_audio(self, user_id: int, audio: bytes) -> None:
        raise NotImplementedError

    def on_audio(self, user_id: int, cb: Callable[[bytes], None]) -> None:
        raise NotImplementedError


# ---- Telegram-native voice chat transport (MVP) ----
class TelegramVoiceTransport(Transport):
    """
    Uses Telegram's group voice chat. The bot joins the group, and can
    both send and receive voice messages during the chat.

    To enable:
      1. Bot must be an admin in a supergroup with voice chat enabled.
      2. Use setChatMenuButton / restrict / admin rights via Bot API.
      3. Handle voice_chat_started to gate the call.
    """

    def __init__(self, bot, chat_id: int):
        self.bot = bot
        self.chat_id = chat_id
        self._audio_recv: Dict[int, Callable[[bytes], None]] = {}

    def start_call(self, user_id: int) -> str:
        # Begin a voice chat in the group; real join is admin-managed.
        # This is a placeholder; in production you'd call the Bot API.
        return f"voicechat://{self.chat_id}/user/{user_id}"

    def end_call(self, user_id: int) -> None:
        pass

    def send_audio(self, user_id: int, audio: bytes) -> None:
        # In production: upload audio file to Telegram and send via send_voice.
        pass

    def on_audio(self, user_id: int, cb: Callable[[bytes], None]) -> None:
        self._audio_recv[user_id] = cb


# ---- WebRTC signaling transport (1:1, optional) ----
class WebRTCTransport(Transport):
    """
    Placeholder for a full 1:1 WebRTC relay.

    Signalling flow:
      1. Client A -> Server: offer (SDP) + user A token
      2. Server -> Client B: offer + A token
      3. Client B -> Server: answer (SDP)
      4. Server -> Client A: answer + B token
      5. Clients exchange ICE candidates via server
      6. Audio streams flow peer-to-peer; server only relays signalling.

    This adds infrastructure (a WebSocket server + TURN). See README.
    """

    def start_call(self, user_id: int) -> str:
        # Return a room token; real WebRTC handshake happens via the relay.
        return f"webrtc://room/{user_id}"

    def end_call(self, user_id: int) -> None:
        pass

    def send_audio(self, user_id: int, audio: bytes) -> None:
        pass

    def on_audio(self, user_id: int, cb: Callable[[bytes], None]) -> None:
        pass


# ---- Module-level factory ----
def transport_factory(platform: str = "telegram"):
    if platform == "webrtc":
        return WebRTCTransport()
    return TelegramVoiceTransport()


# ---- JSON-safe call state ----
@dataclass
class CallState:
    active: bool = False
    user_id: int = 0
    transport: Optional[Transport] = None
