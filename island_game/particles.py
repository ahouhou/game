"""Particle system for visual effects."""

import random, math
from config import SW, SH

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size')

    def __init__(self, x, y, vx, vy, life, color, size=3):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += 0.5 * dt * 60       # gravity
        self.life -= dt
        return self.life > 0

    def draw(self, surface):
        alpha = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * alpha))
        c = tuple(int(v * alpha) for v in self.color)
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r)


import pygame

class Particles:
    def __init__(self):
        self.items: list = []

    def burst(self, x, y, count=15, color=(255, 200, 50), speed=120, size=3):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.3, speed)
            self.items.append(Particle(
                x, y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.uniform(0.4, 1.0),
                color, size,
            ))

    def rain(self, x, y, count=10, color=(100, 150, 255)):
        for _ in range(count):
            self.items.append(Particle(
                random.randint(0, SW), random.randint(-20, y),
                random.uniform(-10, 10), random.uniform(300, 500),
                random.uniform(0.3, 0.6), color, 2,
            ))

    def update(self, dt):
        self.items = [p for p in self.items if p.update(dt)]

    def draw(self, surface):
        for p in self.items:
            p.draw(surface)

    def clear(self):
        self.items.clear()
