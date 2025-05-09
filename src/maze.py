import pygame
import json
import os

class Maze:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def load(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Map file '{path}' not found. Ensure it exists in the correct directory.")
        
        try:
            with open(path, 'r') as f:
                map_data = json.load(f)
            self.tilemap = map_data['tilemap']
            self.offgrid_tiles = map_data.get('offgrid', [])
            # Chuẩn hóa tile['scale'] và kiểm tra tile['pos']
            for loc in self.tilemap:
                tile = self.tilemap[loc]
                if 'scale' not in tile:
                    tile['scale'] = self.tile_size
                if not isinstance(tile['pos'], (list, tuple)) or len(tile['pos']) != 2:
                    print(f"Warning: Invalid pos for tile at {loc}: {tile['pos']}")
                    tile['pos'] = [int(x) for x in loc.split(';')]
                # Đảm bảo scale đúng cho WallStone
                if tile['type'] == "WallStone" and tile['variant'] == 0:
                    tile['scale'] = (self.tile_size[0], self.tile_size[1] * 2)
                else:
                    tile['scale'] = self.tile_size
                # Log các ô có pos hoặc scale bất thường
                if tile['pos'][1] < 0 or tile['scale'][1] <= 0:
                    print(f"Warning: Suspicious tile at {loc}: pos={tile['pos']}, scale={tile['scale']}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from '{path}': {e}")
        except KeyError as e:
            raise KeyError(f"Missing required key {e} in '{path}'. Ensure the JSON file has 'tilemap' and 'offgrid' keys.")

    def save(self, path, scale):
        for tile in self.tilemap.copy():
            if self.tilemap[tile]['type'] == "WallStone" and self.tilemap[tile]['variant'] == 0:
                self.tilemap[tile]['scale'] = (scale[0], scale[1] * 2)
            else:
                self.tilemap[tile]['scale'] = scale
        
        try:
            with open(path, 'w') as f:
                json.dump({
                    'tilemap': self.tilemap,
                    'tile_size': self.tile_size,
                    'offgrid': self.offgrid_tiles
                }, f, indent=4)
        except IOError as e:
            raise IOError(f"Error writing to '{path}': {e}")

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game["assets"][tile['type']][tile['variant']], (
                tile['pos'][0] - offset[0],
                tile['pos'][1] - offset[1]
            ))

        for loc in self.tilemap:
            tile = self.tilemap[loc]
            render_scale = tile.get('scale', self.tile_size)
            # Đảm bảo scale hợp lệ
            if not (isinstance(render_scale, (list, tuple)) and len(render_scale) == 2):
                print(f"Warning: Invalid scale for tile at {loc}: {render_scale}. Using tile_size.")
                render_scale = self.tile_size
            try:
                scaled_image = pygame.transform.scale(
                    self.game["assets"][tile['type']][tile['variant']],
                    render_scale
                )
                surf.blit(
                    scaled_image,
                    (
                        tile['pos'][0] * self.tile_size[0] - offset[0],
                        tile['pos'][1] * self.tile_size[1] - offset[1]
                    )
                )
            except KeyError as e:
                print(f"Error rendering tile at {loc}: Missing asset {e}")
            except Exception as e:
                print(f"Error rendering tile at {loc}: {e}")