#!/usr/bin/env python3
"""
荒岛求生 - Survival Island Game
一款文字冒险游戏，玩家需要在荒岛上生存、建造、制造装备并抵御各种威胁
"""

import random
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============== 游戏配置 ==============
class Config:
    SAVE_FILE = "save.json"
    DAY_TICKS = 3
    HUNGER_DECAY = 15
    HEALTH_DECAY = 5

# ============== 数据类 ==============
class ItemType(Enum):
    RESOURCE = "resource"
    FOOD = "food"
    TOOL = "tool"
    WEAPON = "weapon"
    ARMOR = "armor"
    BUILDING = "building"

@dataclass
class Item:
    name: str
    item_type: ItemType
    description: str
    rarity: int = 1

@dataclass
class Recipe:
    name: str
    ingredients: Dict[str, int]
    result: str
    result_count: int = 1
    description: str = ""

@dataclass
class Enemy:
    name: str
    health: int
    attack: int
    defense: int
    loot: Dict[str, int]
    exp: int

@dataclass
class Event:
    name: str
    description: str
    effect_type: str
    effect_value: int
    probability: float

@dataclass
class Player:
    health: int = 100
    max_health: int = 100
    hunger: int = 100
    max_hunger: int = 100
    energy: int = 100
    max_energy: int = 100
    day: int = 1
    action_points: int = 3
    island_size: int = 1
    shelter_level: int = 0
    weapon: Optional[str] = None
    armor: Optional[str] = None
    inventory: Dict[str, int] = field(default_factory=dict)
    buildings: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    total_fish_caught: int = 0
    enemies_defeated: int = 0
    
    def is_alive(self) -> bool:
        return self.health > 0
    
    def add_item(self, item: str, count: int = 1):
        self.inventory[item] = self.inventory.get(item, 0) + count
    
    def remove_item(self, item: str, count: int = 1) -> bool:
        if self.inventory.get(item, 0) >= count:
            self.inventory[item] -= count
            if self.inventory[item] <= 0:
                del self.inventory[item]
            return True
        return False
    
    def get_item_count(self, item: str) -> int:
        return self.inventory.get(item, 0)

# ============== 游戏数据 ==============
class GameData:
    ITEMS = {
        "木材": Item("木材", ItemType.RESOURCE, "基础建筑材料"),
        "石头": Item("石头", ItemType.RESOURCE, "坚硬的石头"),
        "金属": Item("金属", ItemType.RESOURCE, "稀有金属", 3),
        "布料": Item("布料", ItemType.RESOURCE, "布料", 2),
        "绳索": Item("绳索", ItemType.RESOURCE, "绳索", 2),
        "草药": Item("草药", ItemType.RESOURCE, "野生草药", 2),
        "鱼": Item("鱼", ItemType.FOOD, "新鲜的海鱼"),
        "椰子": Item("椰子", ItemType.FOOD, "甘甜的椰子"),
        "海龟肉": Item("海龟肉", ItemType.FOOD, "营养丰富的肉", 2),
        "神秘果实": Item("神秘果实", ItemType.FOOD, "传说中的果实", 5),
        "石斧": Item("石斧", ItemType.TOOL, "基础砍伐工具"),
        "鱼竿": Item("鱼竿", ItemType.TOOL, "钓鱼工具"),
        "撒网": Item("撒网", ItemType.TOOL, "捕捞工具", 2),
        "高级撒网": Item("高级撒网", ItemType.TOOL, "高效捕捞工具", 3),
        "木棍": Item("木棍", ItemType.WEAPON, "简单的木棍"),
        "石矛": Item("石矛", ItemType.WEAPON, "尖锐的石矛"),
        "鱼叉": Item("鱼叉", ItemType.WEAPON, "专业捕猎武器", 3),
        "三叉戟": Item("三叉戟", ItemType.WEAPON, "传说中的武器", 5),
        "树叶衣": Item("树叶衣", ItemType.ARMOR, "简单的遮蔽物"),
        "兽皮甲": Item("兽皮甲", ItemType.ARMOR, "野战防护", 3),
        "贝壳甲": Item("贝壳甲", ItemType.ARMOR, "坚硬护甲", 4),
        "海神甲": Item("海神甲", ItemType.ARMOR, "传说中的护甲", 5),
        "小木屋": Item("小木屋", ItemType.BUILDING, "简单庇护所"),
        "石屋": Item("石屋", ItemType.BUILDING, "坚固住所"),
        "瞭望塔": Item("瞭望塔", ItemType.BUILDING, "预警设施"),
        "防御墙": Item("防御墙", ItemType.BUILDING, "防御设施"),
        "仓库": Item("仓库", ItemType.BUILDING, "存储设施"),
        "工坊": Item("工坊", ItemType.BUILDING, "制造设施"),
    }
    
    RECIPES = {
        "石斧": Recipe("石斧", {"木材": 2, "石头": 3}, "石斧", 1, "基础砍伐工具"),
        "鱼竿": Recipe("鱼竿", {"木材": 3, "绳索": 2}, "鱼竿", 1, "钓鱼工具"),
        "撒网": Recipe("撒网", {"绳索": 5, "布料": 3}, "撒网", 1, "基础捕捞工具"),
        "高级撒网": Recipe("高级撒网", {"撒网": 1, "金属": 3, "绳索": 5}, "高级撒网", 1, "高效捕捞工具"),
        "木棍": Recipe("木棍", {"木材": 3}, "木棍", 1, "最基础的武器"),
        "石矛": Recipe("石矛", {"木材": 2, "石头": 4, "绳索": 1}, "石矛", 1, "尖锐的石矛"),
        "鱼叉": Recipe("鱼叉", {"金属": 5, "木材": 3, "绳索": 2}, "鱼叉", 1, "专业捕猎武器"),
        "三叉戟": Recipe("三叉戟", {"金属": 10, "神秘果实": 1, "绳索": 5}, "三叉戟", 1, "传说中的武器"),
        "树叶衣": Recipe("树叶衣", {"布料": 2}, "树叶衣", 1, "简单的防护"),
        "兽皮甲": Recipe("兽皮甲", {"布料": 5, "绳索": 3}, "兽皮甲", 1, "野战防护"),
        "贝壳甲": Recipe("贝壳甲", {"石头": 10, "绳索": 5, "布料": 3}, "贝壳甲", 1, "坚硬护甲"),
        "海神甲": Recipe("海神甲", {"金属": 15, "神秘果实": 2, "贝壳甲": 1}, "海神甲", 1, "传说中的护甲"),
        "小木屋": Recipe("小木屋", {"木材": 20, "绳索": 5}, "小木屋", 1, "简单庇护所"),
        "石屋": Recipe("石屋", {"石头": 30, "木材": 10}, "石屋", 1, "坚固住所"),
        "瞭望塔": Recipe("瞭望塔", {"木材": 15, "石头": 10}, "瞭望塔", 1, "预警设施"),
        "防御墙": Recipe("防御墙", {"石头": 25, "木材": 10, "金属": 5}, "防御墙", 1, "防御设施"),
        "仓库": Recipe("仓库", {"木材": 20, "石头": 10}, "仓库", 1, "存储设施"),
        "工坊": Recipe("工坊", {"木材": 25, "石头": 20, "金属": 10}, "工坊", 1, "制造设施"),
        "烤鱼": Recipe("烤鱼", {"鱼": 1, "木材": 1}, "烤鱼", 1, "美味烤鱼"),
        "草药汤": Recipe("草药汤", {"草药": 3, "椰子": 1}, "草药汤", 1, "恢复健康"),
    }
    
    ENEMIES = {
        "海蟹": Enemy("海蟹", 20, 5, 2, {"石头": 2, "绳索": 1}, 5),
        "鲨鱼": Enemy("鲨鱼", 50, 15, 5, {"鱼": 5, "金属": 1}, 15),
        "巨型章鱼": Enemy("巨型章鱼", 80, 20, 10, {"绳索": 5, "金属": 3}, 25),
        "海蛇": Enemy("海蛇", 40, 25, 3, {"草药": 3, "金属": 2}, 20),
        "海龙王": Enemy("海龙王", 150, 35, 20, {"金属": 10, "神秘果实": 1}, 50),
    }
    
    DISASTERS = [
        Event("暴风雨", "狂风暴雨袭击了岛屿！", "damage", 20, 0.15),
        Event("海啸", "巨大的海浪席卷而来！", "damage", 35, 0.08),
        Event("旱灾", "连续干旱，食物腐烂加快", "resource_loss", 30, 0.1),
        Event("瘟疫", "神秘的疾病蔓延", "damage", 25, 0.12),
        Event("龙卷风", "龙卷风席卷岛屿", "resource_loss", 40, 0.05),
    ]
    
    SURPRISES = [
        Event("漂流瓶", "发现了一个漂流瓶！", "discovery", 1, 0.2),
        Event("神秘宝箱", "海浪冲来了一个宝箱！", "discovery", 1, 0.1),
        Event("幸存者", "遇到了另一个幸存者！", "buff", 20, 0.08),
        Event("精灵祝福", "神秘的精灵祝福了你！", "buff", 30, 0.05),
    ]

# ============== 游戏主类 ==============
class SurvivalGame:
    def __init__(self):
        self.player = Player()
        self.running = True
        self.messages: List[str] = []
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def show_banner(self):
        print("""
        ╔══════════════════════════════════════════════════════════╗
        ║                  荒 岛 求 生                              ║
        ║                Survival Island Game                       ║
        ╚══════════════════════════════════════════════════════════╝
        """)
        
    def show_status(self):
        print("\n" + "="*60)
        print(f"  📅 第 {self.player.day} 天 | 行动点: {self.player.action_points}/{Config.DAY_TICKS}")
        print("="*60)
        
        health_bar = self._make_bar(self.player.health, self.player.max_health)
        hunger_bar = self._make_bar(self.player.hunger, self.player.max_hunger)
        energy_bar = self._make_bar(self.player.energy, self.player.max_energy)
        
        print(f"  ❤️ {health_bar} 生命: {self.player.health}/{self.player.max_health}")
        print(f"  🍖 {hunger_bar} 饱食: {self.player.hunger}/{self.player.max_hunger}")
        print(f"  ⚡ {energy_bar} 体力: {self.player.energy}/{self.player.max_energy}")
        
        weapon_str = f"⚔️ {self.player.weapon}" if self.player.weapon else "⚔️ 无"
        armor_str = f"🛡️ {self.player.armor}" if self.player.armor else "🛡️ 无"
        print(f"  {weapon_str} | {armor_str}")
        print(f"  🏝️ 岛屿大小: {self.player.island_size} | 🏠 建筑: {len(self.player.buildings)}")
        print("="*60 + "\n")
        
    def _make_bar(self, current: int, maximum: int) -> str:
        filled = int(current / maximum * 20)
        empty = 20 - filled
        return f"[{'█'*filled}{'░'*empty}]"
        
    def show_inventory(self):
        print("\n📦 背包:")
        print("-" * 40)
        if not self.player.inventory:
            print("  (空)")
        else:
            for item, count in sorted(self.player.inventory.items()):
                item_data = GameData.ITEMS.get(item)
                rarity_stars = "★" * (item_data.rarity if item_data else 1)
                print(f"  • {item} x{count} {rarity_stars}")
        print("-" * 40)
        
    def show_recipes(self):
        print("\n📖 配方列表:")
        print("-" * 60)
        for name, recipe in GameData.RECIPES.items():
            ingredients_str = ", ".join([f"{i}x{c}" for i, c in recipe.ingredients.items()])
            can_craft = all(self.player.get_item_count(i) >= c for i, c in recipe.ingredients.items())
            status = "✅" if can_craft else "❌"
            print(f"  {status} {name}: {ingredients_str}")
        print("-" * 60)
        
    def fish(self) -> Dict[str, int]:
        results = {}
        base_catch = {
            "鱼": random.randint(1, 3),
            "木材": random.randint(0, 2),
            "石头": random.randint(0, 2),
        }
        
        if self.player.get_item_count("高级撒网") > 0:
            for item in base_catch:
                base_catch[item] = base_catch[item] * 2
            self.add_message("🎣 使用高级撒网，效率翻倍！")
        elif self.player.get_item_count("撒网") > 0:
            for item in base_catch:
                base_catch[item] = int(base_catch[item] * 1.5)
            self.add_message("🎣 使用撒网，效率提升！")
            
        if random.random() < 0.15:
            base_catch["金属"] = random.randint(1, 2)
            self.add_message("✨ 发现了稀有金属！")
        if random.random() < 0.1:
            base_catch["绳索"] = random.randint(1, 2)
        if random.random() < 0.08:
            base_catch["布料"] = random.randint(1, 2)
        if random.random() < 0.03:
            base_catch["神秘果实"] = 1
            self.add_message("🌟 传说中的神秘果实！")
        if random.random() < 0.05:
            base_catch["草药"] = random.randint(1, 3)
            
        for item, count in base_catch.items():
            if count > 0:
                self.player.add_item(item, count)
                results[item] = count
                
        self.player.total_fish_caught += 1
        return results
        
    def explore(self) -> str:
        events = []
        resources = random.choice([
            {"木材": random.randint(3, 6)},
            {"石头": random.randint(2, 5)},
            {"椰子": random.randint(1, 3)},
            {"草药": random.randint(1, 2)},
        ])
        
        for item, count in resources.items():
            self.player.add_item(item, count)
            events.append(f"发现了 {item} x{count}")
            
        if random.random() < 0.3:
            enemy_name = random.choice(list(GameData.ENEMIES.keys()))
            events.append(f"遭遇了 {enemy_name}！")
            return self.combat(enemy_name)
            
        return "\n".join(events)
        
    def combat(self, enemy_name: str) -> str:
        enemy = GameData.ENEMIES.get(enemy_name)
        if not enemy:
            return "敌人数据错误"
            
        self.add_message(f"\n⚔️ 战斗开始！你遇到了 {enemy_name}！")
        
        player_attack = 10
        player_defense = 5
        
        weapon_data = GameData.ITEMS.get(self.player.weapon) if self.player.weapon else None
        if weapon_data:
            player_attack += (weapon_data.rarity * 5)
            
        armor_data = GameData.ITEMS.get(self.player.armor) if self.player.armor else None
        if armor_data:
            player_defense += (armor_data.rarity * 3)
            
        if "防御墙" in self.player.buildings:
            player_defense += 10
            
        enemy_hp = enemy.health
        
        while enemy_hp > 0 and self.player.is_alive():
            damage = max(1, player_attack - enemy.defense + random.randint(-3, 3))
            enemy_hp -= damage
            self.add_message(f"⚔️ 你造成了 {damage} 点伤害！敌人剩余HP: {max(0, enemy_hp)}")
            
            if enemy_hp <= 0:
                break
                
            enemy_damage = max(1, enemy.attack - player_defense + random.randint(-2, 2))
            self.player.health -= enemy_damage
            self.add_message(f"💥 {enemy_name} 造成了 {enemy_damage} 点伤害！你的HP: {self.player.health}")
            
            time.sleep(0.3)
            
        if self.player.is_alive():
            self.add_message(f"🏆 胜利！击败了 {enemy_name}！")
            for item, count in enemy.loot.items():
                self.player.add_item(item, count)
                self.add_message(f"  获得战利品: {item} x{count}")
            self.player.enemies_defeated += 1
            return f"🎉 胜利！获得: {', '.join([f'{i}x{c}' for i, c in enemy.loot.items()])}"
        else:
            return "💀 你被击败了..."
            
    def craft(self, recipe_name: str) -> bool:
        recipe = GameData.RECIPES.get(recipe_name)
        if not recipe:
            self.add_message("❌ 配方不存在！")
            return False
            
        for item, count in recipe.ingredients.items():
            if self.player.get_item_count(item) < count:
                self.add_message(f"❌ 材料不足：需要 {item} x{count}")
                return False
                
        for item, count in recipe.ingredients.items():
            self.player.remove_item(item, count)
            
        self.player.add_item(recipe.result, recipe.result_count)
        self.add_message(f"✅ 成功制造了 {recipe.result}！")
        
        item_data = GameData.ITEMS.get(recipe.result)
        if item_data:
            if item_data.item_type == ItemType.WEAPON:
                self.player.weapon = recipe.result
                self.add_message(f"⚔️ 自动装备了 {recipe.result}")
            elif item_data.item_type == ItemType.ARMOR:
                self.player.armor = recipe.result
                self.add_message(f"🛡️ 自动装备了 {recipe.result}")
                
        return True
        
    def build(self, building_name: str) -> bool:
        recipe = GameData.RECIPES.get(building_name)
        if not recipe:
            self.add_message("❌ 建筑不存在！")
            return False
            
        item_data = GameData.ITEMS.get(building_name)
        if not item_data or item_data.item_type != ItemType.BUILDING:
            self.add_message("❌ 这不是一个建筑！")
            return False
            
        if building_name in self.player.buildings:
            self.add_message("❌ 已经建造过了！")
            return False
            
        for item, count in recipe.ingredients.items():
            if self.player.get_item_count(item) < count:
                self.add_message(f"❌ 材料不足：需要 {item} x{count}")
                return False
                
        for item, count in recipe.ingredients.items():
            self.player.remove_item(item, count)
            
        self.player.buildings.append(building_name)
        self.add_message(f"🏗️ 成功建造了 {building_name}！")
        
        if building_name == "小木屋":
            self.player.shelter_level = 1
        elif building_name == "石屋":
            self.player.shelter_level = 2
            
        return True
        
    def expand_island(self) -> bool:
        cost = self.player.island_size * 10
        
        if self.player.get_item_count("木材") < cost:
            self.add_message(f"❌ 需要木材 x{cost}")
            return False
        if self.player.get_item_count("石头") < cost:
            self.add_message(f"❌ 需要石头 x{cost}")
            return False
            
        self.player.remove_item("木材", cost)
        self.player.remove_item("石头", cost)
        self.player.island_size += 1
        self.add_message(f"🏝️ 岛屿扩展成功！现在大小为 {self.player.island_size}")
        return True
        
    def eat(self, food: str) -> bool:
        food_values = {"鱼": 20, "烤鱼": 35, "椰子": 15, "海龟肉": 30, "神秘果实": 50}
        
        if self.player.get_item_count(food) <= 0:
            self.add_message(f"❌ 你没有 {food}")
            return False
            
        value = food_values.get(food, 10)
        self.player.hunger = min(self.player.max_hunger, self.player.hunger + value)
        self.player.remove_item(food, 1)
        self.add_message(f"🍖 吃了 {food}，恢复了 {value} 点饱食度！")
        return True
        
    def heal(self) -> bool:
        if self.player.get_item_count("草药") < 3:
            self.add_message("❌ 需要草药 x3")
            return False
            
        self.player.remove_item("草药", 3)
        heal_amount = 30
        self.player.health = min(self.player.max_health, self.player.health + heal_amount)
        self.add_message(f"💚 使用草药治疗，恢复了 {heal_amount} 点生命！")
        return True
        
    def rest(self):
        self.add_message("😴 你休息了一会儿...")
        rest_amount = 30 + (10 * self.player.shelter_level)
        self.player.energy = min(self.player.max_energy, self.player.energy + rest_amount)
        self.player.hunger = max(0, self.player.hunger - 10)
        self.add_message(f"⚡ 恢复了 {rest_amount} 点体力")
        
    def trigger_event(self):
        disaster_mod = 0.5 if "瞭望塔" in self.player.buildings else 1.0
        
        for disaster in GameData.DISASTERS:
            if random.random() < disaster.probability * disaster_mod:
                self.handle_disaster(disaster)
                return
                
        for surprise in GameData.SURPRISES:
            if random.random() < surprise.probability:
                self.handle_surprise(surprise)
                return
                
    def handle_disaster(self, disaster: Event):
        self.add_message(f"\n⚠️ {disaster.name}！")
        self.add_message(f"   {disaster.description}")
        
        if disaster.effect_type == "damage":
            damage = disaster.effect_value
            if "防御墙" in self.player.buildings:
                damage = int(damage * 0.6)
                self.add_message("   🧱 防御墙减免了部分伤害！")
            if "石屋" in self.player.buildings:
                damage = int(damage * 0.8)
            self.player.health = max(0, self.player.health - damage)
            self.add_message(f"   💔 受到 {damage} 点伤害")
            
        elif disaster.effect_type == "resource_loss":
            lost = int(disaster.effect_value / 100 * sum(self.player.inventory.values()))
            if lost > 0:
                self.add_message(f"   📦 损失了约 {lost} 个物品")
                for _ in range(min(lost, len(self.player.inventory))):
                    if self.player.inventory:
                        item = random.choice(list(self.player.inventory.keys()))
                        self.player.remove_item(item, 1)
                        
    def handle_surprise(self, surprise: Event):
        self.add_message(f"\n✨ {surprise.name}！")
        self.add_message(f"   {surprise.description}")
        
        if surprise.effect_type == "discovery":
            rewards = random.choice([
                {"金属": 3, "绳索": 2},
                {"草药": 5, "椰子": 3},
                {"神秘果实": 1},
                {"金属": 5, "布料": 3},
            ])
            for item, count in rewards.items():
                self.player.add_item(item, count)
                self.add_message(f"   🎁 获得 {item} x{count}")
                
        elif surprise.effect_type == "buff":
            self.player.health = min(self.player.max_health, 
                                     self.player.health + surprise.effect_value)
            self.player.energy = min(self.player.max_energy,
                                     self.player.energy + surprise.effect_value)
            self.add_message(f"   💚 恢复了 {surprise.effect_value} 点生命和体力")
            
    def next_day(self):
        self.player.day += 1
        self.player.action_points = Config.DAY_TICKS
        
        if self.player.hunger <= 0:
            self.player.health -= Config.HEALTH_DECAY
            self.add_message("⚠️ 你快饿死了！生命值下降！")
            
        self.player.hunger = max(0, self.player.hunger - Config.HUNGER_DECAY)
        self.trigger_event()
        self.add_message(f"\n🌅 第 {self.player.day} 天开始了...")
        
    def add_message(self, msg: str):
        self.messages.append(msg)
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
            
    def show_messages(self):
        if self.messages:
            print("\n" + "="*60)
            print("📜 消息日志")
            print("="*60)
            for msg in self.messages[-10:]:
                print(msg)
            print("="*60 + "\n")
            self.messages = []
            
    def save_game(self):
        save_data = asdict(self.player)
        with open(Config.SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        self.add_message("💾 游戏已保存！")
        
    def load_game(self) -> bool:
        if not os.path.exists(Config.SAVE_FILE):
            return False
        try:
            with open(Config.SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.player = Player(**data)
            return True
        except:
            return False
            
    def check_achievements(self):
        achievements = []
        
        if self.player.day >= 10 and "day10" not in self.player.achievements:
            self.player.achievements.append("day10")
            achievements.append("🏆 生存大师：存活10天")
            
        if self.player.total_fish_caught >= 50 and "fisher50" not in self.player.achievements:
            self.player.achievements.append("fisher50")
            achievements.append("🏆 渔夫：捕捞50次")
            
        if self.player.enemies_defeated >= 10 and "warrior10" not in self.player.achievements:
            self.player.achievements.append("warrior10")
            achievements.append("🏆 战士：击败10个敌人")
            
        for ach in achievements:
            self.add_message(ach)
            
    def game_over(self):
        self.clear_screen()
        self.show_banner()
        print("\n" + "="*60)
        print("                      💀 游戏结束 💀                      ")
        print("="*60)
        print(f"\n  你在第 {self.player.day} 天死亡...")
        print(f"  🐟 总捕捞次数: {self.player.total_fish_caught}")
        print(f"  ⚔️ 击败敌人: {self.player.enemies_defeated}")
        print(f"  🏆 成就: {len(self.player.achievements)} 个")
        print(f"  🏝️ 岛屿大小: {self.player.island_size}")
        print("\n" + "="*60)
        
        if os.path.exists(Config.SAVE_FILE):
            os.remove(Config.SAVE_FILE)
            
    def victory(self):
        self.clear_screen()
        self.show_banner()
        print("\n" + "="*60)
        print("                  🎉 恭喜通关！🎉                     ")
        print("="*60)
        print(f"\n  你成功在荒岛上生存了下来！")
        print(f"  📅 生存天数: {self.player.day}")
        print(f"  🐟 总捕捞次数: {self.player.total_fish_caught}")
        print(f"  ⚔️ 击败敌人: {self.player.enemies_defeated}")
        print(f"  🏆 成就: {len(self.player.achievements)} 个")
        print(f"  🏝️ 岛屿大小: {self.player.island_size}")
        print("\n" + "="*60)
        
        if os.path.exists(Config.SAVE_FILE):
            os.remove(Config.SAVE_FILE)
            
    def show_menu(self) -> str:
        print("\n🎮 行动菜单:")
        print("-" * 40)
        print("  1. 🎣 撒网捕捞     2. 🗺️ 探索岛屿")
        print("  3. 🍖 进食        4. 💚 治疗")
        print("  5. 😴 休息        6. 🔨 制造")
        print("  7. 🏗️ 建造        8. 🏝️ 扩展岛屿")
        print("  9. 📦 背包        10. 📖 配方")
        print("  11. 🏠 建筑        12. 💾 保存")
        print("  13. 🌙 下一天      0. 🚪 退出")
        print("-" * 40)
        return input("  请选择行动: ").strip()
        
    def run(self):
        self.clear_screen()
        self.show_banner()
        
        # 尝试加载存档
        if os.path.exists(Config.SAVE_FILE):
            choice = input("发现存档，是否继续？(y/n): ").strip().lower()
            if choice == 'y':
                self.load_game()
                self.add_message("📂 存档已加载！")
            else:
                os.remove(Config.SAVE_FILE)
                
        input("\n按回车开始游戏...")
        
        while self.running and self.player.is_alive():
            self.clear_screen()
            self.show_banner()
            self.show_status()
            self.show_messages()
            self.check_achievements()
            
            # 检查胜利条件
            if self.player.day >= 30:
                self.victory()
                break
                
            # 检查行动点
            if self.player.action_points <= 0:
                print("\n⚠️ 今天没有行动点了！")
                input("按回车进入下一天...")
                self.next_day()
                continue
                
            choice = self.show_menu()
            
            if choice == "1":
                print("\n🎣 撒网捕捞中...")
                results = self.fish()
                print(f"\n捕捞结果:")
                for item, count in results.items():
                    print(f"  • {item} x{count}")
                self.player.action_points -= 1
                
            elif choice == "2":
                print("\n🗺️ 探索岛屿...")
                result = self.explore()
                print(f"\n{result}")
                self.player.action_points -= 1
                
            elif choice == "3":
                self.show_inventory()
                food = input("输入要吃的食物: ").strip()
                self.eat(food)
                
            elif choice == "4":
                self.heal()
                
            elif choice == "5":
                self.rest()
                self.player.action_points -= 1
                
            elif choice == "6":
                self.show_recipes()
                recipe = input("输入要制造的物品: ").strip()
                self.craft(recipe)
                
            elif choice == "7":
                print("\n可建造:")
                for name, recipe in GameData.RECIPES.items():
                    item = GameData.ITEMS.get(name)
                    if item and item.item_type == ItemType.BUILDING:
                        if name not in self.player.buildings:
                            print(f"  • {name}: {recipe.description}")
                building = input("\n输入要建造的建筑: ").strip()
                self.build(building)
                
            elif choice == "8":
                self.expand_island()
                self.player.action_points -= 1
                
            elif choice == "9":
                self.show_inventory()
                
            elif choice == "10":
                self.show_recipes()
                
            elif choice == "11":
                self.show_buildings()
                
            elif choice == "12":
                self.save_game()
                
            elif choice == "13":
                confirm = input("确定进入下一天？(y/n): ").strip().lower()
                if confirm == 'y':
                    self.next_day()
                    
            elif choice == "0":
                self.running = False
                print("\n👋 再见！")
                
            if self.player.action_points <= 0 or choice in ["3", "4", "9", "10", "11", "12"]:
                pass
            
            if choice not in ["0"]:
                input("\n按回车继续...")
                
        if not self.player.is_alive():
            self.game_over()

# ============== 主程序入口 ==============
if __name__ == "__main__":
    game = SurvivalGame()
    game.run()
