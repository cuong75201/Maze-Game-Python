import pygame
import json
class Maze:
    def __init__(self,game,tile_size):
        self.game=game
        self.tile_size=tile_size
        self.tilemap={}
        self.offgrid_tiles=[]
    def load(self,path):
        f=open(path,'r')
        map_data=json.load(f)
        f.close()
        self.tilemap=map_data['tilemap']
        self.offgrid_tiles=map_data['offgrid']
    def save(self,path):
        for tile in self.tilemap.copy():
            if self.tilemap[tile]['type']=="WallStone" and self.tilemap[tile]['variant']==0:
                self.tilemap[tile]['scale']=(self.tile_size[0],self.tile_size[1]*2)
            else:
                self.tilemap[tile]['scale']=(self.tile_size[0],self.tile_size[1])
        f =open(path,'w')
        json.dump({'tilemap':self.tilemap,'tile_size':self.tile_size,'offgrid':self.offgrid_tiles},f)
        f.close()
    def render(self,surf,offset=(0,0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']],tile['pos']) 
        for loc in self.tilemap:
            tile=self.tilemap[loc]
            surf.blit(pygame.transform.scale(self.game.assets[tile['type']][tile['variant']],tile['scale']),(tile['pos'][0]*self.tile_size[0]-offset[0],tile['pos'][1]*self.tile_size[1]-offset[1]))