import pygame
import sys
from config import load_image,load_images
from src.maze import Maze
RENDER_SCALE=3
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze-Game")
        self.screen=pygame.display.set_mode((960,720))
        self.clock=pygame.time.Clock()
        self.display=pygame.Surface((320,240))
        self.assets={
            'WallStone':load_images('level/WallStone'),
            'WallBreakable':load_images('level/WallBreakable'),
            'Earth':load_images('level/Earth')
        }
        self.tilemap=Maze(self,(17,12))
        try: 
            self.tilemap.load('map1.json')
        except FileNotFoundError:
            pass
        self.tile_list=list(self.assets)
        self.tile_group=0
        self.tile_variant=0
        self.shift=False
        self.clicking=False
        self.right_clicking=False
        self.tile_scale=(17,12)
        self.scale=self.tile_scale
        self.scroll=[0,0]
        self.movement=[False,False,False,False]
    def run(self):
        while True:
            self.display.fill( (132, 94, 60 ))
            self.scroll[0]+=(self.movement[1]-self.movement[0])*2
            self.scroll[1]+=(self.movement[3]-self.movement[2])*2
            render_scroll=(int(self.scroll[0]),int(self.scroll[1]))
            current_tile_img=self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)
            mpos=pygame.mouse.get_pos()
            mpos=(mpos[0]/RENDER_SCALE,mpos[1]/RENDER_SCALE)
            tile_pos=(int((mpos[0]+self.scroll[0])//self.tilemap.tile_size[0]),int((mpos[1]+self.scroll[1])//self.tilemap.tile_size[1]))
            if (self.tile_group==0) and (self.tile_variant==0):
                self.scale=list(self.scale)
                self.scale[1]=self.tile_scale[1]*2
                self.scale=tuple(self.scale)
            else:
                self.scale=self.tile_scale
            if self.right_clicking:
                tile_loc=(str(tile_pos[0])+";"+str(tile_pos[1]))
                if tile_loc in self.tilemap.tilemap:
                   del self.tilemap.tilemap[tile_loc]
            if self.clicking:
                self.tilemap.tilemap[str(tile_pos[0])+";"+str(tile_pos[1])]={'type':self.tile_list[self.tile_group],'variant':self.tile_variant,'pos':tile_pos,'scale':self.scale}
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type==pygame.MOUSEBUTTONDOWN:
                    if event.button==1:
                        self.clicking=True
                    if event.button==3:
                        self.right_clicking=True
                    if self.shift:
                        if event.button==4:
                            self.tile_variant=(self.tile_variant-1)%len(self.assets[self.tile_list[self.tile_group]])
                        if event.button==5:
                            self.tile_variant=(self.tile_variant+1)%len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button==4:
                            self.tile_variant=0
                            self.tile_group=(self.tile_group-1)%len(self.tile_list)
                        if event.button==5:
                            self.tile_variant=0
                            self.tile_group=(self.tile_group+1)%len(self.tile_list)
                if event.type==pygame.MOUSEBUTTONUP:
                    if event.button==1:
                        self.clicking =False
                    if event.button==3:
                        self.right_clicking=False
                if event.type==pygame.KEYDOWN:
                    if event.key==pygame.K_LSHIFT:
                        self.shift=True
                    if event.key==pygame.K_a:
                        self.movement[0]=True
                    if event.key==pygame.K_d:
                        self.movement[1]=True
                    if event.key == pygame.K_w:
                        self.movement[2]=True
                    if event.key == pygame.K_s:
                        self.movement[3]=True
                    if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                       
                        self.tilemap.save('map1.json')
                      
                if event.type==pygame.KEYUP:
                    if event.key==pygame.K_LSHIFT:
                        self.shift=False
                    if event.key==pygame.K_a:
                        self.movement[0]=False
                    if event.key==pygame.K_d:
                        self.movement[1]=False
                    if event.key == pygame.K_w:
                        self.movement[2]=False
                    if event.key == pygame.K_s:
                        self.movement[3]=False
                        
            pygame.display.update()
            self.tilemap.render(self.display,render_scroll)
            self.display.blit(pygame.transform.scale(current_tile_img,self.scale),(tile_pos[0]*self.tilemap.tile_size[0]-self.scroll[0],tile_pos[1]*self.tilemap.tile_size[1]-self.scroll[1]))
            self.screen.blit(pygame.transform.scale(self.display,self.screen.get_size()) ,(0,0))
            self.clock.tick(60)
            
Game().run()