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
    inventory: Dict=int; buildings: List=field(default_factory=list)
    achievements: List=field(default_factory=list)
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
        if any(x.name=="防御墙" for x in self.buildings): b+=10
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
        self.menu_btns=[("开始游戏",SW//2-120,SH//2+60,240,60,C_SUCCESS),("继续游戏",SW//2-120,SH//2+140,240,60,C_OCEAN),("退出游戏",SW//2-120,SH//2+220,240,60,C_WARNING)]
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

    def _do_explore(self):
        if self.pts<=0: self.add_msg('⚠ 没有行动点了！'); return
        self.pts-=1; self.p.hunger=max(0,self.p.hunger-20); self.p.energy=max(0,self.p.energy-15)
        f=random.choice([{'木材':random.randint(3,6)},{'石头':random.randint(2,5)},
                        {'椰子':random.randint(1,3)},{'草药':random.randint(1,3)},
                        {'布料':random.randint(1,2)},{'金属':random.randint(1,2)}])
        for i,n in f.items(): self.p.add(i,n)
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
        if self.p.day>=30: self.state='victory'
        elif not self.p.is_alive(): self.state='game_over'
        self.add_msg(f'🌅 第 {self.p.day} 天开始了...')


    # ---- Drawing ----
    def _bar(self,x,y,w,h,cur,mx,col):
        pygame.draw.rect(self.screen,C_DARK,(x,y,w,h))
        if mx>0: pygame.draw.rect(self.screen,col,(x,y,int(w*min(1,cur/mx)),h))
        pygame.draw.rect(self.screen,C_WHITE,(x,y,w,h),1)

    def _btn(self,x,y,w,h,text,bg,fg):
        pygame.draw.rect(self.screen,bg,(x,y,w,h),border_radius=8)
        pygame.draw.rect(self.screen,C_WHITE,(x,y,w,h),1,border_radius=8)
        t=self.fn["sm"].render(text,True,fg)
        self.screen.blit(t,t.get_rect(center=(x+w//2,y+h//2)))

    def _draw_bg(self):
        self.day_e+=0.004
        t=(math.sin(self.day_e)+1)/2
        r=int(C_OCEAN[0]*(1-t)+C_OCEAN_D[0]*t)
        g=int(C_OCEAN[1]*(1-t)+C_OCEAN_D[1]*t)
        b=int(C_OCEAN[2]*(1-t)+C_OCEAN_D[2]*t)
        self.screen.fill((r,g,b)); self.night=t<0.3
        if self.night:
            for sx,sy in self.stars:
                alpha=random.uniform(0.3,1.0)
                sc=tuple(int(v*alpha) for v in C_WHITE)
                pygame.draw.circle(self.screen,sc,(sx,sy),1)

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
            # Handle combat button clicks
            for event in pygame.event.get():
                if event.type==pygame.MOUSEBUTTONDOWN:
                    mx,my=event.pos
                    for xp,yp,w,h,action in self._combat_btns:
                        if xp<=mx<=xp+w and yp<=my<=yp+h:
                            action()
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
            self._draw_bg()
            t=self.fn["lg"].render("🎉 恭喜通关！",True,C_GOLD)
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
            self._handle_events()
            if self.state in ("main","combat"): self._update(dt)
            self._draw()
        pygame.quit()

if __name__=="__main__":
    Game().run()
