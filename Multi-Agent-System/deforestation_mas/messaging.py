"""Komunikasi antaragen bergaya FIPA-ACL (disederhanakan).

Setiap pesan punya *performative* (jenis tindak tutur), pengirim, penerima,
isi, dan conversation_id agar satu kasus bisa dilacak dari awal sampai akhir.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

# Performative yang dipakai sistem
INFORM = "inform"  # menyampaikan fakta (scene baru, hasil verifikasi, laporan)
REQUEST = "request"  # meminta agen lain melakukan sesuatu (validasi)
PROPOSE = "propose"  # mengusulkan kesimpulan (verdict validator)
CONFIRM = "confirm"  # kesimpulan yang sudah disepakati (konsensus)
CANCEL = "cancel"  # membatalkan kasus (alarm palsu disepakati)


@dataclass
class Message:
    performative: str
    sender: str
    receiver: str
    topic: str
    content: dict[str, Any] = field(default_factory=dict)
    conversation_id: str | None = None
    day: int = 0


class MessageBus:
    """Kotak surat per agen. Pesan langsung masuk ke inbox penerima dan dibaca
    saat penerima mendapat giliran ``step()``. Semua pesan dicatat untuk trace."""

    def __init__(self) -> None:
        self._inbox: dict[str, deque[Message]] = defaultdict(deque)
        self.log: list[Message] = []

    def send(self, msg: Message) -> None:
        self._inbox[msg.receiver].append(msg)
        self.log.append(msg)

    def receive_all(self, name: str) -> list[Message]:
        box = self._inbox[name]
        msgs = list(box)
        box.clear()
        return msgs

    def pending(self, name: str) -> int:
        return len(self._inbox[name])

    def conversation(self, conversation_id: str) -> list[Message]:
        return [m for m in self.log if m.conversation_id == conversation_id]

    def count_on(self, day: int) -> int:
        return sum(1 for m in self.log if m.day == day)
