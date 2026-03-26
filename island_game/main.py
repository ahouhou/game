"""荒岛求生 - Survival Island v3.0
入口文件。直接运行: python3 main.py
"""
import os, sys

# 确保从 game 目录运行，或者切换工作目录
if not os.path.exists("config.py"):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
from game import Game

def main():
    pygame.init()
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
