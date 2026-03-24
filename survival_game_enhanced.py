#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""荒岛求生 - Survival Island Game (Enhanced GUI) v2.0"""
import pygame, random, math, json, os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

pygame.init()
try:
    pygame.mixer.init(22050, -16, 2, 512)
    MIXER = True
except:
    MIXER = False

SW, SH = 1400, 900
FPS = 60

C_OCEAN=(25,118,210); C_OCEAN_D=(13,71,161); C_SAND=(255,193,7)
C_GRASS=(56,142,60); C_BROWN=(139,69,19); C_STONE=(128,128,128)
C_WHITE=(255,255,255); C_BLACK=(0,0,0); C_DARK=(20,20,30)
C_HEALTH=(244,67,54); C_HUNGER=(255,152,0); C_ENERGY=(255,235,59)
C_SUCCESS=(76,175,80); C_WARNING=(255,87,34); C_GOLD=(255,215,0)
C_STORM=(96,125,139); C_PURPLE=(138,43,226)

@dataclass
class Building:
    name: str; x: float; y: float
    w: int=65; h: int=65; color: Tuple=(139,69,19); desc: str=""

@dataclass
class Particle:
    x: float; y: float; vx: float; vy: float
    life: float; max_life: float; color: Tuple; size: int=5

@dataclass
class Enemy:
    name: str; max_hp: int; atk: int; dfs: int
    loot: Dict; exp: int; color: Tuple

@dataclass
class Player:
    health: int=100; max_health: int=100; hunger: int=100; max_hunger: int=100
    energy: int=100; max_energy: int=100; day: int=1; island_size: int=1
    weapon: Optional[str]=None; armor: Optional[str]=None
    exp: int=0; level: int=1
    inventory: Dict=field(default_factory=dict); buildings: List=field(default_factory=list)
    achievements: List=field(default_factory=list); pages_found: List=field(default_factory=list); ending_unlocked: str=""
    fish_count: int=0; enemy_kills: int=0; build_count: int=0
    def is_alive(self): return self.health>0
    def add(self,i,n=1): self.inventory[i]=self.inventory.get(i,0)+n
    def use(self,i,n=1):
        if self.inventory.get(i,0)>=n:
            self.inventory[i]-=n
            if self.inventory[i]<=0: del self.inventory[i]
            return True
        return False
    def has(self,i): return self.inventory.get(i,0)
    def patk(self):
        b=10
        for w,a in [("木棍",5),("石矛",12),("鱼叉",20),("三叉戟",35)]:
            if self.weapon==w: b+=a
        return b
    def pdfs(self):
        b=5
        for a,d in [("树叶衣",3),("兽皮甲",8),("贝壳甲",15),("海神甲",25)]:
            if self.armor==a: b+=d
        if any(b.name=="防御墙" for b in self.buildings): b+=10
        return b

ITEMS={
    "木材":("resource","建筑材料",(139,69,19)),
    "石头":("resource","坚硬石头",C_STONE),
    "金属":("resource","稀有金属",(192,192,192)),
    "布料":("resource","布料",(210,180,140)),
    "绳索":("resource","绳索",(160,82,45)),
    "草药":("resource","治疗草药",C_GRASS),
    "鱼":("food","新鲜海鱼",(255,140,0)),
    "椰子":("food","甘甜椰子",(184,134,11)),
    "烤鱼":("food","美味烤鱼",(255,69,0)),
    "神秘果实":("food","传说果实",C_PURPLE),
    "撒网":("tool","捕捞工具",(169,169,169)),
    "高级撒网":("tool","高效捕捞",(211,211,211)),
    "木棍":("weapon","基础武器",C_BROWN),
    "石矛":("weapon","锋利武器",C_STONE),
    "鱼叉":("weapon","专业武器",(192,192,192)),
    "三叉戟":("weapon","传说武器",C_GOLD),
    "树叶衣":("armor","简单护甲",C_GRASS),
    "兽皮甲":("armor","野战护甲",C_BROWN),
    "贝壳甲":("armor","坚硬护甲",(240,255,240)),
    "海神甲":("armor","传说护甲",(0,191,255)),
}

RECIPES={
    "小木屋":{"木材":20,"绳索":5},"石屋":{"石头":30,"木材":10},
    "瞭望塔":{"木材":15,"石头":10},"防御墙":{"石头":25,"木材":10,"金属":5},
    "冶炼屋":{"石头":20,"金属":5,"木材":15},"仓库":{"木材":20,"石头":10},
    "工坊":{"木材":25,"石头":20,"金属":10},
    "木棍":{"木材":3},"石矛":{"木材":2,"石头":4,"绳索":1},
    "鱼叉":{"金属":5,"木材":3,"绳索":2},
    "三叉戟":{"金属":10,"神秘果实":1,"绳索":5},
    "撒网":{"绳索":5,"布料":3},"高级撒网":{"撒网":1,"金属":3,"绳索":5},
    "树叶衣":{"布料":2},"兽皮甲":{"布料":5,"绳索":3},
    "贝壳甲":{"石头":10,"绳索":5,"布料":3},
    "海神甲":{"金属":15,"神秘果实":2,"贝壳甲":1},
    "烤鱼":{"鱼":1,"木材":1},"草药汤":{"草药":3,"椰子":1},
}

BUILDINGS={
    "小木屋":((139,69,19),"简单庇护所"),"石屋":((128,128,128),"坚固住所"),
    "瞭望塔":((255,215,0),"预警设施"),"防御墙":((128,128,128),"防御设施"),
    "冶炼屋":((255,69,0),"金属冶炼"),"仓库":((210,180,140),"存储设施"),
    "工坊":((128,128,128),"制造设施"),
}

ENEMIES={
    "海蟹":Enemy("海蟹",20,5,2,{"石头":2,"绳索":1},5,(200,100,50)),
    "鲨鱼":Enemy("鲨鱼",50,15,5,{"鱼":5,"金属":1},15,(150,150,180)),
    "巨型章鱼":Enemy("巨型章鱼",80,20,10,{"绳索":5,"金属":3},25,C_PURPLE),
    "海蛇":Enemy("海蛇",40,25,3,{"草药":3,"金属":2},20,(50,200,100)),
    "海龙王":Enemy("海龙王",150,35,20,{"金属":10,"神秘果实":1},50,C_GOLD),
}

ACHIEVEMENTS=[
    ("day10","🏆 生存10天","存活整整10天"),
    ("day30","🏆 求生大师","存活30天通关"),
    ("fish50","🏆 超级渔夫","捕捞50次"),
    ("kill10","🏆 海洋战士","击败10个敌人"),
    ("build5","🏆 建筑师","建造5个建筑"),
    ("smith","🏆 冶炼师","建造冶炼屋"),
    ("legendary","🏆 传说装备","获得三叉戟或海神甲"),
]

FOOD_VAL={"鱼":20,"烤鱼":35,"椰子":15,"神秘果实":50,"草药":10}

class Parts:
    def __init__(self): self.items=[]
    def burst(self,x,y,n,col,spd=3,sz=6):
        for _ in range(n):
            a=random.uniform(0,2*math.pi)
            vx=math.cos(a)*spd*random.uniform(0.5,1.5)
            vy=math.sin(a)*spd*random.uniform(0.5,1.5)
            self.items.append(Particle(x,y,vx,vy,random.uniform(0.5,1.2),1.0,col,random.randint(3,sz)))
    def rain(self,x,y,n,col):
        for _ in range(n):
            self.items.append(Particle(x+random.randint(-100,100),y,random.uniform(-2,2),random.uniform(4,8),1.5,1.5,col,2))
    def tornado(self,cx,cy,n,col):
        for _ in range(n):
            a=random.uniform(0,2*math.pi); d=random.uniform(20,80)
            x=cx+math.cos(a)*d; y=cy+math.sin(a)*d
            vx=-math.sin(a)*5+random.uniform(-1,1); vy=math.cos(a)*5+random.uniform(-1,1)
            self.items.append(Particle(x,y,vx,vy,1.0,1.0,col,5))
    def plume(self,x,y,n,col):
        for _ in range(n):
            self.items.append(Particle(x+random.randint(-60,60),y+random.randint(-60,60),random.uniform(-1,1),random.uniform(-1,1),1.5,1.5,col,4))
    def update(self,dt):
        for p in self.items[:]:
            p.life-=dt; p.x+=p.vx; p.y+=p.vy; p.vy+=0.12
            if p.life<=0: self.items.remove(p)
    def draw(self,surf):
        for p in self.items:
            a=max(0,p.life/p.max_life); sz=max(1,int(p.size*a))
            c=tuple(min(255,int(ch+(255-ch)*(1-a))) for ch in p.color)
            pygame.draw.circle(surf,c,(int(p.x),int(p.y)),sz)

class Disaster:
    def __init__(self,dt):
        self.dt=dt; self.x=SW//2; self.y=SH//2; self.dur=2.5; self.el=0.0
        self.done=False; self.pts=Parts()
    def update(self,dt):
        self.el+=dt
        if self.dt=="暴风雨": self.pts.rain(self.x,0,4,C_STORM)
        elif self.dt=="海啸": self.pts.burst(self.x,self.y,4,C_OCEAN,8,10)
        elif self.dt=="龙卷风": self.pts.tornado(self.x,self.y,3,C_STORM)
        elif self.dt=="瘟疫": self.pts.plume(self.x,self.y,3,C_PURPLE)
        self.pts.update(dt)
        if self.el>=self.dur: self.done=True
    def draw(self,surf):
        self.pts.draw(surf)
        ov={"暴风雨":(*C_STORM,30),"海啸":(*C_OCEAN,40),"龙卷风":(80,80,100,30),"瘟疫":(100,0,100,25)}
        o=ov.get(self.dt,(0,0,0,0))
        s=pygame.Surface((SW,SH),pygame.SRCALPHA)
        pygame.draw.rect(s,o,s.get_rect()); surf.blit(s,(0,0))

class Game:
    def __init__(self):
        self.screen=pygame.display.set_mode((SW,SH))
        pygame.display.set_caption("🏝 荒岛求生 - Survival Island")
        self.clock=pygame.time.Clock()
        self.running=True
        self.fn={'lg':pygame.font.Font(None,52),'md':pygame.font.Font(None,36),
                 'sm':pygame.font.Font(None,26),'xs':pygame.font.Font(None,20)}
        self.p=Player(); self.p.inventory={}
        self.pts=3; self.state="menu"
        self.ce=None; self.chp=0; self.clog=[]
        self.parts=Parts(); self.dis=[]; self.msgs=[]
        self.night=False; self.day_e=0.0; self.shk=0.0
        self.ap=None; self.ap_t=0.0
        self.stars=[(random.randint(0,SW),random.randint(0,SH//2)) for _ in range(80)]
        self.snd={}; self._mk_snd()
        self.build_slots=self._gen_slots()
        self.p.add("木材",15); self.p.add("石头",8); self.p.add("鱼",3); self.p.add("绳索",3)
        self.show_inv=False; self.show_cft=False; self.show_ach=False; self.show_bld=False
        self.intro_slide=0; self.intro_t=0.0; self.intro_done=False
        self.quest=None; self.drift_opened=False; self.page_to_show=None
        self.explore_count=0; self.full_hunger_days=0
        self.menu_btns=[("开始游戏",SW//2-120,SH//2+60,240,60,C_SUCCESS),("继续游戏",SW//2-120,SH//2+140,240,60,C_OCEAN),("退出游戏",SW//2-120,SH//2+220,240,60,C_WARNING)]
        # ===== 视觉效果系统 =====
        self.t=0.0; self.wave_t=0.0; self.cloud_t=0.0
        self.clouds=[(random.uniform(0,SW),random.uniform(30,150),random.uniform(0.3,1.0),random.randint(80,200)) for _ in range(6)]
        self.wave_offsets=[random.uniform(0,50) for _ in range(8)]
        self.wind_leaf_t=0.0; self.wind_leaves=[]
    def _gen_slots(self):
        cx,cy=SW//2,SH//2+30
        return [(cx+dx,cy+dy) for dx,dy in [(0,0),(-80,60),(80,60),(-40,-60),(40,-60),(-120,0),(120,0)]]
    def _mk_snd(self):
        if not MIXER: return
        try:
            import numpy as np; sr=22050
            def mk(f,d,v=.3):
                t=np.linspace(0,d,int(sr*d)); w=np.sin(2*np.pi*f*t)*np.exp(-t*8)
                w=(w*32767*v).astype(np.int16); st=np.column_stack((w,w))
                return pygame.sndarray.make_sound(st)
            self.snd={"catch":mk(440,.12,.25),"build":mk(220,.25,.3),"eat":mk(660,.1,.2),"hurt":mk(110,.2,.35),"levelup":mk(880,.35,.3),"achieve":mk(1200,.5,.3),"explore":mk(330,.1,.2),"attack":mk(150,.18,.3),"button":mk(300,.08,.15)}
        except: pass
    def _play(self,n):
        if n in self.snd:
            try: self.snd[n].play()
            except: pass
    def add_msg(self,t,d=3.0): self.msgs.append((t,d))
    def save(self):
        try:
            d={"p":self.p.__dict__,"pts":self.pts,"night":self.night}
            with open('save.json','w',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=2)
            self.add_msg("💾 游戏已保存")
        except: self.add_msg("❌ 保存失败")
    def load(self):
        if not os.path.exists('save.json'): return False
        try:
            with open('save.json','r',encoding='utf-8') as f: d=json.load(f)
            self.p.__dict__.update(d['p']); self.pts=d.get('pts',3); self.night=d.get('night',False); self.build_slots=self._gen_slots()
            self.add_msg("📂 存档已加载"); return True
        except: return False
    def _check_ach(self):
        for k,n,d in ACHIEVEMENTS:
            if k in self.p.achievements: continue
            u=False
            if k=="day10" and self.p.day>=10: u=True
            elif k=="day30" and self.p.day>=30: u=True
            elif k=="fish50" and self.p.fish_count>=50: u=True
            elif k=="kill10" and self.p.enemy_kills>=10: u=True
            elif k=="build5" and self.p.build_count>=5: u=True
            elif k=="smith" and any(b.name=="冶炼屋" for b in self.p.buildings): u=True
            elif k=="legendary" and (self.p.has("三叉戟")>0 or self.p.has("海神甲")>0): u=True
            if u:
                self.p.achievements.append(k); self.ap=(n,d); self.ap_t=3.5; self._play("achieve"); self.add_msg(f"{n} 已解锁！")

    # ---- Game Actions ----
    def _do_fish(self):
        if self.pts<=0: self.add_msg('⚠ 没有行动点了！'); return
        self.pts-=1; self.p.hunger=max(0,self.p.hunger-15); self.p.energy=max(0,self.p.energy-10)
        ml=4 if self.p.has('高级撒网')>0 else(2 if self.p.has('撒网')>0 else 1)
        c={'鱼':random.randint(2,4)*ml}
        for _ in range(6):
            r=random.random()
            if r<.25: c['木材']=c.get('木材',0)+random.randint(1,3)
            elif r<.45: c['石头']=c.get('石头',0)+random.randint(1,2)
            elif r<.57: c['金属']=c.get('金属',0)+random.randint(1,2)
            elif r<.65: c['布料']=c.get('布料',0)+random.randint(1,2)
            elif r<.69: c['神秘果实']=c.get('神秘果实',0)+1
            elif r<.79: c['草药']=c.get('草药',0)+random.randint(1,2)
            elif r<.85: c['绳索']=c.get('绳索',0)+random.randint(1,2)
        for i,n in c.items(): self.p.add(i,n)
        self.p.fish_count+=1; self._play('catch')
        self.parts.burst(SW//2,SH//2+50,25,C_OCEAN,5,8)
        s=','.join(f'{i}x{n}' for i,n in c.items())
        self.add_msg(f'🎣 捕捞成功！获得: {s}'); self._check_ach()
        if self.quest: self._check_quest('item',1)

    def _do_explore(self):
        if self.pts<=0: self.add_msg('⚠ 没有行动点了！'); return
        self.pts-=1; self.p.hunger=max(0,self.p.hunger-20); self.p.energy=max(0,self.p.energy-15)
        f=random.choice([{'木材':random.randint(3,6)},{'石头':random.randint(2,5)},
                        {'椰子':random.randint(1,3)},{'草药':random.randint(1,3)},
                        {'布料':random.randint(1,2)},{'金属':random.randint(1,2)}])
        for i,n in f.items(): self.p.add(i,n)
        self.explore_count+=1
        if self.quest: self._check_quest('explore',1)
        self.parts.burst(SW//2,SH//2+50,20,C_GRASS,4,7); self._play('explore')
        s=','.join(f'{i}x{n}' for i,n in f.items()); self.add_msg(f'🗺 探索发现: {s}')
        if random.random()<.30:
            n=random.choice(['海蟹','海蟹','鲨鱼','鲨鱼','海蛇','海蛇','巨型章鱼','海龙王'])
            self.ce=ENEMIES[n]; self.chp=self.ce.max_hp
            self.clog=[f'⚔ 遭遇 {n}！',f'HP:{self.ce.max_hp} ATK:{self.ce.atk} DEF:{self.ce.dfs}']
            self.state='combat'

    def _do_eat(self):
        fd={k:v for k,v in self.p.inventory.items() if ITEMS.get(k) and ITEMS[k][0]=='food'}
        if not fd: self.add_msg('❌ 背包里没有食物！'); return
        fd=max(fd,key=lambda f:FOOD_VAL.get(f,10))
        val=FOOD_VAL.get(fd,10); self.p.use(fd)
        self.p.hunger=min(100,self.p.hunger+val); self._play('eat')
        self.parts.burst(200,300,15,C_HUNGER,3,5)
        self.add_msg(f'🍖 吃了 {fd}，恢复 {val} 饱食度！')

    def _do_heal(self):
        if self.p.has('草药')<3: self.add_msg('❌ 需要草药 x3'); return
        self.p.use('草药',3); h=30; self.p.health=min(100,self.p.health+h)
        self._play('eat'); self.parts.burst(200,300,15,C_SUCCESS,3,5)
        self.add_msg(f'💚 使用草药治疗，恢复 {h} 生命！')

    def _do_craft(self,name):
        if name not in RECIPES: return
        cost=RECIPES[name]
        for i,n in cost.items():
            if self.p.has(i)<n: self.add_msg(f'❌ 材料不足：需 {i}x{n}'); return
        for i,n in cost.items(): self.p.use(i,n)
        self.p.add(name); self._play('build')
        self.parts.burst(SW//2,SH//2,30,C_SUCCESS,5,8)
        tp=ITEMS.get(name)
        if tp:
            if tp[0]=='weapon': self.p.weapon=name; self.add_msg(f'⚔ 制造了 {name} 并装备！')
            elif tp[0]=='armor': self.p.armor=name; self.add_msg(f'🛡 制造了 {name} 并装备！')
            elif tp[0]=='building': self.add_msg(f'🏗 制造了 {name}！')
            else: self.add_msg(f'✅ 制造了 {name}！')
        else: self.add_msg(f'✅ 制造了 {name}！')
        self._check_ach()

    def _do_build(self,name):
        if name not in BUILDINGS: return
        if any(b.name==name for b in self.p.buildings): self.add_msg(f'❌ {name} 已经建过了！'); return
        cost=RECIPES.get(name,{})
        for i,n in cost.items():
            if self.p.has(i)<n: self.add_msg(f'❌ 材料不足：需 {i}x{n}'); return
        for i,n in cost.items(): self.p.use(i,n)
        used={(b.x,b.y) for b in self.p.buildings}
        slot=next(((x,y) for x,y in self.build_slots if (x,y) not in used),(random.randint(300,700),random.randint(300,500)))
        col=BUILDINGS[name][0]
        self.p.buildings.append(Building(name,slot[0],slot[1],65,65,col,BUILDINGS[name][1]))
        self.p.build_count+=1; self.pts-=1; self.p.energy=max(0,self.p.energy-20)
        self._play('build'); self.parts.burst(slot[0],slot[1],40,col,6,10)
        self.add_msg(f'🏗 建造了 {name}！'); self._check_ach()

    def _ca_attack(self):
        if not self.ce: return
        e=self.ce; dmg=max(1,self.p.patk()-e.dfs+random.randint(-3,3))
        self.chp-=dmg; self.clog=[f'⚔ 你造成 {dmg} 伤害！敌人HP:{max(0,self.chp)}']
        self._play('attack'); self.parts.burst(900,300,10,C_HEALTH,4,5)
        if self.chp<=0:
            self.clog=[f'🏆 击败了 {e.name}！']; self.p.exp+=e.exp
            for i,n in e.loot.items(): self.p.add(i,n); self.clog.append(f'🎁 获得: {i}x{n}')
            self.p.enemy_kills+=1; self._check_ach()
            self.parts.burst(900,300,40,C_GOLD,6,10); self._play('achieve')
            self.state='main'; self.ce=None; return
        edmg=max(1,e.atk-self.p.pdfs()+random.randint(-2,2))
        self.p.health-=edmg; self.clog.append(f'💥 {e.name} 反击！{edmg}伤害！HP:{self.p.health}')
        self._play('hurt'); self.shk=.3
        if not self.p.is_alive(): self.state='game_over'

    def _ca_defend(self):
        if not self.ce: return
        self.clog=['🛡 你摆出防御姿态！']; e=self.ce
        edmg=max(1,e.atk-self.p.pdfs()-5+random.randint(-2,2))
        self.p.health-=edmg; self.clog.append(f'💥 {e.name}攻击！{edmg}伤害！HP:{self.p.health}')
        self._play('hurt'); self.shk=.3
        if not self.p.is_alive(): self.state='game_over'

    def _ca_item(self):
        if not self.ce: return
        if self.p.has('草药')>=1:
            self.p.use('草药'); self.p.health=min(100,self.p.health+15)
            self.clog=['💚 使用草药恢复 15 HP！']; self._play('eat')
        else: self.clog=['❌ 没有草药！']

    def _ca_run(self):
        if random.random()<.6: self.clog=['🏃 逃跑成功！']; self.state='main'; self.ce=None
        else:
            self.clog=['❌ 逃跑失败！']
            if self.ce:
                e=self.ce; edmg=max(1,e.atk-self.p.pdfs()+random.randint(-2,2))
                self.p.health-=edmg; self.clog.append(f'💥 {e.name}攻击！{edmg}伤害！HP:{self.p.health}')
                self._play('hurt'); self.shk=.3
                if not self.p.is_alive(): self.state='game_over'

    def _spawn_quest(self):
        if self.quest and not self.quest.completed: return
        if random.random()>0.35: return
        d=self.p.day
        pool=[
            Quest("collect","收集任务","收集5条鱼","鱼",5,{"经验":20}),
            Quest("collect","收集任务","收集10块木材","木材",10,{"经验":15}),
            Quest("collect","收集任务","收集3个神秘果实","神秘果实",3,{"经验":50,"生命":30}),
            Quest("collect","收集任务","收集5块金属","金属",5,{"经验":30}),
            Quest("build","建造任务","建造一个小木屋","小木屋",1,{"经验":40}),
            Quest("build","建造任务","建造一个冶炼屋","冶炼屋",1,{"经验":60}),
            Quest("build","建造任务","建造一个仓库","仓库",1,{"经验":30}),
            Quest("combat","击败任务","击败3个敌人","敌人",3,{"经验":45}),
            Quest("combat","击败任务","击败鲨鱼","鲨鱼",1,{"经验":30,"金属":5}),
            Quest("combat","击败任务","击败海龙王","海龙王",1,{"经验":80}),
            Quest("survive","生存任务","再存活3天","生存",d+3,{"经验":25}),
            Quest("survive","生存任务","保持满饱食度2天","满饱食",2,{"经验":20,"体力":30}),
        ]
        self.quest=random.choice(pool)
        self.add_msg("📜 新任务："+self.quest.title+" - "+self.quest.desc)

    def _check_quest(self,kind,amount):
        if not self.quest or self.quest.completed: return
        q=self.quest
        if q.qtype=="collect" and kind in ("item","check"):
            if self.p.has(q.target)>=q.target_count:
                q.completed=True; self.add_msg("✅ 任务完成："+q.title+"！"); self._reward_quest()
        elif q.qtype=="build" and kind=="build":
            if any(b.name==q.target for b in self.p.buildings):
                q.completed=True; self.add_msg("✅ 任务完成："+q.title+"！"); self._reward_quest()
        elif q.qtype=="combat" and kind=="kill":
            q.current+=amount
            if q.current>=q.target_count:
                q.completed=True; self.add_msg("✅ 任务完成："+q.title+"！"); self._reward_quest()
        elif q.qtype=="survive" and kind=="day":
            if self.p.hunger>=80: self.full_hunger_days+=1
            if q.target=="满饱食" and self.full_hunger_days>=q.target_count:
                q.completed=True; self.add_msg("✅ 任务完成："+q.title+"！"); self._reward_quest()
            if q.target=="生存" and self.p.day>=q.target_count:
                q.completed=True; self.add_msg("✅ 任务完成："+q.title+"！"); self._reward_quest()

    def _reward_quest(self):
        if not self.quest: return
        r=self.quest.reward; msg="🎁 任务奖励："
        if "经验" in r: self.p.exp+=r["经验"]; msg+="经验+"+str(r["经验"])+" "
        if "生命" in r: self.p.health=min(100,self.p.health+r["生命"]); msg+="生命+"+str(r["生命"])+" "
        if "金属" in r: self.p.add("金属",r["金属"]); msg+="金属+"+str(r["金属"])
        if "神秘果实" in r: self.p.add("神秘果实",r["神秘果实"]); msg+="神秘果实+"+str(r["神秘果实"])
        self.add_msg(msg); self.quest=None

    def _check_drift_bottle(self):
        if self.drift_opened or self.p.day<2: return
        if random.random()<0.08:
            pg=random.choice(DRIFT_BOTTLES)
            if pg.id not in self.p.pages_found:
                self.p.pages_found.append(pg.id)
                self.drift_opened=True; self.page_to_show=pg
                self.add_msg("📜 发现了漂流瓶："+pg.title)

    def _get_ending(self):
        if self.p.health<=0: return ENDINGS["none"]
        if self.p.has("三叉戟")>0 or self.p.has("海神甲")>0: return ENDINGS["legend"]
        if len(self.p.buildings)>=5 and self.p.day>=25: return ENDINGS["survivor"]
        if len(self.p.pages_found)>=5: return ENDINGS["memory"]
        return ENDINGS["normal"]

    def _draw_intro_screen(self):
        self.intro_t+=0.016
        if self.intro_t>6.0 and self.intro_slide<7:
            self.intro_slide+=1; self.intro_t=0.0
        if self.intro_t>5.0 and self.intro_slide>=7:
            self.intro_done=True; self.state="menu"; return
        t=self.day_e; bg_t=(math.sin(t)+1)/2
        r=int(10*(1-bg_t)+25*bg_t); g=int(10*(1-bg_t)+71*bg_t); b=int(30*(1-bg_t)+161*bg_t)
        self.screen.fill((r,g,b))
        for sx,sy in self.stars:
            alpha=0.4+0.6*abs(math.sin(self.t*2+sx*0.1))
            sc=tuple(int(v*alpha) for v in C_WHITE)
            pygame.draw.circle(self.screen,sc,(sx,sy),1)
        pygame.draw.circle(self.screen,(220,220,180),(120,80),35)
        if self.intro_slide<len(DRIFT_BOTTLES):
            pg=DRIFT_BOTTLES[self.intro_slide]
            mood_c={"fear":C_WARNING,"hope":C_SUCCESS,"memory":C_GOLD,"peace":C_OCEAN}
            col=mood_c.get(pg.mood,C_WHITE)
            ov=pygame.Surface((SW,SH//2+80),pygame.SRCALPHA)
            pygame.draw.rect(ov,(0,0,0,210),(0,0,SW,SH//2+80))
            self.screen.blit(ov,(0,SH//2-40))
            pygame.draw.line(self.screen,col,(100,SH//2-20),(SW-100,SH//2-20),2)
            t2=self.fn["md"].render(pg.title,True,col); self.screen.blit(t2,(SW//2-t2.get_width()//2,SH//2-10))
            visible=int(self.intro_t*25)
            vt=pg.content[:visible]
            words=vt.split("。")
            display=""; y=SH//2+30
            for para in words:
                for word in para.split("——"):
                    if len(display+word)>58:
                        t2=self.fn["sm"].render(display,True,C_WHITE); self.screen.blit(t2,(80,y)); y+=26; display=word+"——"
                    else: display+=word+"——"
            if display:
                t2=self.fn["sm"].render(display,True,C_WHITE); self.screen.blit(t2,(80,y))
            if self.intro_t>1.0:
                t2=self.fn["xs"].render("点击任意键跳过",True,(100,100,100))
                self.screen.blit(t2,(SW//2-t2.get_width()//2,SH-40))
        pygame.display.flip()

    def _draw_ending_screen(self):
        end=self._get_ending()
        title_text,desc_text,style=end[0],end[1],end[2]
        col_map={"grey":(150,150,150),"gold":C_GOLD,"green":C_GRASS,"purple":C_PURPLE,"dark":(80,80,80)}
        col=col_map.get(style,C_WHITE)
        ov=pygame.Surface((SW,SH),pygame.SRCALPHA)
        pygame.draw.rect(ov,(0,0,0,220),(0,0,SW,SH)); self.screen.blit(ov,(0,0))
        pw,ph=700,480; px,py=(SW-pw)//2,(SH-ph)//2
        pygame.draw.rect(self.screen,(20,20,40),(px,py,pw,ph),border_radius=20)
        pygame.draw.rect(self.screen,col,(px,py,pw,ph),3,border_radius=20)
        t2=self.fn["lg"].render(title_text,True,col); self.screen.blit(t2,(px+pw//2-t2.get_width()//2,py+30))
        pygame.draw.line(self.screen,col,(px+60,py+85),(px+pw-60,py+85),2)
        words=desc_text.split("。"); y=py+105; line=""
        for word in words:
            if len(line+word)>50: t2=self.fn["sm"].render(line,True,C_WHITE); self.screen.blit(t2,(px+60,y)); y+=28; line=word+"。"
            else: line+=word+"。"
        if line: t2=self.fn["sm"].render(line,True,C_WHITE); self.screen.blit(t2,(px+60,y)); y+=40
        stats=["生存天数："+str(self.p.day),"捕捞次数："+str(self.p.fish_count),"击败敌人："+str(self.p.enemy_kills),"建造建筑："+str(len(self.p.buildings)),"解锁故事："+str(len(self.p.pages_found))+"/8","获得成就："+str(len(self.p.achievements))+"/7"]
        t2=self.fn["md"].render("游戏数据",True,col); self.screen.blit(t2,(px+60,y)); y+=35
        for s in stats: t2=self.fn["sm"].render(s,True,C_WHITE); self.screen.blit(t2,(px+60,y)); y+=28
        self._btn(SW//2-80,py+ph-70,160,50,"重新开始",C_SUCCESS,C_WHITE)
        self._go_restart_btn=[(SW//2-80,py+ph-70,160,50)]


    def _next_day(self):
        self.p.day+=1; self.pts=3
        if self.p.hunger<=0: self.p.health-=15; self.add_msg('⚠ 饥饿！生命值下降！')
        self.p.hunger=max(0,self.p.hunger-12)
        while self.p.exp>=self.p.level*30:
            self.p.level+=1; self.p.max_health+=10
            self.p.health=min(self.p.max_health,self.p.health+10)
            self._play('levelup'); self.add_msg(f'🎉 升级！等级:{self.p.level} 最大生命+10！')
        rate=.30
        if any(b.name=='瞭望塔' for b in self.p.buildings): rate*=.5
        if random.random()<rate:
            dt=random.choice(['暴风雨','海啸','龙卷风','瘟疫'])
            self.dis.append(Disaster(dt)); dmgs={'暴风雨':15,'海啸':25,'龙卷风':20,'瘟疫':18}
            dmg=dmgs[dt]
            if any(b.name=='防御墙' for b in self.p.buildings): dmg=int(dmg*.6); self.add_msg('🧱 防御墙减免了伤害！')
            if any(b.name=='石屋' for b in self.p.buildings): dmg=int(dmg*.8)
            self.p.health=max(0,self.p.health-dmg); self.add_msg(f'⚠ {dt}来袭！受到 {dmg} 点伤害！'); self._play('hurt')
        self._check_ach()
        self._spawn_quest()
        self._check_drift_bottle()
        if self.p.day>=30: self.state='victory'
        elif not self.p.is_alive(): self.state='game_over'
        self.add_msg(f'🌅 第 {self.p.day} 天开始了...')


    # ---- Drawing ----
    def _bar(self,x,y,w,h,cur,mx,col):
        # 背景
        pygame.draw.rect(self.screen,(0,0,0,180),(x-2,y-2,w+4,h+4),border_radius=6)
        # 填充（渐变效果）
        fill=int(w*min(1,max(0,cur/mx)))
        if fill>0:
            # 深色底层
            dark_c=tuple(max(0,c-60) for c in col)
            pygame.draw.rect(self.screen,dark_c,(x,y,w,h),border_radius=4)
            # 亮色填充
            for i in range(min(fill,h)):
                frac=i/h
                r=int(col[0]*(1-frac)+dark_c[0]*frac)
                g=int(col[1]*(1-frac)+dark_c[1]*frac)
                b=int(col[2]*(1-frac)+dark_c[2]*frac)
                pygame.draw.line(self.screen,(r,g,b),(x,y+i),(x+fill,y+i))
        # 边框
        pygame.draw.rect(self.screen,C_WHITE,(x,y,w,h),1,border_radius=4)
        # 光泽
        shine_s=pygame.Surface((w,3),pygame.SRCALPHA)
        pygame.draw.rect(shine_s,(255,255,255,40),(0,0,w,3))
        self.screen.blit(shine_s,(x,y+1))

    def _btn(self,x,y,w,h,text,bg,fg,hover=False):
        # 光晕效果
        glow=int(20 if not hover else 40)
        glow_s=pygame.Surface((w+20,h+20),pygame.SRCALPHA)
        glow_c=tuple(min(255,max(0,c)) for c in bg)
        glow_c_alpha=tuple(list(glow_c)+[glow])
        pygame.draw.rect(glow_s,glow_c_alpha,(8,8,w+4,h+4),border_radius=12)
        self.screen.blit(glow_s,(x-10,y-10))
        # 主按钮
        # 渐变背景（通过多层半透明矩形模拟）
        for i in range(3):
            alpha=40-i*10
            l_c=tuple(min(255,max(0,c+30-i*15)) for c in bg)
            pygame.draw.rect(self.screen,l_c,(x+i,y+i,w-i*2,h-i*2),border_radius=8-i)
        pygame.draw.rect(self.screen,bg,(x,y,w,h),border_radius=8)
        # 顶部高光
        highlight_h=min(8,h//3)
        hi_c=tuple(min(255,max(0,c+50)) for c in bg)
        hi_s=pygame.Surface((w-4,highlight_h),pygame.SRCALPHA)
        hi_alpha=tuple(list(hi_c)+[80])
        pygame.draw.rect(hi_s,hi_alpha,(2,0,w-4,highlight_h),border_radius=4)
        self.screen.blit(hi_s,(x+2,y+2))
        # 边框
        pygame.draw.rect(self.screen,C_WHITE,(x,y,w,h),1,border_radius=8)
        # 文字
        t=self.fn["sm"].render(text,True,fg)
        self.screen.blit(t,t.get_rect(center=(x+w//2,y+h//2)))

    def _draw_bg(self):
        self.day_e+=0.002; self.cloud_t+=0.008; self.wave_t+=0.03
        t=(math.sin(self.day_e)+1)/2; self.night=t<0.25
        # 天空渐变
        sky_t=math.sin(self.day_e*0.5)
        if self.night:
            r0,g0,b0=10,10,30; r1,g1,b1=25,25,60
        elif t>0.75:
            r0,g0,b0=255,100,50; r1,g1,b1=255,60,30
        else:
            r0,g0,b0=int(135*(1-sky_t)+30*sky_t),int(211*(1-sky_t)+120*sky_t),int(235*(1-sky_t)+200*sky_t)
            r1,g1,b1=25,118,210
        for y in range(0,SH//2,3):
            frac=y/(SH//2)
            r=int(r0*(1-frac)+r1*frac); g=int(g0*(1-frac)+g1*frac); b=int(b0*(1-frac)+b1*frac)
            pygame.draw.line(self.screen,(r,g,b),(0,y),(SW,y))
        # 海洋渐变
        for y in range(SH//2,SH,3):
            frac=(y-SH//2)/(SH-SH//2)
            r=int(25*(1-frac)+13*frac); g=int(118*(1-frac)+71*frac); b=int(210*(1-frac)+161*frac)
            pygame.draw.line(self.screen,(r,g,b),(0,y),(SW,y))
        # 动态波浪
        for wi,woy in enumerate(self.wave_offsets):
            wy=SH//2+wi*18+int(math.sin(self.wave_t+woy)*5)
            points=[]
            for x in range(0,SW+20,20):
                y=wy+int(math.sin(x*0.015+self.wave_t*1.5+woy)*3)
                points.append((x,y))
            if len(points)>1:
                for i in range(len(points)-1):
                    alpha=max(30,180-wi*20)
                    col=(255,255,255)
                    pygame.draw.line(self.screen,col,points[i],points[i+1],1)
        # 云朵
        for cx,cy,cs,cw in self.clouds:
            nx=cx+cs*0.3
            if nx>SW+cw: nx=-cw
            # 用椭圆绘制云朵
            base_c=int(220*(1-t)+80*t)
            cloud_c=(base_c,base_c,int(base_c*1.05))
            for dx,dy,dr in [(0,0,cs*0.4),(cs*0.3,cs*0.1,cs*0.3),(cs*0.6,cs*0.05,cs*0.25),(cs*0.15,cs*0.15,cs*0.2)]:
                pygame.draw.circle(self.screen,cloud_c,(int(nx+dx),int(cy+dy)),int(dr))
            # 更新位置
            for i,(ocx,ocy,ocs,ocw) in enumerate(self.clouds):
                if ocx==cx: self.clouds[i]=(nx,cy,cs,cw)
        # 星星（夜晚）
        if self.night:
            for sx,sy in self.stars:
                alpha=0.4+0.6*abs(math.sin(self.t*2+sx*0.1))
                sc=tuple(int(v*alpha) for v in C_WHITE)
                pygame.draw.circle(self.screen,sc,(sx,sy),1 if alpha<0.7 else 2)
        # 月亮（夜晚）
        if self.night:
            mx,my=120,80
            pygame.draw.circle(self.screen,(220,220,180),(mx,my),35)
            pygame.draw.circle(self.screen,(15,15,35),(mx+5,my-3),35)
        # 太阳（日间）
        elif t>0.3 and t<0.8:
            sun_y=int(60+t*30)
            pygame.draw.circle(self.screen,(255,230,50),(SW-120,sun_y),40)
            for i in range(8):
                a=i*math.pi/4+self.t*0.3
                ex=int(SW-120+math.cos(a)*55); ey=int(sun_y+math.sin(a)*55)
                pygame.draw.line(self.screen,(255,220,0),(ex,ey),(int(SW-120+math.cos(a)*70),int(sun_y+math.sin(a)*70)),2)
        self.t+=0.016

    def _draw_island(self):
        cx,cy=SW//2,SH//2+30; sz=300+(self.p.island_size-1)*30
        for i in range(5,0,-1):
            c=tuple(max(0,int(C_OCEAN_D[j]+(C_OCEAN[j]-C_OCEAN_D[j])*(1-i/5))) for j in range(3))
            pygame.draw.ellipse(self.screen,c,(cx-5*i,cy-5*i,sz+10*i,sz+10*i))
        pygame.draw.ellipse(self.screen,C_SAND,(cx,cy,sz,sz))
        g=int(sz*.12); pygame.draw.ellipse(self.screen,C_GRASS,(cx+g,cy+g,sz-g*2,sz-g*2))
        for tx,ty in [(cx+sz*.3,cy+sz*.25),(cx+sz*.7,cy+sz*.3),(cx+sz*.5,cy+sz*.6),(cx+sz*.25,cy+sz*.65)]:
            pygame.draw.rect(self.screen,C_BROWN,(int(tx),int(ty),6,14))
            pygame.draw.circle(self.screen,C_GRASS,(int(tx+3),int(ty)-2),10)
        for b in self.p.buildings:
            pygame.draw.ellipse(self.screen,(0,0,0,60),(int(b.x-30),int(b.y+50),60,15))
            if b.name=="疃望塔":
                pygame.draw.rect(self.screen,b.color,(int(b.x-15),int(b.y),30,55))
                pygame.draw.polygon(self.screen,C_BROWN,[(int(b.x-20),int(b.y)),(int(b.x+30),int(b.y)),(int(b.x+5),int(b.y-25))])
            elif b.name=="冶炼屋":
                pygame.draw.rect(self.screen,b.color,(int(b.x-25),int(b.y+10),50,45))
                pygame.draw.circle(self.screen,(255,100,0),(int(b.x),int(b.y+15)),12)
            else:
                pygame.draw.rect(self.screen,b.color,(int(b.x-25),int(b.y+10),50,45))
                pygame.draw.polygon(self.screen,C_BROWN,[(int(b.x-30),int(b.y+10)),(int(b.x+25),int(b.y+10)),(int(b.x-2),int(b.y-20))])
            nm=self.fn["xs"].render(b.name[:4],True,C_WHITE); self.screen.blit(nm,(int(b.x-20),int(b.y+56)))
        px,py=cx+sz//2-15,cy+sz//2-15
        pygame.draw.ellipse(self.screen,(0,0,0,50),(int(px-2),int(py+28),34,14))
        pygame.draw.ellipse(self.screen,C_HUNGER,(int(px),int(py),30,30))
        for ex,ey in [(9,10),(21,10)]:
            pygame.draw.circle(self.screen,C_WHITE,(int(px+ex),int(py+ey)),4)
            pygame.draw.circle(self.screen,C_BLACK,(int(px+ex+1),int(py+ey+1)),2)

    def _draw_minimap(self):
        mx,my=SW-175,SH-155; mw,mh=155,135
        pygame.draw.rect(self.screen,(0,0,0,180),(mx,my,mw,mh),border_radius=8)
        pygame.draw.rect(self.screen,C_WHITE,(mx,my,mw,mh),1,border_radius=8)
        pygame.draw.ellipse(self.screen,C_SAND,(mx+20,my+20,115,95))
        for b in self.p.buildings:
            bx=(b.x/SW)*mw+mx; by=(b.y/SH)*mh+my; pygame.draw.circle(self.screen,b.color,(int(bx),int(by)),4)
        pcx=(SW//2/SW)*mw+mx; pcy=(SH//2/SH)*mh+my
        pygame.draw.circle(self.screen,C_HUNGER,(int(pcx),int(pcy)),5)
        t=self.fn["xs"].render("小地图",True,C_GOLD); self.screen.blit(t,(mx+5,my+5))

    def _draw_ach_popup(self,dt):
        if not self.ap: return
        self.ap_t-=dt
        if self.ap_t<=0: self.ap=None; return
        x,y=SW//2-200,80
        pygame.draw.rect(self.screen,(0,0,0,220),(x,y,400,80),border_radius=12)
        pygame.draw.rect(self.screen,C_GOLD,(x,y,400,80),2,border_radius=12)
        na,de=self.ap
        t1=self.fn["md"].render(na,True,C_GOLD); t2=self.fn["sm"].render(de,True,C_WHITE)
        self.screen.blit(t1,(x+20,y+12)); self.screen.blit(t2,(x+20,y+48))
        p=self.ap_t/3.5
        pygame.draw.rect(self.screen,C_DARK,(x+5,y+73,390,5),border_radius=3)
        pygame.draw.rect(self.screen,C_GOLD,(x+5,y+73,int(390*p),5),border_radius=3)

    def _draw_ui(self):
        self._bar(20,20,220,22,self.p.health,self.p.max_health,C_HEALTH)
        t=self.fn["xs"].render("❤ {} / {}".format(self.p.health,self.p.max_health),True,C_WHITE); self.screen.blit(t,(25,22))
        self._bar(20,48,220,22,self.p.hunger,100,C_HUNGER)
        t=self.fn["xs"].render("🍖 {}".format(self.p.hunger),True,C_WHITE); self.screen.blit(t,(25,50))
        self._bar(20,76,220,22,self.p.energy,100,C_ENERGY)
        t=self.fn["xs"].render("⚡ {}".format(self.p.energy),True,C_BLACK); self.screen.blit(t,(25,78))
        t=self.fn["md"].render("📅 第 {} 天".format(self.p.day),True,C_GOLD); self.screen.blit(t,(250,22))
        t=self.fn["sm"].render("行动点: {}/3".format(self.pts),True,C_WHITE); self.screen.blit(t,(250,55))
        t=self.fn["sm"].render("等级:{}  经验:{}/{}".format(self.p.level,self.p.exp,self.p.level*30),True,C_SUCCESS); self.screen.blit(t,(250,82))
        wp=self.p.weapon or "无"; ar=self.p.armor or "无"
        t=self.fn["xs"].render("⚔ {}  🛡 {}".format(wp,ar),True,C_WHITE); self.screen.blit(t,(250,108))
        t=self.fn["xs"].render("🏗️ 岛屿:{}  建筑:{}".format(self.p.island_size,len(self.p.buildings)),True,C_WHITE); self.screen.blit(t,(250,132))

    def _draw_main_panel(self):
        # Left panel - inventory
        pygame.draw.rect(self.screen,(0,0,0,180),(20,170,280,460),border_radius=10)
        pygame.draw.rect(self.screen,C_OCEAN,(20,170,280,460),2,border_radius=10)
        t=self.fn["md"].render("📦 背包",True,C_SAND); self.screen.blit(t,(30,178))
        y=215
        for item,cnt in sorted(self.p.inventory.items()):
            tp=ITEMS.get(item)
            col=tp[2] if tp else C_WHITE
            pygame.draw.rect(self.screen,col,(30,y,18,18),border_radius=3)
            pygame.draw.rect(self.screen,C_WHITE,(30,y,18,18),1,border_radius=3)
            t=self.fn["xs"].render("{} x{}".format(item,cnt),True,C_WHITE); self.screen.blit(t,(55,y+1))
            y+=26
            if y>600: break
        # Right panel - buildings
        rx=SW-300
        pygame.draw.rect(self.screen,(0,0,0,180),(rx,170,280,460),border_radius=10)
        pygame.draw.rect(self.screen,C_GRASS,(rx,170,280,460),2,border_radius=10)
        t=self.fn["md"].render("🏗️ 建筑",True,C_SAND); self.screen.blit(t,(rx+10,178))
        y=215
        for b in self.p.buildings:
            pygame.draw.rect(self.screen,b.color,(rx+10,y,20,20),border_radius=3)
            pygame.draw.rect(self.screen,C_WHITE,(rx+10,y,20,20),1,border_radius=3)
            t=self.fn["xs"].render(b.name,True,C_SUCCESS); self.screen.blit(t,(rx+38,y+2))
            y+=26
            if y>600: break
        if not self.p.buildings:
            t=self.fn["xs"].render("暂无建筑",True,(100,100,100)); self.screen.blit(t,(rx+10,y+2))

    def _draw_action_buttons(self):
        # Bottom action bar
        pygame.draw.rect(self.screen,(0,0,0,150),(20,SH-130,SW-40,110),border_radius=10)
        pygame.draw.rect(self.screen,C_WHITE,(20,SH-130,SW-40,110),1,border_radius=10)
        self._btn(30,SH-115,120,50,"🎣 捕捞",C_OCEAN,C_WHITE)
        self._btn(165,SH-115,120,50,"🗺 探索",C_GRASS,C_WHITE)
        self._btn(300,SH-115,120,50,"🚖 进食",C_HUNGER,C_BLACK)
        self._btn(435,SH-115,120,50,"💚 治疗",C_SUCCESS,C_WHITE)
        self._btn(570,SH-115,120,50,"🏗️ 建造",C_BROWN,C_WHITE)
        self._btn(705,SH-115,120,50,"✅ 制作",C_STONE,C_WHITE)
        self._btn(840,SH-115,120,50,"🏆 成就",C_GOLD,C_BLACK)
        self._btn(975,SH-115,120,50,"💾 存档",C_OCEAN,C_WHITE)
        self._btn(1110,SH-115,120,50,"🌅 下一天",C_WARNING,C_WHITE)
        self._btn(30,SH-200,160,55,"📋 托盘",C_DARK,C_WHITE)


    def _draw_inventory_overlay(self):
        # Semi-transparent overlay
        overlay=pygame.Surface((SW,SH),pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); self.screen.blit(overlay,(0,0))
        # Panel
        pw,ph=600,500; px,py=(SW-pw)//2,(SH-ph)//2
        pygame.draw.rect(self.screen,(20,20,40),(px,py,pw,ph),border_radius=15)
        pygame.draw.rect(self.screen,C_SAND,(px,py,pw,ph),3,border_radius=15)
        t=self.fn["lg"].render("📦 背包",True,C_SAND); self.screen.blit(t,(px+20,py+15))
        # Items grid
        y=py+70; x=px+20
        for item,cnt in sorted(self.p.inventory.items()):
            tp=ITEMS.get(item)
            col=tp[2] if tp else C_WHITE
            dtype=tp[0] if tp else "?"
            pygame.draw.rect(self.screen,col,(x,y,30,30),border_radius=5)
            pygame.draw.rect(self.screen,C_WHITE,(x,y,30,30),1,border_radius=5)
            t=self.fn["sm"].render("{} x{}".format(item,cnt),True,C_WHITE); self.screen.blit(t,(x+38,y+4))
            t=self.fn["xs"].render("[{}]".format(dtype),True,(150,150,150)); self.screen.blit(t,(x+38,y+24))
            x+=200
            if x>pw+px-200:
                x=px+20; y+=55
        t=self.fn["sm"].render("按 ESC 关闭",True,(150,150,150)); self.screen.blit(t,(px+pw-130,py+ph-35))

    def _draw_craft_overlay(self):
        overlay=pygame.Surface((SW,SH),pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); self.screen.blit(overlay,(0,0))
        pw,ph=700,500; px,py=(SW-pw)//2,(SH-ph)//2
        pygame.draw.rect(self.screen,(20,20,40),(px,py,pw,ph),border_radius=15)
        pygame.draw.rect(self.screen,C_STONE,(px,py,pw,ph),3,border_radius=15)
        t=self.fn["lg"].render("✅ 制作",True,C_SAND); self.screen.blit(t,(px+20,py+15))
        y=py+70
        for name,cost in RECIPES.items():
            can=all(self.p.has(i)>=n for i,n in cost.items())
            bg=C_SUCCESS if can else C_DARK
            col=C_WHITE if can else (100,100,100)
            pygame.draw.rect(self.screen,bg,(px+20,y,pw-40,40),border_radius=6)
            t=self.fn["sm"].render("✔ {} : {}".format(name," ".join("{}x{}".format(i,n) for i,n in cost.items())),True,col); self.screen.blit(t,(px+30,y+8))
            y+=48
            if y>py+ph-80: break
        t=self.fn["sm"].render("按 ESC 关闭",True,(150,150,150)); self.screen.blit(t,(px+pw-130,py+ph-35))

    def _draw_build_overlay(self):
        overlay=pygame.Surface((SW,SH),pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); self.screen.blit(overlay,(0,0))
        pw,ph=700,500; px,py=(SW-pw)//2,(SH-ph)//2
        pygame.draw.rect(self.screen,(20,20,40),(px,py,pw,ph),border_radius=15)
        pygame.draw.rect(self.screen,C_BROWN,(px,py,pw,ph),3,border_radius=15)
        t=self.fn["lg"].render("🏗️ 建造",True,C_SAND); self.screen.blit(t,(px+20,py+15))
        y=py+70
        for name,data in BUILDINGS.items():
            built=any(b.name==name for b in self.p.buildings)
            cost=RECIPES.get(name,{})
            can=not built and all(self.p.has(i)>=n for i,n in cost.items())
            bg=C_SUCCESS if can else (C_WARNING if not built else C_STONE)
            col=C_WHITE if can else (150,150,150)
            txt="✔ {} : {}".format(name," ".join("{}x{}".format(i,n) for i,n in cost.items())) if not built else "{} 已建造".format(name)
            pygame.draw.rect(self.screen,bg,(px+20,y,pw-40,45),border_radius=6)
            t=self.fn["sm"].render(txt,True,col); self.screen.blit(t,(px+30,y+10))
            y+=55
            if y>py+ph-80: break
        t=self.fn["sm"].render("按 ESC 关闭",True,(150,150,150)); self.screen.blit(t,(px+pw-130,py+ph-35))

    def _draw_ach_overlay(self):
        overlay=pygame.Surface((SW,SH),pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); self.screen.blit(overlay,(0,0))
        pw,ph=500,450; px,py=(SW-pw)//2,(SH-ph)//2
        pygame.draw.rect(self.screen,(20,20,40),(px,py,pw,ph),border_radius=15)
        pygame.draw.rect(self.screen,C_GOLD,(px,py,pw,ph),3,border_radius=15)
        t=self.fn["lg"].render("🏆 成就",True,C_GOLD); self.screen.blit(t,(px+20,py+15))
        y=py+70
        for key,name,desc in ACHIEVEMENTS:
            unlocked=key in self.p.achievements
            bg=C_SUCCESS if unlocked else C_DARK
            col=C_WHITE if unlocked else (100,100,100)
            st="\u2714" if unlocked else "\u2716"
            pygame.draw.rect(self.screen,bg,(px+20,y,pw-40,40),border_radius=6)
            t=self.fn["sm"].render("{} {} - {}".format(st,name,desc),True,col); self.screen.blit(t,(px+30,y+8))
            y+=48
        t=self.fn["sm"].render("按 ESC 关闭",True,(150,150,150)); self.screen.blit(t,(px+pw-130,py+ph-35))

    def _draw_combat_ui(self):
        if not self.ce: return
        overlay=pygame.Surface((SW,SH),pygame.SRCALPHA)
        overlay.fill((0,0,0,200)); self.screen.blit(overlay,(0,0))
        # Enemy info
        e=self.ce
        pw,ph=900,400; px,py=(SW-pw)//2,(SH-ph)//2
        pygame.draw.rect(self.screen,(30,10,10),(px,py,pw,ph),border_radius=15)
        pygame.draw.rect(self.screen,e.color,(px,py,pw,ph),3,border_radius=15)
        # Enemy display
        pygame.draw.circle(self.screen,e.color,(px+pw//2,py+80),50)
        t=self.fn["lg"].render(e.name,True,e.color); self.screen.blit(t,(px+pw//2-60,py+140))
        # HP bar
        self._bar(px+50,py+175,800,25,self.chp,e.max_hp,e.color)
        t=self.fn["sm"].render("HP: {}/{}".format(max(0,self.chp),e.max_hp),True,C_WHITE); self.screen.blit(t,(px+60,py+178))
        # Player info
        pygame.draw.rect(self.screen,(10,30,10),(px,py+210,pw,ph-220),border_radius=10)
        self._bar(px+50,py+225,800,25,self.p.health,self.p.max_health,C_HEALTH)
        t=self.fn["sm"].render("❤ {} / {}".format(self.p.health,self.p.max_health),True,C_WHITE); self.screen.blit(t,(px+60,py+228))
        self._bar(px+50,py+258,800,25,self.p.hunger,100,C_HUNGER)
        t=self.fn["sm"].render("🍖 {} / 100".format(self.p.hunger),True,C_WHITE); self.screen.blit(t,(px+60,py+261))
        # Combat log
        t=self.fn["sm"].render("等级:{}  武器:{}  防具:{}".format(self.p.level,self.p.weapon or "无",self.p.armor or "无"),True,C_SUCCESS); self.screen.blit(t,(px+60,py+295))
        for i,log in enumerate(self.clog[-3:]):
            t=self.fn["sm"].render(log,True,C_WHITE); self.screen.blit(t,(px+60,py+320+i*25))
        # Combat buttons
        bw=180; bh=55
        for label,xp,yp,action in [
            ("⚔️ 攻击",px+50,py+ph-75,self._ca_attack),
            ("🛡️ 防御",px+260,py+ph-75,self._ca_defend),
            ("💚 用药",px+470,py+ph-75,self._ca_item),
            ("🏃 逃脱",px+680,py+ph-75,self._ca_run),
        ]:
            bg=C_HEALTH if action==self._ca_attack else (C_STONE if action==self._ca_defend else (C_SUCCESS if action==self._ca_item else C_HUNGER))
            self._btn(xp,yp,bw,bh,label,bg,C_WHITE)
            self._combat_btns.append((xp,yp,bw,bh,action))

    def _draw_menu(self):
        self._draw_bg()
        # Title
        t=self.fn["lg"].render("🏟️ 荒岛求生",True,C_SAND)
        self.screen.blit(t,t.get_rect(center=(SW//2,SH//2-100)))
        t=self.fn["sm"].render("Survival Island Game v2.0",True,(180,180,180))
        self.screen.blit(t,t.get_rect(center=(SW//2,SH//2-50)))
        for label,x,y,w,h,bg in self.menu_btns:
            self._btn(x,y,w,h,label,bg,C_WHITE)
        # Check for existing save
        has_save=os.path.exists("save.json")
        if not has_save:
            t=self.fn["xs"].render("暂无存档",True,(100,100,100)); self.screen.blit(t,(SW//2-40,SH//2+165))



    def _do_restart(self):
        self.p=Player(); self.p.inventory={}
        self.p.add("木材",15); self.p.add("石头",8); self.p.add("鱼",3); self.p.add("绳索",3)
        self.pts=3; self.state="menu"; self.build_slots=self._gen_slots()
        self.dis=[]; self.msgs=[]; self.parts=Parts(); self.ap=None
        self.quest=None; self.drift_opened=False; self.intro_done=False; self.intro_slide=0; self.intro_t=0.0
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT: self.running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    self.show_inv=False; self.show_cft=False; self.show_ach=False; self.show_bld=False
                elif self.state=="menu":
                    if event.key in (pygame.K_RETURN,pygame.K_SPACE):
                        if os.path.exists("save.json") and self.load(): self.state="main"
                        else: self.state="main"
                elif self.state=="main":
                    # Keyboard shortcuts
                    if event.key==pygame.K_1: self._do_fish()
                    elif event.key==pygame.K_2: self._do_explore()
                    elif event.key==pygame.K_3: self._do_eat()
                    elif event.key==pygame.K_4: self._do_heal()
                    elif event.key==pygame.K_s: self.save()
                    elif event.key==pygame.K_n: self._next_day()
                    elif event.key==pygame.K_i: self.show_inv=not self.show_inv
                    elif event.key==pygame.K_c: self.show_cft=not self.show_cft
                    elif event.key==pygame.K_b: self.show_bld=not self.show_bld
                    elif event.key==pygame.K_a: self.show_ach=not self.show_ach
            elif event.type==pygame.MOUSEBUTTONDOWN:
                mx,my=event.pos
                if self.state=="menu":
                    for label,x,y,w,h,bg in self.menu_btns:
                        if x<=mx<=x+w and y<=my<=y+h:
                            self._play("button")
                            if "退出" in label: self.running=False
                            elif "继续" in label:
                                if self.load(): self.state="main"
                            else: self.state="main"
                elif self.state=="main":
                    # Bottom action buttons
                    if SH-130<=my<=SH-20:
                        if 30<=mx<=150: self._do_fish()
                        elif 165<=mx<=285: self._do_explore()
                        elif 300<=mx<=420: self._do_eat()
                        elif 435<=mx<=555: self._do_heal()
                        elif 570<=mx<=690: self.show_bld=True
                        elif 705<=mx<=825: self.show_cft=True
                        elif 840<=mx<=960: self.show_ach=True
                        elif 975<=mx<=1095: self.save()
                        elif 1110<=mx<=1230: self._next_day()
                        elif 30<=mx<=190 and SH-210<=my<=SH-145: self.show_inv=not self.show_inv
                    # Craft overlay buttons
                    if self.show_cft:
                        pw,ph=700,500; px,py=(SW-pw)//2,(SH-ph)//2
                        if px+20<=mx<=px+pw-20 and py+70<=my<=py+ph-80:
                            idx=(my-(py+70))//48
                            names=[n for n in RECIPES.keys()]
                            if 0<=idx<len(names): self._do_craft(names[idx])
                    # Build overlay buttons
                    if self.show_bld:
                        pw,ph=700,500; px,py=(SW-pw)//2,(SH-ph)//2
                        if px+20<=mx<=px+pw-20 and py+70<=my<=py+ph-80:
                            idx=(my-(py+70))//55
                            names=[n for n in BUILDINGS.keys()]
                            if 0<=idx<len(names): self._do_build(names[idx])

    def _update(self,dt):
        self.parts.update(dt)
        for d in self.dis[:]:
            d.update(dt)
            if d.done: self.dis.remove(d)
        for m in self.msgs[:]:
            m=(m[0],m[1]-dt)
            if m[1]<=0: self.msgs.remove(m)
        if self.shk>0: self.shk-=dt
        if self.ap_t>0: self.ap_t-=dt
        elif self.ap: self.ap=None

    def _draw(self):
        if self.state=="menu":
            self._draw_menu()
        elif self.state=="main":
            # Screen shake
            ox=random.randint(-3,3) if self.shk>0 else 0
            oy=random.randint(-3,3) if self.shk>0 else 0
            surf=self.screen
            if ox or oy:
                surf=self.screen.copy()
            self._draw_bg()
            self._draw_island()
            for d in self.dis: d.draw(self.screen)
            self.parts.draw(self.screen)
            self._draw_minimap()
            self._draw_main_panel()
            self._draw_ui()
            self._draw_action_buttons()
            # Messages
            y=SH-260
            for m,t in self.msgs[-5:]:
                alpha=max(0,min(255,int(255*t/3)))
                col=tuple(min(255,c) for c in C_SUCCESS)
                tt=self.fn["sm"].render(m,True,col); tt.set_alpha(int(alpha*255))
                self.screen.blit(tt,(20,y)); y-=28
            self._draw_ach_popup(dt=0.016)
            if self.show_inv: self._draw_inventory_overlay()
            if self.show_cft: self._draw_craft_overlay()
            if self.show_bld: self._draw_build_overlay()
            if self.show_ach: self._draw_ach_overlay()
        elif self.state=="combat":
            self._draw_bg()
            self._draw_island()
            self._combat_btns=[]
            self._draw_combat_ui()
        elif self.state=="game_over":
            self._draw_bg()
            t=self.fn["lg"].render("💀 游戲结束",True,C_WARNING)
            self.screen.blit(t,t.get_rect(center=(SW//2,SH//2-80)))
            stats=["生存天数: {}".format(self.p.day),"捕捞:{} 死交:{} 建筑:{}".format(self.p.fish_count,self.p.enemy_kills,self.p.build_count),"成就: {}/7".format(len(self.p.achievements)),"","按 ESC 重新开始"]
            y=SH//2
            for s in stats:
                if s:
                    t=self.fn["md"].render(s,True,C_WHITE); self.screen.blit(t,t.get_rect(center=(SW//2,y)))
                y+=50
            for event in pygame.event.get():
                if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                    self.p=Player(); self.p.inventory={}
                    self.p.add("木材",15); self.p.add("矹头",8); self.p.add("鱼",3); self.p.add("细累",3)
                    self.pts=3; self.state="menu"; self.build_slots=self._gen_slots()
                    self.dis=[]; self.msgs=[]; self.parts=Parts()
        elif self.state=="victory":
            self._draw_ending_screen()
            self.screen.blit(t,t.get_rect(center=(SW//2,SH//2-100)))
            stats=["生存{} 天成功！".format(self.p.day),"捕捞:{} 死交:{} 建筑:{}".format(self.p.fish_count,self.p.enemy_kills,self.p.build_count),"成就: {}/7".format(len(self.p.achievements)),"","按 ESC 重新开始"]
            y=SH//2
            for s in stats:
                if s:
                    t=self.fn["md"].render(s,True,C_WHITE); self.screen.blit(t,t.get_rect(center=(SW//2,y)))
                y+=50
            for event in pygame.event.get():
                if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                    self.p=Player(); self.p.inventory={}
                    self.p.add("木材",15); self.p.add("矹头",8); self.p.add("鱼",3); self.p.add("细累",3)
                    self.pts=3; self.state="menu"; self.build_slots=self._gen_slots()
                    self.dis=[]; self.msgs=[]; self.parts=Parts()
        pygame.display.flip()

    def run(self):
        while self.running:
            dt=self.clock.tick(FPS)/1000.0
            if not self.intro_done:
                self._draw_intro_screen()
                for event in pygame.event.get():
                    if event.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN):
                        self.intro_done=True; self.state="menu"
                continue
            self._handle_events()
            if self.state in ("main","combat"): self._update(dt)
            self._draw()
        pygame.quit()



class Quest:
    def __init__(self, qt, title, desc, tgt, cnt, rew):
        self.qtype=qt; self.title=title; self.desc=desc
        self.target=tgt; self.target_count=cnt; self.reward=rew
        self.current=0; self.completed=False

class StoryPage:
    def __init__(self, sid, title, content, mood):
        self.id=sid; self.title=title; self.content=content; self.mood=mood

DRIFT_BOTTLES=[
    StoryPage(1,"第一章：醒来","我在一片黑暗中醒来。海浪的声音越来越清晰……睁开眼，发现自己躺在一片陌生的沙滩上。天空很蓝，但我感到一阵深深的恐惧——我在哪里？这是什么时代？我只记得船剧烈摇晃，然后就……失去了意识。","fear"),
    StoryPage(2,"第一章：希望","我在沙滩上用漂流木搭了一个临时的庇护所。第一夜很冷，但至少我活了下来。我告诫自己：无论如何，都要活下去。在潮汐退去后的沙滩上，我发现了一些有用的东西——生活还要继续。","hope"),
    StoryPage(3,"第一章：记忆","翻看口袋时，我找到了一张被海水浸泡过的照片。照片里是一个女人和一个大约五岁的男孩。他们是谁？为什么我会带着这张照片？记忆像碎片一样模糊……","memory"),
    StoryPage(4,"第二章：第二十天","已经在这个岛上生活了二十天。我的木屋已经扩建了，甚至还有了一个冶炼的小火炉。但每天夜里，我都会做同样的梦——那个女人和男孩在远处向我招手，我却怎么也走不过去。","peace"),
    StoryPage(5,"第二章：暴风雨","暴风雨来得毫无预兆。雷电交加，我躲在小木屋里瑟瑟发抖，听着外面的世界仿佛要崩塌。但这场风暴也带来了意想不到的礼物——海水冲来了一个密封的箱子，里面有一些工具和一本残缺的航海日志。","fear"),
    StoryPage(6,"第三章：日志","日志的大部分页面已经被海水侵蚀，只剩下零星的片段。日志的最后一行写着：如果有人找到这个，请告诉我的家人，我一直在寻找他们。那是我的手写体……那是我的字迹？","memory"),
    StoryPage(7,"第三章：真相","那个女人叫林雨晴。那个男孩叫小海。他们是我的家人。记忆像潮水一样涌回来——我是一名远洋船长，我的船在风暴中沉没了。但我是怎么来到这个岛的？为什么我独自一人？","hope"),
    StoryPage(8,"终章：离去","第三十天清晨，海面上出现了一艘船的影子。我用篝火发出了信号。这三十天的经历改变了我——我找到了自己的过去，也找到了活下去的勇气。无论前方等待我的是什么，我都不再害怕。","peace"),
]

ENDINGS={
    "normal":("普通结局 - 孤独的生还者","你成功在荒岛上生存了30天并获救。但那些记忆的碎片，始终没有拼凑完整。漂流瓶里的故事，成了你永远无法解开的谜。","grey"),
    "memory":("记忆结局 - 父亲的归来","你成功在荒岛上生存了30天。找到了妻子林雨晴和儿子小海的照片后，你决心要活下去找到他们。在获救的那一刻，你发誓无论花多长时间，都要把他们找回来。","gold"),
    "survivor":("生存结局 - 岛的主人","你在荒岛上建立了属于自己的王国。有建筑、有装备、有动物朋友。你选择留在这个岛上，成为了真正的岛主。这里就是你的家。","green"),
    "legend":("传说结局 - 海神祝福","在第30天的夜晚，你获得了传说中的三叉戟和海神甲。海龙王的身影在月光下浮现——它是来祝福你的。你被送往了传说中的海底之城。","purple"),
    "none":("沉默结局 - 无人知晓","你消失了。没有人在这片海域寻找你。但或许在某一天，会有人发现你留下的那些建筑残骸，猜想到曾经有一个人在这里生活过。","dark"),
}

if __name__=="__main__":
    Game().run()
