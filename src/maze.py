import pygame
import json

class Maze:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)
        self.tilemap = map_data['tilemap']
        self.offgrid_tiles = map_data['offgrid']

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game['assets'][tile['type']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for loc in self.tilemap:
            tile = self.tilemap[loc]
            surf.blit(
                pygame.transform.scale(self.game['assets'][tile['type']][tile['variant']], tile['scale']),
                (tile['pos'][0] * self.tile_size[0] - offset[0], tile['pos'][1] * self.tile_size[1] - offset[1])
            )
