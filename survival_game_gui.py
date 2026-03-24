#!/usr/bin/env python3
"""
荒岛求生 - Survival Island Game (GUI Version)
使用 Pygame 实现的图形界面生存游戏
"""

import pygame
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import time

# ============== 初始化 Pygame ==============
pygame.init()

# ============== 常量配置 ==============
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

# 颜色定义
class Colors:
    # 主题色
    OCEAN_BLUE = (25, 118, 210)
    SAND_YELLOW = (255, 193, 7)
    FOREST_GREEN = (56, 142, 60)
    DARK_BROWN = (62, 39, 35)
    STONE_GRAY = (117, 117, 117)
    
    # UI色
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    DARK_BG = (20, 20, 30)
    LIGHT_BG = (240, 240, 245)
    
    # 状态色
    HEALTH_RED = (244, 67, 54)
    HUNGER_ORANGE = (255, 152, 0)
    ENERGY_YELLOW = (255, 235, 59)
    SUCCESS_GREEN = (76, 175, 80)
    WARNING_RED = (255, 87, 34)
    
    # 渐变色
    SUNSET_ORANGE = (255, 107, 53)
    STORM_GRAY = (96, 125, 139)

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
    icon_color: Tuple = (200, 200, 200)

@dataclass
class Building:
    name: str
    x: int
    y: int
    width: int = 60
    height: int = 60
    color: Tuple = Colors.DARK_BROWN
    description: str = ""

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    lifetime: float
    max_lifetime: float
    color: Tuple
    size: int = 5

@dataclass
class Player:
    health: int = 100
    max_health: int = 100
    hunger: int = 100
    max_hunger: int = 100
    energy: int = 100
    max_energy: int = 100
    day: int = 1
    island_size: int = 1
    weapon: Optional[str] = None
    armor: Optional[str] = None
    inventory: Dict[str, int] = field(default_factory=dict)
    buildings: List[Building] = field(default_factory=list)
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
        "木材": Item("木材", ItemType.RESOURCE, "基础建筑材料", 1, (139, 69, 19)),
        "石头": Item("石头", ItemType.RESOURCE, "坚硬的石头", 1, (128, 128, 128)),
        "金属": Item("金属", ItemType.RESOURCE, "稀有金属", 3, (192, 192, 192)),
        "布料": Item("布料", ItemType.RESOURCE, "布料", 2, (210, 180, 140)),
        "绳索": Item("绳索", ItemType.RESOURCE, "绳索", 2, (160, 82, 45)),
        "草药": Item("草药", ItemType.RESOURCE, "野生草药", 2, (34, 139, 34)),
        "鱼": Item("鱼", ItemType.FOOD, "新鲜的海鱼", 1, (255, 140, 0)),
        "椰子": Item("椰子", ItemType.FOOD, "甘甜的椰子", 1, (184, 134, 11)),
        "烤鱼": Item("烤鱼", ItemType.FOOD, "美味烤鱼", 1, (255, 69, 0)),
        "石斧": Item("石斧", ItemType.TOOL, "基础砍伐工具", 1, (105, 105, 105)),
        "撒网": Item("撒网", ItemType.TOOL, "捕捞工具", 2, (169, 169, 169)),
        "高级撒网": Item("高级撒网", ItemType.TOOL, "高效捕捞工具", 3, (211, 211, 211)),
        "木棍": Item("木棍", ItemType.WEAPON, "简单的木棍", 1, (139, 69, 19)),
        "石矛": Item("石矛", ItemType.WEAPON, "尖锐的石矛", 2, (105, 105, 105)),
        "鱼叉": Item("鱼叉", ItemType.WEAPON, "专业捕猎武器", 3, (192, 192, 192)),
        "三叉戟": Item("三叉戟", ItemType.WEAPON, "传说中的武器", 5, (255, 215, 0)),
        "树叶衣": Item("树叶衣", ItemType.ARMOR, "简单的遮蔽物", 1, (34, 139, 34)),
        "兽皮甲": Item("兽皮甲", ItemType.ARMOR, "野战防护", 3, (139, 69, 19)),
        "贝壳甲": Item("贝壳甲", ItemType.ARMOR, "坚硬护甲", 4, (240, 255, 240)),
        "海神甲": Item("海神甲", ItemType.ARMOR, "传说中的护甲", 5, (0, 191, 255)),
    }
    
    BUILDINGS = {
        "小木屋": {"color": (139, 69, 19), "desc": "简单庇护所", "cost": {"木材": 20, "绳索": 5}},
        "石屋": {"color": (128, 128, 128), "desc": "坚固住所", "cost": {"石头": 30, "木材": 10}},
        "瞭望塔": {"color": (184, 134, 11), "desc": "预警设施", "cost": {"木材": 15, "石头": 10}},
        "防御墙": {"color": (105, 105, 105), "desc": "防御设施", "cost": {"石头": 25, "木材": 10, "金属": 5}},
        "冶炼屋": {"color": (255, 69, 0), "desc": "金属冶炼", "cost": {"石头": 20, "金属": 5, "木材": 15}},
        "仓库": {"color": (210, 180, 140), "desc": "存储设施", "cost": {"木材": 20, "石头": 10}},
        "工坊": {"color": (192, 192, 192), "desc": "制造设施", "cost": {"木材": 25, "石头": 20, "金属": 10}},
    }

# ============== 粒子系统 ==============
class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []
    
    def add_particle(self, x: float, y: float, vx: float, vy: float, 
                     lifetime: float, color: Tuple, size: int = 5):
        particle = Particle(x, y, vx, vy, lifetime, lifetime, color, size)
        self.particles.append(particle)
    
    def add_burst(self, x: float, y: float, count: int, color: Tuple, speed: float = 3):
        """爆发效果"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.add_particle(x, y, vx, vy, 1.0, color, random.randint(3, 8))
    
    def add_rain(self, x: float, y: float, count: int):
        """雨效果"""
        for _ in range(count):
            vx = random.uniform(-2, 2)
            vy = random.uniform(3, 6)
            self.add_particle(x + random.randint(-50, 50), y, vx, vy, 2.0, Colors.STORM_GRAY, 2)
    
    def update(self, dt: float):
        for particle in self.particles[:]:
            particle.lifetime -= dt
            particle.x += particle.vx
            particle.y += particle.vy
            particle.vy += 0.1  # 重力
            
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def draw(self, surface: pygame.Surface):
        for particle in self.particles:
            alpha = int(255 * (particle.lifetime / particle.max_lifetime))
            color = tuple(min(255, c + (255 - c) * (1 - particle.lifetime / particle.max_lifetime)) 
                         for c in particle.color)
            pygame.draw.circle(surface, color, (int(particle.x), int(particle.y)), particle.size)

# ============== 灾害特效 ==============
class DisasterEffect:
    def __init__(self, disaster_type: str, x: float, y: float):
        self.type = disaster_type
        self.x = x
        self.y = y
        self.duration = 2.0
        self.elapsed = 0.0
        self.particles = ParticleSystem()
        
        if disaster_type == "暴风雨":
            self._init_storm()
        elif disaster_type == "海啸":
            self._init_tsunami()
        elif disaster_type == "龙卷风":
            self._init_tornado()
        elif disaster_type == "瘟疫":
            self._init_plague()
    
    def _init_storm(self):
        """暴风雨特效"""
        for _ in range(30):
            self.particles.add_rain(self.x, self.y, 1)
    
    def _init_tsunami(self):
        """海啸特效"""
        for _ in range(50):
            angle = random.uniform(-math.pi/4, math.pi/4)
            vx = math.cos(angle) * 8
            vy = math.sin(angle) * 8
            self.particles.add_particle(self.x, self.y, vx, vy, 1.5, Colors.OCEAN_BLUE, 8)
    
    def _init_tornado(self):
        """龙卷风特效"""
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(10, 50)
            vx = math.cos(angle) * 5 - (self.y - 450) * 0.01
            vy = math.sin(angle) * 5 + (self.x - 700) * 0.01
            x = self.x + math.cos(angle) * distance
            y = self.y + math.sin(angle) * distance
            self.particles.add_particle(x, y, vx, vy, 1.5, Colors.STORM_GRAY, 6)
    
    def _init_plague(self):
        """瘟疫特效"""
        for _ in range(30):
            self.particles.add_particle(self.x + random.randint(-100, 100), 
                                       self.y + random.randint(-100, 100),
                                       random.uniform(-1, 1), random.uniform(-1, 1),
                                       1.5, (139, 0, 139), 4)
    
    def update(self, dt: float):
        self.elapsed += dt
        self.particles.update(dt)
        
        # 持续生成粒子
        if self.elapsed < self.duration:
            if self.type == "暴风雨":
                self.particles.add_rain(self.x, self.y, 2)
            elif self.type == "龙卷风":
                for _ in range(3):
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.uniform(10, 50)
                    vx = math.cos(angle) * 5
                    vy = math.sin(angle) * 5
                    x = self.x + math.cos(angle) * distance
                    y = self.y + math.sin(angle) * distance
                    self.particles.add_particle(x, y, vx, vy, 1.0, Colors.STORM_GRAY, 5)
    
    def draw(self, surface: pygame.Surface):
        self.particles.draw(surface)
    
    def is_finished(self) -> bool:
        return self.elapsed >= self.duration

# ============== 主游戏类 ==============
class SurvivalGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🏝️ 荒岛求生 - Survival Island")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        self.player = Player()
        self.particles = ParticleSystem()
        self.disasters: List[DisasterEffect] = []
        self.messages: List[Tuple[str, float]] = []  # (message, lifetime)
        self.running = True
        self.game_state = "playing"  # playing, game_over, victory
        self.selected_building = None
        self.action_points = 3
        
        # 初始化物品
        self.player.add_item("木材", 10)
        self.player.add_item("石头", 5)
        self.player.add_item("鱼", 3)
    
    def add_message(self, text: str, duration: float = 3.0):
        """添加消息"""
        self.messages.append((text, duration))
    
    def add_disaster(self, disaster_type: str):
        """触发灾害"""
        x = SCREEN_WIDTH // 2
        y = SCREEN_HEIGHT // 2
        self.disasters.append(DisasterEffect(disaster_type, x, y))
        self.add_message(f"⚠️ {disaster_type}！")
    
    def draw_status_bar(self, x: int, y: int, width: int, height: int, 
                       current: int, maximum: int, color: Tuple, label: str):
        """绘制状态条"""
        # 背景
        pygame.draw.rect(self.screen, Colors.DARK_BG, (x, y, width, height))
        pygame.draw.rect(self.screen, color, (x, y, width, height), 2)
        
        # 填充
        fill_width = int(width * (current / maximum))
        pygame.draw.rect(self.screen, color, (x, y, fill_width, height))
        
        # 文字
        text = self.font_tiny.render(f"{label}: {current}/{maximum}", True, Colors.WHITE)
        self.screen.blit(text, (x + 5, y + 2))
    
    def draw_inventory(self):
        """绘制背包"""
        x, y = 20, 150
        width = 300
        
        # 背景
        pygame.draw.rect(self.screen, Colors.DARK_BG, (x - 10, y - 10, width + 20, 400))
        pygame.draw.rect(self.screen, Colors.OCEAN_BLUE, (x - 10, y - 10, width + 20, 400), 2)
        
        # 标题
        title = self.font_medium.render("📦 背包", True, Colors.SAND_YELLOW)
        self.screen.blit(title, (x, y))
        
        # 物品列表
        y += 40
        for item, count in sorted(self.player.inventory.items()):
            item_data = GameData.ITEMS.get(item)
            color = item_data.icon_color if item_data else Colors.WHITE
            
            # 物品框
            pygame.draw.rect(self.screen, color, (x, y, 20, 20))
            pygame.draw.rect(self.screen, Colors.WHITE, (x, y, 20, 20), 1)
            
            # 物品名和数量
            text = self.font_tiny.render(f"{item} x{count}", True, Colors.WHITE)
            self.screen.blit(text, (x + 30, y))
            
            y += 30
    
    def draw_buildings(self):
        """绘制建筑"""
        x, y = SCREEN_WIDTH - 320, 150
        width = 300
        
        # 背景
        pygame.draw.rect(self.screen, Colors.DARK_BG, (x - 10, y - 10, width + 20, 400))
        pygame.draw.rect(self.screen, Colors.FOREST_GREEN, (x - 10, y - 10, width + 20, 400), 2)
        
        # 标题
        title = self.font_medium.render("🏗️ 建筑", True, Colors.SAND_YELLOW)
        self.screen.blit(title, (x, y))
        
        # 建筑列表
        y += 40
        for building in self.player.buildings:
            text = self.font_tiny.render(f"🏠 {building.name}", True, Colors.SUCCESS_GREEN)
            self.screen.blit(text, (x, y))
            y += 25
    
    def draw_island(self):
        """绘制岛屿"""
        island_x = SCREEN_WIDTH // 2 - 150
        island_y = SCREEN_HEIGHT // 2 - 150
        island_size = 300 + (self.player.island_size - 1) * 50
        
        # 绘制岛屿
        pygame.draw.ellipse(self.screen, Colors.SAND_YELLOW, 
                           (island_x, island_y, island_size, island_size))
        pygame.draw.ellipse(self.screen, Colors.DARK_BROWN, 
                           (island_x, island_y, island_size, island_size), 3)
        
        # 绘制建筑
        for building in self.player.buildings:
            pygame.draw.rect(self.screen, building.color, 
                            (building.x, building.y, building.width, building.height))
            pygame.draw.rect(self.screen, Colors.WHITE, 
                            (building.x, building.y, building.width, building.height), 2)
            
            # 建筑名称
            name_text = self.font_tiny.render(building.name[:4], True, Colors.WHITE)
            self.screen.blit(name_text, (building.x + 5, building.y + 5))
    
    def draw_ui(self):
        """绘制UI"""
        # 顶部状态栏
        self.draw_status_bar(20, 20, 200, 20, self.player.health, 
                            self.player.max_health, Colors.HEALTH_RED, "❤️ 生命")
        self.draw_status_bar(20, 50, 200, 20, self.player.hunger, 
                            self.player.max_hunger, Colors.HUNGER_ORANGE, "🍖 饱食")
        self.draw_status_bar(20, 80, 200, 20, self.player.energy, 
                            self.player.max_energy, Colors.ENERGY_YELLOW, "⚡ 体力")
        
        # 日期和行动点
        day_text = self.font_medium.render(f"📅 第 {self.player.day} 天", True, Colors.SAND_YELLOW)
        self.screen.blit(day_text, (SCREEN_WIDTH - 250, 20))
        
        action_text = self.font_small.render(f"行动点: {self.action_points}/3", True, Colors.WHITE)
        self.screen.blit(action_text, (SCREEN_WIDTH - 250, 60))
        
        # 装备
        weapon_text = self.font_tiny.render(f"⚔️ {self.player.weapon or '无'}", True, Colors.WHITE)
        armor_text = self.font_tiny.render(f"🛡️ {self.player.armor or '无'}", True, Colors.WHITE)
        self.screen.blit(weapon_text, (SCREEN_WIDTH - 250, 100))
        self.screen.blit(armor_text, (SCREEN_WIDTH - 250, 130))
    
    def draw_messages(self):
        """绘制消息"""
        y = SCREEN_HEIGHT - 100
        for message, _ in self.messages[-5:]:
            text = self.font_small.render(message, True, Colors.SUCCESS_GREEN)
            self.screen.blit(text, (20, y))
            y -= 30
    
    def draw_buttons(self):
        """绘制按钮"""
        buttons = [
            ("🎣 捕捞", 20, SCREEN_HEIGHT - 60),
            ("🗺️ 探索", 150, SCREEN_HEIGHT - 60),
            ("🍖 进食", 280, SCREEN_HEIGHT - 60),
            ("🏗️ 建造", 410, SCREEN_HEIGHT - 60),
            ("🌙 下一天", 540, SCREEN_HEIGHT - 60),
        ]
        
        for text, x, y in buttons:
            pygame.draw.rect(self.screen, Colors.OCEAN_BLUE, (x, y, 120, 40))
            pygame.draw.rect(self.screen, Colors.WHITE, (x, y, 120, 40), 2)
            
            btn_text = self.font_small.render(text, True, Colors.WHITE)
            text_rect = btn_text.get_rect(center=(x + 60, y + 20))
            self.screen.blit(btn_text, text_rect)
    
    def draw(self):
        """绘制所有内容"""
        self.screen.fill(Colors.DARK_BG)
        
        # 绘制背景（海洋）
        pygame.draw.rect(self.screen, Colors.OCEAN_BLUE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        
        # 绘制岛屿
        self.draw_island()
        
        # 绘制灾害特效
        for disaster in self.disasters:
            disaster.draw(self.screen)
        
        # 绘制粒子
        self.particles.draw(self.screen)
        
        # 绘制UI
        self.draw_ui()
        self.draw_inventory()
        self.draw_buildings()
        self.draw_messages()
        self.draw_buttons()
        
        pygame.display.flip()
    
    def fish(self):
        """捕捞"""
        catch = {
            "鱼": random.randint(2, 5),
            "木材": random.randint(0, 2),
            "石头": random.randint(0, 2),
        }
        
        if random.random() < 0.2:
            catch["金属"] = random.randint(1, 2)
        
        for item, count in catch.items():
            self.player.add_item(item, count)
        
        self.player.total_fish_caught += 1
        self.action_points -= 1
        self.player.hunger = max(0, self.player.hunger - 15)
        
        # 粒子效果
        self.particles.add_burst(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 20, Colors.OCEAN_BLUE, 4)
        
        self.add_message(f"🎣 捕捞成功！获得: {', '.join([f'{i}x{c}' for i, c in catch.items()])}")
    
    def explore(self):
        """探索"""
        resources = random.choice([
            {"木材": random.randint(3, 6)},
            {"石头": random.randint(2, 5)},
            {"椰子": random.randint(1, 3)},
        ])
        
        for item, count in resources.items():
            self.player.add_item(item, count)
        
        self.action_points -= 1
        self.player.hunger = max(0, self.player.hunger - 20)
        self.player.energy = max(0, self.player.energy - 15)
        
        # 粒子效果
        self.particles.add_burst(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 15, Colors.FOREST_GREEN, 3)
        
        self.add_message(f"🗺️ 探索发现: {', '.join([f'{i}x{c}' for i, c in resources.items()])}")
    
    def eat(self):
        """进食"""
        if self.player.get_item_count("鱼") > 0:
            self.player.remove_item("鱼", 1)
            self.player.hunger = min(100, self.player.hunger + 20)
            self.add_message("🍖 吃了鱼，恢复了20点饱食度！")
            self.particles.add_burst(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 10, Colors.HUNGER_ORANGE, 2)
        else:
            self.add_message("❌ 没有食物！")
    
    def build(self):
        """建造"""
        if self.selected_building is None:
            self.add_message("❌ 请先选择建筑类型！")
            return
        
        building_name = self.selected_building
        building_data = GameData.BUILDINGS.get(building_name)
        
        if not building_data:
            return
        
        # 检查材料
        for item, count in building_data["cost"].items():
            if self.player.get_item_count(item) < count:
                self.add_message(f"❌ 材料不足：需要 {item} x{count}")
                return
        
        # 消耗材料
        for item, count in building_data["cost"].items():
            self.player.remove_item(item, count)
        
        # 添加建筑
        x = random.randint(SCREEN_WIDTH // 2 - 100, SCREEN_WIDTH // 2 + 100)
        y = random.randint(SCREEN_HEIGHT // 2 - 100, SCREEN_HEIGHT // 2 + 100)
        
        building = Building(building_name, x, y, 60, 60, building_data["color"], building_data["desc"])
        self.player.buildings.append(building)
        
        self.action_points -= 1
        self.player.energy = max(0, self.player.energy - 20)
        
        # 粒子效果
        self.particles.add_burst(x, y, 30, building_data["color"], 5)
        
        self.add_message(f"🏗️ 成功建造了 {building_name}！")
    
    def next_day(self):
        """进入下一天"""
        self.player.day += 1
        self.action_points = 3
        
        # 饥饿扣血
        if self.player.hunger <= 0:
            self.player.health -= 10
            self.add_message("⚠️ 你快饿死了！")
        
        self.player.hunger = max(0, self.player.hunger - 15)
        
        # 随机灾害
        if random.random() < 0.3:
            disaster = random.choice(["暴风雨", "海啸", "龙卷风", "瘟疫"])
            self.add_disaster(disaster)
            
            # 灾害伤害
            if disaster == "暴风雨":
                self.player.health = max(0, self.player.health - 15)
            elif disaster == "海啸":
                self.player.health = max(0, self.player.health - 25)
            elif disaster == "龙卷风":
                self.player.health = max(0, self.player.health - 20)
            elif disaster == "瘟疫":
                self.player.health = max(0, self.player.health - 18)
        
        # 检查胜利
        if self.player.day >= 30:
            self.game_state = "victory"
        
        # 检查失败
        if not self.player.is_alive():
            self.game_state = "game_over"
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                
                # 检查按钮点击
                if SCREEN_HEIGHT - 60 <= y <= SCREEN_HEIGHT - 20:
                    if 20 <= x <= 140:
                        self.fish()
                    elif 150 <= x <= 270:
                        self.explore()
                    elif 280 <= x <= 400:
                        self.eat()
                    elif 410 <= x <= 530:
                        self.build()
                    elif 540 <= x <= 660:
                        self.next_day()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.selected_building = "小木屋"
                    self.add_message("✅ 选择了小木屋")
                elif event.key == pygame.K_2:
                    self.selected_building = "石屋"
                    self.add_message("✅ 选择了石屋")
                elif event.key == pygame.K_3:
                    self.selected_building = "瞭望塔"
                    self.add_message("✅ 选择了瞭望塔")
                elif event.key == pygame.K_4:
                    self.selected_building = "防御墙"
                    self.add_message("✅ 选择了防御墙")
                elif event.key == pygame.K_5:
                    self.selected_building = "冶炼屋"
                    self.add_message("✅ 选择了冶炼屋")
                elif event.key == pygame.K_6:
                    self.selected_building = "仓库"
                    self.add_message("✅ 选择了仓库")
                elif event.key == pygame.K_7:
                    self.selected_building = "工坊"
                    self.add_message("✅ 选择了工坊")
    
    def update(self, dt: float):
        """更新游戏状态"""
        # 更新粒子
        self.particles.update(dt)
        
        # 更新灾害
        for disaster in self.disasters[:]:
            disaster.update(dt)
            if disaster.is_finished():
                self.disasters.remove(disaster)
        
        # 更新消息
        for message, lifetime in self.messages[:]:
            lifetime -= dt
            if lifetime <= 0:
                self.messages.remove((message, lifetime))
    
    def run(self):
        """主循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
            
            if self.game_state == "game_over":
                self.show_game_over()
                break
            elif self.game_state == "victory":
                self.show_victory()
                break
    
    def show_game_over(self):
        """显示游戏结束"""
        self.screen.fill(Colors.DARK_BG)
        
        title = self.font_large.render("💀 游戏结束", True, Colors.WARNING_RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title, title_rect)
        
        stats = [
            f"生存天数: {self.player.day}",
            f"捕捞次数: {self.player.total_fish_caught}",
            f"击败敌人: {self.player.enemies_defeated}",
        ]
        
        y = SCREEN_HEIGHT // 2
        for stat in stats:
            text = self.font_medium.render(stat, True, Colors.WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 50
        
        pygame.display.flip()
        pygame.time.wait(3000)
    
    def show_victory(self):
        """显示胜利"""
        self.screen.fill(Colors.DARK_BG)
        
        title = self.font_large.render("🎉 恭喜通关！", True, Colors.SUCCESS_GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title, title_rect)
        
        stats = [
            f"生存天数: {self.player.day}",
            f"捕捞次数: {self.player.total_fish_caught}",
            f"击败敌人: {self.player.enemies_defeated}",
            f"岛屿大小: {self.player.island_size}",
        ]
        
        y = SCREEN_HEIGHT // 2
        for stat in stats:
            text = self.font_medium.render(stat, True, Colors.WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 50
        
        pygame.display.flip()
        pygame.time.wait(3000)

# ============== 主程序入口 ==============
if __name__ == "__main__":
    game = SurvivalGame()
    game.run()
    pygame.quit()
