import asyncio
import random
import threading
import time
from typing import Dict, List, Optional, Tuple
from server import ConnectionManager

# Optional generate.py (dynamic graph); fallback to a small static graph if unavailable
try:
    from generate import generate_graph as _gen_graph, get_children as _gen_get_children
    _GEN_OK, _GEN_ERR = True, None
except Exception as e:
    _GEN_OK, _GEN_ERR = False, e

async def _safe_generate_graph():
    if _GEN_OK:
        return await _gen_graph()
    raise RuntimeError(f"generate import failed: {_GEN_ERR}")

def _safe_get_children(emoji: str, adj: Dict[str, List[str]]) -> List[str]:
    return _gen_get_children(emoji, adj) if _GEN_OK else adj.get(emoji, [])

SMALL_GRAPH: Dict[str, List[str]] = {
    "😀": ["😃", "🙂"],
    "😃": ["😀", "😊"],
    "🙂": ["😀", "😊"],
    "😊": ["🙂", "😃", "🥰"],
    "🥰": ["😊", "😍"],
    "😍": ["🥰", "😉"],
    "😉": ["😍"],
}

GAME_TIME_MINUTES = 1


class GameLogic:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        return cls()

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        try:
            self.adjacency_list: Dict[str, List[str]] = asyncio.run(_safe_generate_graph())
        except Exception:
            self.adjacency_list = SMALL_GRAPH
        self.user_score: Dict[str, float] = {}
        self._score_lock = threading.Lock()
        self.start_value: Optional[str] = None
        self.dest_value: Optional[str] = None
        self.timer_seconds: int = 0
        self.game_active: bool = False
        self.round_started_at: float = 0.0
        self._initialized = True

    def set_two_values(self):
        nodes = list(self.adjacency_list.keys())
        if not nodes:
            self.start_value = self.dest_value = "😀"
            return
        start_candidates = [n for n in nodes if self.adjacency_list.get(n)] or nodes
        self.start_value = random.choice(start_candidates)
        self.dest_value = random.choice(nodes)
        while self.dest_value == self.start_value:
            self.dest_value = random.choice(nodes)

    def show_children(self, emoji: str) -> str:
        children = _safe_get_children(emoji, self.adjacency_list)
        return ", ".join(children) if children else "Dead end"

    def save_user_time(self, user: str, seconds_taken: float):
        with self._score_lock:
            if user not in self.user_score:
                self.user_score[user] = seconds_taken

    def show_start(self, cm: ConnectionManager):
        msgs = [
            f"{self.start_value} ----> {self.dest_value}\n-1",
            f"{self.show_children(self.start_value)}-1",
            "whats your pick: \n",
        ]
        cm.set_on_join_messages(msgs)
        for m in msgs:
            cm.broadcast(m)

    def get_winner(self) -> Optional[Tuple[str, float]]:
        return min(self.user_score.items(), key=lambda x: x[1]) if self.user_score else None

    def process(self, user: str, data: str, cm: ConnectionManager):
        if not self.game_active:
            cm.send_to_user(user, "Game not started-1")
            cm.send_to_user(user, "whats your pick: \n")
            return
        pick = data.strip()
        if not pick:
            cm.send_to_user(user, "Invalid input-1")
            cm.send_to_user(user, "whats your pick: \n")
            return
        if pick == self.dest_value:
            elapsed = time.time() - self.round_started_at
            self.save_user_time(user, elapsed)
            cm.broadcast(f"{user} reached destination in {int(elapsed)}s-1")
            self.timer_seconds = 0
            return
        children = _safe_get_children(pick, self.adjacency_list)
        cm.send_to_user(user, f"{', '.join(children)}-1" if children else "Dead end-1")
        cm.send_to_user(user, "whats your pick: \n")

    def start(self):
        ConnectionManager.initialize(self.process)
        cm = ConnectionManager.instance()

        countdown = 10
        while countdown > 0:
            time.sleep(1)
            countdown -= 1
            cm.broadcast(f"Game starts in {countdown}\n-1")

        self.user_score.clear()
        self.set_two_values()
        self.show_start(cm)

        self.game_active = True
        self.timer_seconds = 60 * GAME_TIME_MINUTES
        self.round_started_at = time.time()

        while self.timer_seconds > 0:
            time.sleep(1)
            self.timer_seconds -= 1
            if self.timer_seconds % 10 == 0:
                cm.broadcast(f"{self.timer_seconds} seconds left\n-1")

        self.game_active = False
        winner = self.get_winner()
        cm.broadcast(f"Winner: {winner[0]} in {int(winner[1])}s-1" if winner else "No winner this round-1")
        cm.broadcast("Round over-1")


if __name__ == "__main__":
    GameLogic.instance().start()
