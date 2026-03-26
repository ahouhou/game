"""Main Game class: event handling, game logic, main loop."""

import os, json, random, math, pygame
from config import *
from data import *
from models import Player, Quest, StoryPage
from particles import Particles
from sprites import get_sprites, PLAYER_ROWS, ENEMY_ROWS, EFFECT_ROWS, AnimState
import renderer as R
import ui
from ui import Button

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("荒岛求生 - Survival Island")
        self.clock = pygame.time.Clock()
        ui.init_fonts()
        self.reset()

    def reset(self):
        """Full game state reset."""
        self.running = True
        self.state = "intro"          # intro / menu / main / combat / gameover / ending
        self.intro_done = False
        self.intro_page = 0
        self.intro_typed = ""
        self.intro_timer = 0.0
        self.t = 0.0                  # global timer

        # Player
        self.p = Player()
        self.p.add("木材", 15)
        self.p.add("石头", 8)
        self.p.add("鱼", 3)
        self.p.add("绳索", 3)
        self.p.weapon = "木棍"
        self.p.dur["木棍"] = 30

        # Action points
        self.pts = ACTION_POINTS

        # Weather & tips
        self.weather = "sunny"
        self.tip_msg = ""

        # Quest
        self.quest = None
        self.quest_log = []

        # Combat
        self.enemy_name = ""
        self.enemy_hp = 0
        self.enemy_max_hp = 0
        self.enemy_atk = 0
        self.enemy_dfs = 0
        self.combat_log = []

        # Messages
        self.msgs = []               # [(text, life_seconds)]

        # Overlays
        self.overlay = None          # None / "inv" / "craft" / "build" / "ach" / "quest" / "story" / "story_detail"
        self.story_detail = None

        # Particles
        self.parts = Particles()

        # ── Sprite entities ──
        self._sprites = get_sprites()
        # Player sprite on island
        self.player_x = SW * 0.4    # island center-ish
        self.player_y = SH * 0.47
        self.player_facing = 1      # 1=right, -1=left
        self.player_anim = AnimState(self._sprites["player"],
                                       row=PLAYER_ROWS["idle_right"], fps=6)
        self.player_action = ""       # "" / "fish" / "walk" / "hurt" / "victory"
        self.player_action_timer = 0.0
        # Movement
        self.keys_pressed = set()
        self.player_vx = 0.0
        self.player_vy = 0.0

        # Scene enemies (shown on island before combat)
        self.scene_enemies = []       # [{name, x, y, hp, max_hp, anim}]
        self.scene_enemy_spawn_timer = 0.0

        # Floating damage / pickup numbers
        self.floats = []             # [(text, x, y, vy, life, color)]

        # Combat enemy sprite anim (persistent)
        self.combat_enemy_anim = None

        # Visual timers
        self.day_e = 0.3
        self.wave_t = 0.0
        self.cloud_t = 0.0
        self.shake = 0.0

        # Save slots
        self.save_slots = {}
        for i in range(1, SAVE_SLOTS + 1):
            self.save_slots[i] = self._read_slot_info(i)

        # Button cache (rebuilt each frame)
        self._btns = []

    # ────────── Helpers ──────────
    def msg(self, text):
        self.msgs.append((text, 4.0))

    def _read_slot_info(self, slot):
        path = f"save{slot}.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                return d.get("player", {}).get("day", 0)
            except Exception:
                return None
        return None

    # ────────── Durability ──────────
    def _use_weapon_dur(self, amount=1):
        if not self.p.weapon or self.p.weapon not in self.p.dur:
            return
        self.p.dur[self.p.weapon] -= amount
        if self.p.dur[self.p.weapon] <= 0:
            old = self.p.weapon
            if old == "木棍":
                self.p.dur["木棍"] = 30
                self.msg(f"{old} 耐久耗尽，自动修复!")
            else:
                self.p.weapon = None
                self.msg(f"{old} 已损坏!")

    def _use_armor_dur(self, amount=2):
        if not self.p.armor or self.p.armor not in self.p.dur:
            return
        self.p.dur[self.p.armor] -= amount
        if self.p.dur[self.p.armor] <= 0:
            old = self.p.armor
            self.p.armor = None
            self.msg(f"{old} 已损坏!")

    def _equip_item(self, name):
        from data import RECIPES, ITEM_DUR
        if name not in RECIPES:
            return
        itype = RECIPES[name][1]
        if itype == "weapon":
            self.p.weapon = name
            self.p.dur[name] = ITEM_DUR.get(name, 30)
            self.msg(f"装备了 {name}!")
        elif itype == "armor":
            self.p.armor = name
            self.p.dur[name] = ITEM_DUR.get(name, 30)
            self.msg(f"穿戴了 {name}!")

    # ────────── Game Actions ──────────
    def do_fish(self):
        if self.pts <= 0:
            self.msg("行动点不足!"); return
        self.pts -= 1
        n = random.randint(1, 4)
        self.p.add("鱼", n)
        self.p.fish_count += 1
        self._use_weapon_dur(1)
        self.msg(f"捕捞成功! 获得 {n} 条鱼")
        self.parts.burst(SW//2, SH//2, 20, C_OCEAN, 100)
        self._add_float(f"+{n}鱼", SW//2, SH//3, C_OCEAN)
        # Fish animation
        self.player_anim.set_row(PLAYER_ROWS["fish"])
        self.player_action = "fish"; self.player_action_timer = 0.8
        self._check_quest()

    def do_explore(self):
        if self.pts <= 0:
            self.msg("行动点不足!"); return
        self.pts -= 1
        self.p.explore_count += 1
        self._use_weapon_dur(1)
        # Walk animation
        self.player_anim.set_row(PLAYER_ROWS["walk_right" if self.player_facing > 0 else "walk_left"])
        self.player_action = "walk"; self.player_action_timer = 0.6
        # Find something
        item = random.choice(EXPLORE_ITEMS)
        n = random.randint(1, 3)
        self.p.add(item, n)
        self.msg(f"探索发现: {item} x{n}")
        self._add_float(f"+{item}x{n}", self.player_x, self.player_y - 60, C_GRASS)
        self.parts.burst(SW//2, SH//2, 20, C_GRASS, 100)
        # Random encounter - spawn on island
        if random.random() < 0.30:
            ename = random.choice(EXPLORE_ENEMIES)
            ed = ENEMIES[ename]
            self._spawn_island_enemy(ename, ed)
            self.msg(f"发现 {ename}!")
        self._check_quest()

    def _spawn_island_enemy(self, ename, edata):
        """Spawn an enemy on the island scene (right side, approaching)."""
        self.scene_enemies.append({
            "name": ename,
            "hp": edata.max_hp,
            "max_hp": edata.max_hp,
            "x": SW * 0.85,
            "y": SH * 0.45,
            "vx": -1.5,
            "anim_row": ENEMY_ROWS.get(ename, 0),
            "anim": AnimState(self._sprites["enemies"], row=ENEMY_ROWS.get(ename, 0), fps=4),
        })

    def _add_float(self, text, x, y, color):
        """Add a floating number/text that rises and fades."""
        self.floats.append({"text": text, "x": x, "y": y,
                           "vy": -1.5, "life": 1.5, "color": color})

    def _trigger_action(self, action, dur=0.8):
        """Set player animation to action for dur seconds, then revert."""
        self.player_action = action
        self.player_action_timer = dur

    def do_eat(self):
        if self.p.has("鱼") < 1:
            self.msg("没有鱼可吃!"); return
        self.p.use("鱼", 1)
        self.p.hunger = min(100, self.p.hunger + 40)
        self.msg("进食成功! 饱腹+40")

    def do_heal(self):
        if self.p.has("草药汤") > 0:
            self.p.use("草药汤", 1)
            self.p.health = min(self.p.max_health, self.p.health + 30)
            self.msg("使用草药汤! 生命+30")
        elif self.p.has("神秘果实") > 0:
            self.p.use("神秘果实", 1)
            self.p.health = min(self.p.max_health, self.p.health + 30)
            self.msg("使用神秘果实! 生命+30")
        elif self.p.has("草药") >= 2:
            self.p.use("草药", 2)
            self.p.health = min(self.p.max_health, self.p.health + 15)
            self.msg("使用草药x2! 生命+15")
        else:
            self.msg("没有治疗物品!")

    def do_craft(self, name):
        from data import RECIPES
        if name not in RECIPES:
            return
        cost, itype, stat, dur = RECIPES[name]
        for item, n in cost.items():
            if self.p.has(item) < n:
                self.msg(f"材料不足: 需要 {item}x{n}"); return
        for item, n in cost.items():
            self.p.use(item, n)
        self.p.add(name)
        self.msg(f"制作了 {name}!")
        self.parts.burst(SW//2, SH//2, 25, C_GOLD, 120)
        # Auto equip weapons/armor
        if itype in ("weapon", "armor"):
            self._equip_item(name)
        self._check_quest()

    def do_build(self, name):
        if name not in BUILDINGS:
            return
        if name in self.p.buildings:
            self.msg("已经建造过了!"); return
        cost, effect = BUILDINGS[name]
        for item, n in cost.items():
            if self.p.has(item) < n:
                self.msg(f"材料不足: 需要 {item}x{n}"); return
        for item, n in cost.items():
            self.p.use(item, n)
        self.p.buildings.append(name)
        self.p.build_count += 1
        self.msg(f"建造了 {name}! ({effect})")
        self.parts.burst(SW//2, SH//2, 30, C_BROWN, 130)
        self._check_quest()
        self._check_achievements()

    # ────────── Day Cycle ──────────
    def next_day(self):
        self.p.day += 1
        self.p.energy = 100
        self.pts = ACTION_POINTS

        # Hunger
        self.p.hunger = max(0, self.p.hunger - DAILY_HUNGER_LOSS)
        if self.p.hunger <= 0:
            self.p.health = max(0, self.p.health - STARVATION_DAMAGE)
            self.msg("饥饿! 生命-15")

        # Weather
        if random.random() < 0.3:
            self.weather = random.choice(["sunny","cloudy","rainy","stormy","foggy"])
        self.tip_msg = random.choice(DAILY_TIPS)

        # Disaster
        has_tower = "瞭望塔" in self.p.buildings
        chance = DISASTER_CHANCE / 2 if has_tower else DISASTER_CHANCE
        if random.random() < chance:
            dtype = random.choice(DISASTER_TYPES)
            dmg = DISASTER_DAMAGE[dtype]
            has_wall = "防御墙" in self.p.buildings
            has_stone = "石屋" in self.p.buildings
            if has_wall: dmg = int(dmg * 0.6)
            if has_stone: dmg = int(dmg * 0.8)
            actual = max(0, dmg - self.p.pdef)
            self.p.health = max(0, self.p.health - actual)
            self._use_armor_dur(2)
            self.msg(f"{dtype}来袭! 受到{actual}点伤害!")
            self.shake = 0.5

        # Quest
        self._check_quest("day", 1)
        if not self.quest and random.random() < QUEST_SPAWN_CHANCE:
            self._spawn_quest()

        # Drift bottle
        if self.p.day > 2 and random.random() < DRIFT_BOTTLE_CHANCE:
            available = [s["id"] for s in STORIES if s["id"] not in self.p.pages_found]
            if available:
                found = random.choice(available)
                self.p.pages_found.append(found)
                self.msg(f"发现漂流瓶! 故事({len(self.p.pages_found)}/8)")
                self.parts.burst(SW//2, SH//2, 30, C_GOLD, 150)

        self._check_achievements()

        # Death check
        if self.p.health <= 0:
            self.state = "gameover"
            self.p.ending_unlocked = "dead"

    # ────────── Quest System ──────────
    def _spawn_quest(self):
        qtype = random.choice(["collect","build","combat","survive"])
        if qtype == "collect":
            target = random.choice(["鱼","木材","石头","绳索","金属","草药"])
            need = random.randint(3, 8)
            q = Quest("collect", f"收集{target}", f"收集 {target} x{need}", target, need,
                      {"经验": 15})
        elif qtype == "build":
            avail = [n for n in BUILDINGS if n not in self.p.buildings]
            if not avail: return
            target = random.choice(avail)
            q = Quest("build", f"建造{target}", f"建造 {target}", target, 1,
                      {"经验": 20, "金属": 3})
        elif qtype == "combat":
            need = random.randint(2, 5)
            q = Quest("combat", f"击败{need}个敌人", f"击败 {need} 个敌人", "kill", need,
                      {"经验": 25, "神秘果实": 1})
        else:
            target_day = self.p.day + random.randint(3, 6)
            q = Quest("survive", f"存活到第{target_day}天", f"存活到第 {target_day} 天", "day",
                      target_day, {"经验": 10, "草药": 3})
        self.quest = q
        self.msg(f"新任务: {q.title}")

    def _check_quest(self, kind=None, amount=0):
        if not self.quest or self.quest.completed:
            return
        q = self.quest
        if q.qtype == "collect" and kind in ("item", None):
            q.current = self.p.has(q.target)
        elif q.qtype == "combat" and kind == "kill":
            q.current = self.p.enemy_kills
        elif q.qtype == "survive" and kind == "day":
            q.current = self.p.day
        elif q.qtype == "build" and kind in ("build", None):
            q.current = 1 if q.target in self.p.buildings else 0
        if q.current >= q.need:
            self._complete_quest()

    def _complete_quest(self):
        q = self.quest
        q.completed = True
        self.msg(f"任务完成: {q.title}!")
        self.quest_log.append(("完成", q.title, "任务已完成"))
        # Rewards
        for key, val in q.reward.items():
            if key == "经验":
                self.p.gain_exp(val)
                self.msg(f"  +{val} 经验")
            elif key == "生命":
                self.p.health = min(self.p.max_health, self.p.health + val)
            else:
                self.p.add(key, val)
                self.msg(f"  +{key} x{val}")
        self.parts.burst(SW//2, SH//2, 40, C_GOLD, 150)
        self.quest = None
        self._check_achievements()

    # ────────── Combat ──────────
    def _start_combat(self, ename, edata):
        self.enemy_name = ename
        self.enemy_max_hp = edata.max_hp
        self.enemy_hp = edata.max_hp
        self.enemy_atk = edata.atk
        self.enemy_dfs = edata.dfs
        self.combat_log = [f"遭遇了 {ename}!"]
        self.state = "combat"
        # Set enemy sprite animation
        e_row = ENEMY_ROWS.get(ename, 0)
        self.combat_enemy_anim = AnimState(self._sprites["enemies"], row=e_row, fps=4)
        # Enemy hit flash state
        self.enemy_hit_flash = 0.0

    def _combat_attack(self):
        dmg = max(1, self.p.patk - self.enemy_dfs + random.randint(-3, 3))
        self.enemy_hp -= dmg
        self.combat_log.append(f"你造成 {dmg} 点伤害!")
        self.parts.burst(700, 300, 15, C_HEALTH, 120)
        self._add_float(f"-{dmg}", 720, 280, C_HEALTH)
        self.enemy_hit_flash = 0.15  # Flash for 150ms
        self._use_weapon_dur(2)
        if self.enemy_hp <= 0:
            self._combat_victory()
            return
        self._enemy_attack()

    def _combat_defend(self):
        self.combat_log.append("你选择防御!")
        edmg = max(1, self.enemy_atk - self.p.pdef + random.randint(-3, 3))
        actual = max(0, edmg // 2)
        self.p.health = max(0, self.p.health - actual)
        self.combat_log.append(f"防御中... 受到 {actual} 点伤害")

    def _enemy_attack(self):
        edmg = max(1, self.enemy_atk - self.p.pdef + random.randint(-3, 3))
        actual = max(0, edmg)
        self.p.health = max(0, self.p.health - actual)
        self._use_armor_dur(2)
        self.combat_log.append(f"{self.enemy_name} 攻击! 你受到 {actual} 点伤害!")
        self._add_float(f"-{actual}", 700, 450, C_HEALTH)
        # Player hurt animation
        self.player_anim.set_row(PLAYER_ROWS["hurt"])
        self.player_action = "hurt"; self.player_action_timer = 0.8
        # Screen shake
        self.shake = 0.2
        if self.p.health <= 0:
            self._combat_defeat()

    def _combat_flee(self):
        if random.random() < 0.4:
            self.combat_log.append("逃跑成功!")
            self.state = "main"
        else:
            self.combat_log.append("逃跑失败!")
            self._enemy_attack()

    def _combat_victory(self):
        ed = ENEMIES.get(self.enemy_name)
        self.combat_log.append(f"击败了 {self.enemy_name}!")
        if ed:
            self.p.gain_exp(ed.exp)
            self.p.enemy_kills += 1
            for item, n in ed.loot.items():
                self.p.add(item, n)
                self.combat_log.append(f"  获得 {item} x{n}")
        self.msg(f"击败了 {self.enemy_name}!")
        self.parts.burst(SW//2, SH//2, 40, C_GOLD, 180)
        self._check_quest("kill", 1)
        self._check_achievements()
        self.state = "main"

    def _combat_defeat(self):
        self.combat_log.append("你被击败了...")
        self.p.health = max(1, self.p.health)  # don't die in combat, just lose HP
        self.msg(f"被 {self.enemy_name} 打败! 生命恢复至1")
        self.state = "main"

    def _combat_use_item(self):
        # Use best healing item
        if self.p.has("草药汤") > 0:
            self.p.use("草药汤", 1)
            self.p.health = min(self.p.max_health, self.p.health + 30)
            self.combat_log.append("使用草药汤! +30HP")
        elif self.p.has("神秘果实") > 0:
            self.p.use("神秘果实", 1)
            self.p.health = min(self.p.max_health, self.p.health + 30)
            self.combat_log.append("使用神秘果实! +30HP")
        elif self.p.has("烤鱼") > 0:
            self.p.use("烤鱼", 1)
            self.p.hunger = min(100, self.p.hunger + 25)
            self.combat_log.append("使用烤鱼! 饱腹+25")
        else:
            self.combat_log.append("没有可用的道具!")
            return
        self._enemy_attack()

    # ────────── Achievements ──────────
    def _check_achievements(self):
        for ach in ACHIEVEMENTS:
            if ach["id"] not in self.p.achievements:
                try:
                    if ach["check"](self.p):
                        self.p.achievements.append(ach["id"])
                        self.msg(f"成就解锁: {ach['name']}!")
                        R.trigger_ach_popup(ach["name"], ach["desc"])
                        self.parts.burst(SW//2, 50, 30, C_GOLD, 150)
                except Exception:
                    pass

    # ────────── Ending ──────────
    def _get_ending(self):
        if self.p.health <= 0:
            return "dead"
        if self.p.has("三叉戟") > 0 or self.p.has("海神甲") > 0:
            return "legend"
        if self.p.build_count >= 5 and self.p.day >= 25:
            return "survivor"
        if len(self.p.pages_found) >= 5:
            return "memory"
        return "normal"

    # ────────── Save / Load ──────────
    def save_game(self, slot=1):
        data = {
            "player": {
                "health": self.p.health, "max_health": self.p.max_health,
                "hunger": self.p.hunger, "energy": self.p.energy,
                "day": self.p.day, "exp": self.p.exp, "level": self.p.level,
                "weapon": self.p.weapon, "armor": self.p.armor,
                "dur": self.p.dur, "inventory": self.p.inventory,
                "fish_count": self.p.fish_count, "explore_count": self.p.explore_count,
                "enemy_kills": self.p.enemy_kills, "build_count": self.p.build_count,
                "buildings": self.p.buildings, "achievements": self.p.achievements,
                "pages_found": self.p.pages_found, "ending_unlocked": self.p.ending_unlocked,
            },
            "game": {
                "weather": self.weather, "quest_log": self.quest_log,
                "tip_msg": self.tip_msg,
            },
        }
        path = f"save{slot}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.save_slots[slot] = self.p.day
        self.msg(f"存档{slot}已保存! (第{self.p.day}天)")

    def load_game(self, slot=1):
        path = f"save{slot}.json"
        if not os.path.exists(path):
            self.msg(f"存档{slot}不存在!"); return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            pd = data["player"]; gd = data.get("game", {})
            self.p = Player()
            for k, v in pd.items():
                setattr(self.p, k, v)
            self.weather = gd.get("weather", "sunny")
            self.quest_log = gd.get("quest_log", [])
            self.tip_msg = gd.get("tip_msg", "")
            self.state = "main"
            self.intro_done = True
            self.overlay = None
            self.quest = None
            self.msg(f"读档{slot}成功! (第{self.p.day}天)")
            return True
        except Exception as e:
            self.msg(f"读档失败: {e}")
            return False

    # ────────── Event Handling ──────────
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        # Don't clear _btns here! It's filled by draw() and used here.

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                # Track held keys for smooth movement
                if event.type == pygame.KEYDOWN:
                    self.keys_pressed.add(event.key)
                else:
                    self.keys_pressed.discard(event.key)

            if event.type == pygame.KEYDOWN:
                if self.state == "intro":
                    self.intro_done = True
                    self.state = "menu"
                    continue

                if event.key == pygame.K_ESCAPE:
                    if self.overlay:
                        self.overlay = None; continue
                    if self.state == "combat":
                        # Can't escape combat with ESC
                        self.msg("无法在战斗中逃跑!"); continue
                    if self.state == "main":
                        self.state = "menu"; continue

                if self.state == "menu":
                    pass  # handled by mouse click on buttons
                elif self.state == "main":
                    if event.key == pygame.K_1: self.do_fish()
                    elif event.key == pygame.K_2: self.do_explore()
                    elif event.key == pygame.K_3: self.do_eat()
                    elif event.key == pygame.K_4: self.do_heal()
                    elif event.key == pygame.K_n: self.next_day()
                    elif event.key == pygame.K_i: self.overlay = "inv" if self.overlay != "inv" else None
                    elif event.key == pygame.K_c: self.overlay = "craft" if self.overlay != "craft" else None
                    elif event.key == pygame.K_b: self.overlay = "build" if self.overlay != "build" else None
                    elif event.key == pygame.K_a: self.overlay = "ach" if self.overlay != "ach" else None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if self.state == "menu":
                    for cat, label, btn in self._btns:
                        if btn.clicked(pos):
                            if label == "退出":
                                self.running = False
                            elif label == "继续":
                                # Load slot 1 or start new
                                self.load_game(1) if self.save_slots.get(1) else self._start_new_game()
                            else:
                                self._start_new_game()

                elif self.state == "main" and self.overlay is None:
                    for cat, label, btn in self._btns:
                        if btn.clicked(pos):
                            if cat == "action":
                                if label == "捕捞": self.do_fish()
                                elif label == "探索": self.do_explore()
                                elif label == "进食": self.do_eat()
                                elif label == "治疗": self.do_heal()
                                elif label == "建造": self.overlay = "build"
                                elif label == "制作": self.overlay = "craft"
                                elif label == "成就": self.overlay = "ach"
                                elif label == "下一天": self.next_day()
                            elif cat == "sys":
                                if label == "背包": self.overlay = "inv"
                                elif label == "任务": self.overlay = "quest"
                                elif label in ("S1","S2","S3"):
                                    slot = int(label[-1])
                                    self.save_game(slot)

                elif self.state == "main" and self.overlay:
                    for entry in self._btns:
                        if len(entry) >= 3 and entry[-1].clicked(pos):
                            eid = entry[0]
                            if eid == "inv_close": self.overlay = None
                            elif eid == "craft_close": self.overlay = None
                            elif eid == "build_close": self.overlay = None
                            elif eid == "ach_close": self.overlay = None
                            elif eid == "qlog_close": self.overlay = None
                            elif eid == "story_close": self.overlay = None
                            elif eid == "story_detail_close": self.overlay = "story"
                            elif eid == "story_btn": self.overlay = "story"
                            elif eid == "craft":
                                self.do_craft(entry[1])
                            elif eid == "build":
                                self.do_build(entry[1])
                            elif eid == "read_story":
                                sid = entry[1]
                                for s in STORIES:
                                    if s["id"] == sid:
                                        self.story_detail = s; self.overlay = "story_detail"; break

                elif self.state == "combat":
                    for entry in self._btns:
                        if len(entry) >= 3 and entry[-1].clicked(pos):
                            label = entry[1]
                            if label == "攻击": self._combat_attack()
                            elif label == "防御": self._combat_defend()
                            elif label == "道具": self._combat_use_item()
                            elif label == "逃跑": self._combat_flee()

                elif self.state in ("gameover", "ending"):
                    for entry in self._btns:
                        if len(entry) >= 2 and entry[-1].clicked(pos):
                            if entry[0] == "ending_restart":
                                self.reset()

    def _start_new_game(self):
        self.reset()
        self.intro_done = True
        self.state = "main"
        self.msg("欢迎来到荒岛求生!")
        self.msg("提示: 捕捞获取食物, 探索发现资源")

    # ────────── Update ──────────
    def update(self, dt):
        self.t += dt
        self.parts.update(dt)

        # ── Combat enemy hit flash ──
        if self.state == "combat" and hasattr(self, 'enemy_hit_flash'):
            self.enemy_hit_flash = max(0, self.enemy_hit_flash - dt)

        # ── Player sprite animation ──
        self.player_anim.update(dt)
        if self.player_action_timer > 0:
            self.player_action_timer -= dt
            if self.player_action_timer <= 0:
                # Revert to idle
                row = PLAYER_ROWS["idle_right" if self.player_facing > 0 else "idle_left"]
                self.player_anim.set_row(row)

        # ── Player movement (keyboard) ──
        if self.state == "main" and self.overlay is None and not self.player_action:
            SPEED = 200.0   # pixels per second
            dx = dy = 0.0
            if self.keys_pressed:
                if self.keys_pressed.intersection({pygame.K_LEFT, pygame.K_a, pygame.K_KP4}):
                    dx -= 1; self.player_facing = -1
                if self.keys_pressed.intersection({pygame.K_RIGHT, pygame.K_d, pygame.K_KP6}):
                    dx += 1; self.player_facing = 1
                if self.keys_pressed.intersection({pygame.K_UP, pygame.K_w, pygame.K_KP8}):
                    dy -= 1
                if self.keys_pressed.intersection({pygame.K_DOWN, pygame.K_s, pygame.K_KP2}):
                    dy += 1
            # Normalize diagonal
            if dx and dy:
                dx *= 0.707; dy *= 0.707
            if dx or dy:
                row = PLAYER_ROWS["walk_right" if self.player_facing > 0 else "walk_left"]
                self.player_anim.set_row(row)
            else:
                row = PLAYER_ROWS["idle_right" if self.player_facing > 0 else "idle_left"]
                if self.player_anim.row != row:
                    self.player_anim.set_row(row)

            # Apply velocity with delta time
            new_x = self.player_x + dx * SPEED * dt
            new_y = self.player_y + dy * SPEED * dt

            # ── Island boundary collision ──
            # Grass area: roughly x=[80,1320], y=[~250, ~550] (top is SH*0.42, bottom is SH*0.58)
            # Use screen fraction bounds
            MIN_X, MAX_X = 80, 1320
            MIN_Y, MAX_Y = int(SH * 0.37), int(SH * 0.56)

            # Try X
            if MIN_X <= new_x <= MAX_X:
                # Soft boundary check - push away from edge
                if new_x < MIN_X + 20:
                    new_x = MIN_X + 20
                elif new_x > MAX_X - 20:
                    new_x = MAX_X - 20
                self.player_x = new_x
            # Try Y
            if MIN_Y <= new_y <= MAX_Y:
                self.player_y = new_y

            # ── Enemy contact collision ──
            PW, PH = 96, 120   # player sprite size
            for e in self.scene_enemies[:]:
                ex, ey = e["x"], e["y"]
                dist = ((self.player_x - ex) ** 2 + (self.player_y - ey) ** 2) ** 0.5
                if dist < (PW + 90) * 0.5:   # half-width overlap threshold
                    # Trigger combat!
                    from data import ENEMIES
                    ed = ENEMIES.get(e["name"])
                    if ed:
                        self._start_combat(e["name"], ed)
                        self.msg(f"遭遇 {e['name']}！进入战斗！")
                    self.scene_enemies.remove(e)
                    break

        # ── Scene enemies movement ──
        for e in self.scene_enemies[:]:
            e["anim"].update(dt)
            e["x"] += e["vx"] * dt * 60
            if e["x"] < SW * 0.5 or e["x"] > SW * 0.95:
                e["vx"] *= -1
            e["_life"] = e.get("_life", 8.0) - dt
            if e["_life"] <= 0:
                self.scene_enemies.remove(e)

        # ── Floating texts ──
        for f in self.floats[:]:
            f["y"] += f["vy"] * dt * 60
            f["life"] -= dt
            if f["life"] <= 0:
                self.floats.remove(f)

        # ── Combat enemy animation ──
        if self.state == "combat" and self.combat_enemy_anim:
            self.combat_enemy_anim.update(dt)

        # Messages decay
        new_msgs = []
        for text, life in self.msgs:
            life -= dt
            if life > 0:
                new_msgs.append((text, life))
        self.msgs = new_msgs

        # Shake decay
        if self.shake > 0:
            self.shake -= dt

    # ────────── Draw ──────────
    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        self._btns = []  # Clear buttons at start of draw cycle
        night = math.sin(self.day_e) < -0.5

        if self.state == "intro":
            self._draw_intro()
            return

        if self.state == "menu":
            self._draw_menu(mouse_pos)
            pygame.display.flip()
            return

        if self.state == "combat":
            self._draw_combat(mouse_pos)
            pygame.display.flip()
            return

        if self.state in ("gameover", "ending"):
            etype = self.p.ending_unlocked or "dead"
            edata = ENDINGS.get(etype, ENDINGS["dead"])
            self._btns = R.draw_ending(self.screen, etype, edata, self.p, mouse_pos)
            pygame.display.flip()
            return

        # Main state
        self.screen.fill(BLACK)
        # Calculate day progress (0=midnight, 0.5=noon, 1=midnight)
        day_progress = (self.day_e % (2 * math.pi)) / (2 * math.pi)
        R.draw_sky(self.screen, self.t, night, day_progress)
        if night:
            R.draw_stars(self.screen, self.t)
        R.draw_ocean(self.screen, self.wave_t)
        R.draw_clouds(self.screen, self.cloud_t, night)
        R.draw_weather(self.screen, self.weather, self.parts)
        R.draw_island(self.screen)

        # ── Sprite entities ──
        self._draw_player_sprite()
        self._draw_scene_enemies()
        self._draw_floating_texts()

        self.parts.draw(self.screen)
        R.draw_hud(self.screen, self.p, self.weather)
        R.draw_quest_info(self.screen, self.quest)

        # Action bar (builds buttons and stores in self._btns)
        self._btns = R.build_action_bar(self.screen, self.p, self.quest, mouse_pos)
        R.draw_messages(self.screen, self.msgs)
        R.draw_ach_popup(self.screen)

        # Overlay panels
        if self.overlay == "inv":
            self._btns = R.draw_inventory(self.screen, self.p, mouse_pos)
        elif self.overlay == "craft":
            self._btns = R.draw_craft(self.screen, self.p, mouse_pos)
        elif self.overlay == "build":
            self._btns = R.draw_build(self.screen, self.p, mouse_pos)
        elif self.overlay == "ach":
            self._btns = R.draw_ach(self.screen, self.p, mouse_pos)
        elif self.overlay == "story":
            self._btns = R.draw_story(self.screen, self.p, mouse_pos)
        elif self.overlay == "story_detail" and self.story_detail:
            self._btns = R.draw_story_detail(self.screen, self.story_detail, mouse_pos)
        elif self.overlay == "quest":
            self._btns = R.draw_quest_log(self.screen, self.quest_log, self.quest, mouse_pos)

        pygame.display.flip()

    def _draw_intro(self):
        page = INTRO_PAGES[self.intro_page] if self.intro_page < len(INTRO_PAGES) else ""
        self.intro_timer += 0.016
        # Typewriter effect: reveal 2 chars per tick (60fps)
        target_len = min(len(page), int(self.intro_timer * 2))
        if target_len > len(self.intro_typed):
            self.intro_typed = page[:target_len]
        R.draw_intro(self.screen, self.intro_page, len(INTRO_PAGES), self.intro_typed, self.t)
        # Auto advance after 6 seconds
        if self.intro_timer > 6.0:
            self.intro_page += 1
            self.intro_timer = 0.0
            self.intro_typed = ""
            if self.intro_page >= len(INTRO_PAGES):
                self.intro_done = True
                self.state = "menu"

    def _draw_menu(self, mouse_pos):
        self.screen.fill(BLACK)
        R.draw_sky(self.screen, self.t, False)
        R.draw_ocean(self.screen, self.wave_t)
        R.draw_island(self.screen)

        # Title
        ti = ui.font("xl").render("荒岛求生", True, C_GOLD)
        self.screen.blit(ti, (SW//2 - ti.get_width()//2, SH//2 - 160))
        sub = ui.font("sm").render("Survival Island v3.0", True, (160,160,160))
        self.screen.blit(sub, (SW//2 - sub.get_width()//2, SH//2 - 100))

        # Save slot info
        for i in range(1, SAVE_SLOTS + 1):
            sd = self.save_slots.get(i)
            txt = f"存档{i}: Day {sd}" if sd else f"存档{i}: 空"
            col = C_SUCCESS if sd else (80,80,100)
            t = ui.font("xs").render(txt, True, col)
            self.screen.blit(t, (SW//2 - 60, SH//2 - 60 + (i-1)*22))

        # Buttons
        btns = []
        bw, bh = 240, 56
        bx = SW//2 - bw//2
        configs = [
            ("新游戏", bx, SH//2 + 20, bw, bh, C_OCEAN),
            ("继续游戏", bx, SH//2 + 90, bw, bh, C_GRASS if self.save_slots.get(1) else (40,40,50)),
            ("退出", bx, SH//2 + 160, bw, bh, C_HEALTH),
        ]
        for label, x, y, w, h, bg in configs:
            btn = Button(x, y, w, h, label, bg)
            btn.draw(self.screen, mouse_pos)
            btns.append(("menu", label, btn))
        self._btns = btns

    def _draw_combat(self, mouse_pos):
        e_row = ENEMY_ROWS.get(self.enemy_name, 0)
        self._btns = R.draw_combat(
            self.screen, self.p.health, self.p.max_health,
            self.enemy_hp, self.enemy_max_hp, self.enemy_name,
            self.p.patk, self.p.pdef,
            self.enemy_atk, self.enemy_dfs,
            self.combat_log, mouse_pos,
            enemy_sprite=self._sprites["enemies"],
            enemy_row=e_row,
            enemy_anim=self.combat_enemy_anim,
            enemy_hit_flash=getattr(self, 'enemy_hit_flash', 0.0)
        )

    # ────────── Sprite Drawing ──────────
    def _draw_player_sprite(self):
        """Draw player character sprite on the island."""
        frame = self.player_anim.current_frame
        fw, fh = frame.get_width(), frame.get_height()
        x = int(self.player_x - fw // 2)
        y = int(self.player_y - fh // 2)
        self.screen.blit(frame, (x, y))

        # Name tag
        t = ui.font("xs").render("主角", True, C_GOLD)
        self.screen.blit(t, (int(self.player_x - t.get_width() // 2), y - 20))

    def _draw_scene_enemies(self):
        """Draw enemies wandering on the island."""
        for e in self.scene_enemies:
            frame = e["anim"].current_frame
            fw, fh = frame.get_width(), frame.get_height()
            x = int(e["x"] - fw // 2)
            y = int(e["y"] - fh // 2)
            self.screen.blit(frame, (x, y))

            # HP bar
            ratio = e["hp"] / e["max_hp"] if e["max_hp"] > 0 else 0
            bar_w = 80
            bx = int(e["x"] - bar_w // 2)
            by = y - 16
            pygame.draw.rect(self.screen, (40, 40, 40), (bx, by, bar_w, 8), border_radius=3)
            col = C_HEALTH if ratio > 0.5 else C_WARNING
            if ratio > 0:
                pygame.draw.rect(self.screen, col,
                                (bx, by, int(bar_w * ratio), 8), border_radius=3)

            # Name
            t = ui.font("xs").render(e["name"], True, C_WARNING)
            self.screen.blit(t, (int(e["x"] - t.get_width() // 2), y - 28))

    def _draw_floating_texts(self):
        """Draw floating damage/pickup numbers."""
        for f in self.floats:
            alpha = max(50, int(255 * f["life"] / 1.5))
            col = f["color"]
            # Dark outline
            t_outline = ui.font("sm").render(f["text"], True, (0, 0, 0))
            t_outline.set_alpha(alpha)
            t_color = ui.font("sm").render(f["text"], True, col)
            t_color.set_alpha(alpha)
            ox = int(f["x"] - t_color.get_width() // 2)
            self.screen.blit(t_outline, (ox + 1, int(f["y"]) + 1))
            self.screen.blit(t_color, (ox, int(f["y"])))

    # ────────── Main Loop ──────────
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            if not self.intro_done:
                self._draw_intro()
                for event in pygame.event.get():
                    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        self.intro_done = True
                        self.state = "menu"
                self.wave_t += 0.03
                self.cloud_t += 0.008
                self.t += 0.016
                continue

            self.handle_events()
            if self.state in ("main", "combat"):
                self.update(dt)
                self.day_e += 0.002
                self.wave_t += 0.03
                self.cloud_t += 0.008
            self.draw()

        pygame.quit()
