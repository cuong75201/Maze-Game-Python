import pygame
import sys
import math
import os

# Tính đường dẫn tuyệt đối đến thư mục Maze-Game-Python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import load_image, load_images
from maze import Maze
from enemy import Enemy
from player import Player

# Phần còn lại của game.py giữ nguyên
RENDER_SCALE = 3

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze Shooter Game with Editor")
        self.screen = pygame.display.set_mode((1100, 720))
        self.clock = pygame.time.Clock()
        self.display = pygame.Surface((320, 240))

        # Tải assets
        self.assets = {
            'WallStone': load_images('level/WallStone'),
            'WallBreakable': load_images('level/WallBreakable'),
            'Earth': load_images('level/Earth')
        }
        self.tilemap = Maze(self, (17, 12))
        try:
            self.tilemap.load('map1.json')
        except FileNotFoundError:
            print("Không tìm thấy map1.json, khởi tạo mê cung mặc định.")

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.shift = False
        self.clicking = False
        self.right_clicking = False
        self.tile_scale = (17, 12)
        self.scale = self.tile_scale
        self.scroll = [0, 0]
        self.movement = [False, False, False, False]  # [left, right, up, down]

        # Chuyển tilemap thành mê cung lưới
        self.maze_width, self.maze_height = 17, 12
        self.cell_size = self.tilemap.tile_size[0]  # Giả định tile_size[0] = tile_size[1]
        self.maze = self.convert_tilemap_to_maze()

        # Thiết lập biên giống editor.py
        self.BORDER_MARGIN = 20
        self.BORDER_THICKNESS = 10
        self.BORDER_HEIGHT = 720 - 2 * self.BORDER_MARGIN - 70
        self.BORDER_LEFT = self.BORDER_MARGIN + self.BORDER_THICKNESS
        self.BORDER_RIGHT = 1100 - self.BORDER_MARGIN - self.BORDER_THICKNESS
        self.BORDER_TOP = self.BORDER_MARGIN + self.BORDER_THICKNESS
        self.BORDER_BOTTOM = self.BORDER_MARGIN + self.BORDER_HEIGHT - self.BORDER_THICKNESS

        # Thêm người chơi
        player_start_pos = self.find_initial_player_position()
        self.player = Player(
            player_start_pos[1] * self.cell_size,
            player_start_pos[0] * self.cell_size,
            border_left=self.BORDER_LEFT,
            border_right=self.BORDER_RIGHT,
            border_top=self.BORDER_TOP,
            border_bottom=self.BORDER_BOTTOM,
            maze=self.tilemap
        )

        # Thêm quái vật
        self.enemies = [
            Enemy(3, 3, self.cell_size, self.maze_width, self.maze_height, self.maze, "slime"),
            Enemy(5, 5, self.cell_size, self.maze_width, self.maze_height, self.maze, "skeleton"),
            Enemy(7, 7, self.cell_size, self.maze_width, self.maze_height, self.maze, "ghost"),
            Enemy(9, 9, self.cell_size, self.maze_width, self.maze_height, self.maze, "giant"),
            Enemy(2, 2, self.cell_size, self.maze_width, self.maze_height, self.maze, "zombie")
        ]

    def convert_tilemap_to_maze(self):
        """Chuyển tilemap thành lưới 0 (đường) và 1 (tường)"""
        maze = [[1 for _ in range(self.maze_width)] for _ in range(self.maze_height)]
        for loc, tile in self.tilemap.tilemap.items():
            x, y = map(int, loc.split(';'))
            if 0 <= x < self.maze_width and 0 <= y < self.maze_height:
                if tile['type'] == 'Earth':
                    maze[y][x] = 0
                else:
                    maze[y][x] = 1
        return maze

    def find_initial_player_position(self):
        """Tìm vị trí ban đầu hợp lệ cho người chơi (ô đường đi)"""
        if self.maze[1][1] == 0:
            return [1, 1]
        for y in range(self.maze_height):
            for x in range(self.maze_width):
                if self.maze[y][x] == 0:
                    return [y, x]
        print("Warning: No valid starting position found for player. Using [1, 1].")
        return [1, 1]

    def run(self):
        while True:
            self.display.fill((132, 94, 60))  # Màu nền

            # Cập nhật scroll
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # Cập nhật người chơi
            keys = pygame.key.get_pressed()
            self.player.move(keys)
            if keys[pygame.K_SPACE]:
                self.player.shoot()
            self.player.update_bullets()

            # Cập nhật quái vật
            maze_changed = False
            player_grid_pos = [int(self.player.rect.y // self.cell_size), int(self.player.rect.x // self.cell_size)]
            for enemy in self.enemies:
                enemy.move(player_grid_pos, self.player.rect)

            # Xử lý chỉnh sửa tilemap
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
            current_tile_img.set_alpha(100)
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size[0]),
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size[1])
            )
            if (self.tile_group == 0) and (self.tile_variant == 0):
                self.scale = list(self.scale)
                self.scale[1] = self.tile_scale[1] * 2
                self.scale = tuple(self.scale)
            else:
                self.scale = self.tile_scale

            if self.right_clicking:
                tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                    self.maze = self.convert_tilemap_to_maze()
                    maze_changed = True

            if self.clicking:
                tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
                self.tilemap.tilemap[tile_loc] = {
                    'type': self.tile_list[self.tile_group],
                    'variant': self.tile_variant,
                    'pos': tile_pos,
                    'scale': self.scale
                }
                self.maze = self.convert_tilemap_to_maze()
                maze_changed = True

            if maze_changed:
                for enemy in self.enemies:
                    enemy.on_maze_changed()

            # Xử lý sự kiện
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_variant = 0
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                        if event.button == 5:
                            self.tile_variant = 0
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        self.tilemap.save('map1.json')
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False

            # Render mê cung
            self.tilemap.render(self.display, render_scroll)

            # Vẽ người chơi
            self.player.draw(self.display)

            # Vẽ quái vật
            for enemy in self.enemies:
                enemy.draw(self.display, render_scroll)

            # Vẽ tile đang chọn
            self.display.blit(pygame.transform.scale(current_tile_img, self.scale),
                             (tile_pos[0] * self.tilemap.tile_size[0] - self.scroll[0],
                              tile_pos[1] * self.tilemap.tile_size[1] - self.scroll[1]))

            # Cập nhật màn hình
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

if __name__ == "__main__":
    Game().run()