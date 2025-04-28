import pygame
import os
import sys
from config import load_image, load_images
from src.button import Button
from editor import Editor
from main import Game
class Menu:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze-Game with Enemies")
        self.screen = pygame.display.set_mode((960, 720))
        self.clock = pygame.time.Clock()
        self.display = pygame.Surface((320, 240))

        # background
        self.background=load_image("background.png")
        # Button
        self.btn_play=Button(95,155,load_image("button/PlayBtn.png"),load_image("button/PlayClick.png"),0.08)
        self.btn_opt=Button(170,155,load_image("button/OptBtn.png"),load_image("button/OptClick.png"),0.08)

        self.editor=Editor()
        self.game=Game()

    def run(self):
        while True: 
            
            self.display.blit(pygame.transform.scale(self.background,self.display.get_size()),(0,0))
            if self.btn_play.draw(self.display,self.screen):
                self.game.run()
            if self.btn_opt.draw(self.display,self.screen):
                self.editor.run()
            
 
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            # Cập nhật màn hình
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Menu().run()