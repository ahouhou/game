"""Player, Quest dataclasses."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Player:
    # core stats
    health: int = 100
    max_health: int = 100
    hunger: int = 100
    energy: int = 100
    day: int = 1
    exp: int = 0
    level: int = 1
    # equipment
    weapon: Optional[str] = None
    armor: Optional[str] = None
    dur: Dict[str, int] = field(default_factory=dict)   # item_name → remaining durability
    # inventory
    inventory: Dict[str, int] = field(default_factory=dict)
    # progress
    fish_count: int = 0
    explore_count: int = 0
    enemy_kills: int = 0
    build_count: int = 0
    # buildings (names)
    buildings: List[str] = field(default_factory=list)
    # achievements
    achievements: List[str] = field(default_factory=list)
    # story
    pages_found: List[int] = field(default_factory=list)
    ending_unlocked: str = ""

    def has(self, item: str) -> int:
        return self.inventory.get(item, 0)

    def add(self, item: str, n: int = 1):
        self.inventory[item] = self.has(item) + n

    def use(self, item: str, n: int = 1) -> bool:
        if self.has(item) < n:
            return False
        self.inventory[item] -= n
        if self.inventory[item] <= 0:
            del self.inventory[item]
        return True

    @property
    def patk(self) -> int:
        b = 10
        if self.weapon:
            from data import WEAPON_ATK
            b += WEAPON_ATK.get(self.weapon, 0)
        return b

    @property
    def pdef(self) -> int:
        b = 0
        if self.armor:
            from data import ARMOR_DFS
            b += ARMOR_DFS.get(self.armor, 0)
        return b

    def gain_exp(self, amount: int):
        self.exp += amount
        threshold = self.level * 50
        while self.exp >= threshold:
            self.exp -= threshold
            self.level += 1
            self.max_health += 10
            self.health = min(self.health + 20, self.max_health)


@dataclass
class Quest:
    qtype: str          # collect / build / combat / survive
    title: str
    desc: str
    target: str         # item name / building name / "day" / "kill"
    need: int
    reward: dict        # exp / item / hp etc
    current: int = 0
    completed: bool = False


@dataclass
class StoryPage:
    page_id: int
    title: str
    text: str
    mood: str
