import pygame
import sys
from config import load_image, load_images
from src.maze import Maze
from src.enemy import Enemy  # Import Enemy từ src/enemy.py
import math

RENDER_SCALE = 3
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Maze-Game with Enemies")
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
            self.tilemap.load('maps/map1.json')
        except FileNotFoundError:
            pass

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        self.tile_scale = (17, 12)
        self.scale = self.tile_scale
        self.scroll = [0, 0]

        # Chuyển tilemap thành mê cung lưới
        self.maze_width, self.maze_height = 17, 12
        self.cell_size = self.tilemap.tile_size[0]  # Giả định tile_size[0] = tile_size[1]
        self.maze = self.convert_tilemap_to_maze()

        # Thêm người chơi
        self.PLAYER_SIZE = 10
        # Tìm vị trí ban đầu hợp lệ (ô đường đi)
        self.player_pos = self.find_initial_player_position()
        self.player_rect = pygame.Rect(
            self.player_pos[1] * self.cell_size + (self.cell_size - self.PLAYER_SIZE) // 2,
            self.player_pos[0] * self.cell_size + (self.cell_size - self.PLAYER_SIZE) // 2,
            self.PLAYER_SIZE, self.PLAYER_SIZE
        )
        self.player_target_pos = None
        self.player_speed = 60
        self.player_last_move = 0
        self.player_move_delay = 100

        # Thêm quái vật (bao gồm zombie)
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
            else:
                print(f"Warning: Tile at ({x}, {y}) is out of bounds for maze size ({self.maze_width}, {self.maze_height})")
        return maze

    def find_initial_player_position(self):
        """Tìm vị trí ban đầu hợp lệ cho người chơi (ô đường đi)"""
        # Thử vị trí [1, 1] trước
        if self.maze[1][1] == 0:
            return [1, 1]
        # Nếu không, tìm ô đường đi gần nhất
        for y in range(self.maze_height):
            for x in range(self.maze_width):
                if self.maze[y][x] == 0:
                    return [y, x]
        # Nếu không tìm thấy ô đường đi, trả về [1, 1] và in cảnh báo
        print("Warning: No valid starting position found for player. Using [1, 1].")
        return [1, 1]

    def find_nearest_valid_position(self, current_x, current_y):
        """Tìm ô đường đi gần nhất từ vị trí hiện tại"""
        current_grid_x = int(current_x // self.cell_size)
        current_grid_y = int(current_y // self.cell_size)
        queue = [(current_grid_y, current_grid_x)]
        visited = set()
        visited.add((current_grid_y, current_grid_x))
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while queue:
            y, x = queue.pop(0)
            if (0 <= y < self.maze_height and 0 <= x < self.maze_width and
                    self.maze[y][x] == 0):
                return [y, x]
            for dy, dx in directions:
                next_y, next_x = y + dy, x + dx
                if (0 <= next_y < self.maze_height and 0 <= next_x < self.maze_width and
                        (next_y, next_x) not in visited):
                    queue.append((next_y, next_x))
                    visited.add((next_y, next_x))
        # Nếu không tìm thấy ô hợp lệ, trả về vị trí hiện tại
        return [current_grid_y, current_grid_x]

    def run(self):
        while True: 
            

            
            
            self.display.fill((132, 94, 60))

            # Cập nhật scroll
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # Cập nhật self.player_pos dựa trên self.player_rect
            current_grid_x = int(self.player_rect.x // self.cell_size)
            current_grid_y = int(self.player_rect.y // self.cell_size)
            self.player_pos = [current_grid_y, current_grid_x]

            # Kiểm tra ô hiện tại của người chơi
            if (0 <= current_grid_y < self.maze_height and 0 <= current_grid_x < self.maze_width and
                    self.maze[current_grid_y][current_grid_x] == 1):
                # Nếu ô hiện tại là tường, tìm ô đường đi gần nhất và di chuyển đến đó
                new_pos = self.find_nearest_valid_position(self.player_rect.x, self.player_rect.y)
                self.player_rect.x = new_pos[1] * self.cell_size + (self.cell_size - self.PLAYER_SIZE) // 2
                self.player_rect.y = new_pos[0] * self.cell_size + (self.cell_size - self.PLAYER_SIZE) // 2
                self.player_pos = new_pos
                self.player_target_pos = None  # Hủy di chuyển

            # Xử lý di chuyển người chơi
            if self.player_target_pos:
                target_grid_x = int(self.player_target_pos[0] // self.cell_size)
                target_grid_y = int(self.player_target_pos[1] // self.cell_size)
                # Kiểm tra xem ô đích có phải là đường đi không
                if (0 <= target_grid_y < self.maze_height and 0 <= target_grid_x < self.maze_width and
                        self.maze[target_grid_y][target_grid_x] == 0):
                    dx = self.player_target_pos[0] - self.player_rect.x
                    dy = self.player_target_pos[1] - self.player_rect.y
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance > 1:
                        speed_per_frame = self.player_speed / 60
                        if distance <= speed_per_frame:
                            self.player_rect.x = self.player_target_pos[0]
                            self.player_rect.y = self.player_target_pos[1]
                            self.player_pos = [target_grid_y, target_grid_x]
                            self.player_target_pos = None
                        else:
                            direction_x = dx / distance
                            direction_y = dy / distance
                            new_x = self.player_rect.x + direction_x * speed_per_frame
                            new_y = self.player_rect.y + direction_y * speed_per_frame
                            new_grid_x = int(new_x // self.cell_size)
                            new_grid_y = int(new_y // self.cell_size)
                            if (0 <= new_grid_y < self.maze_height and 0 <= new_grid_x < self.maze_width and
                                    self.maze[new_grid_y][new_grid_x] == 0):
                                self.player_rect.x = new_x
                                self.player_rect.y = new_y
                                self.player_pos = [new_grid_y, new_grid_x]
                            else:
                                self.player_target_pos = None
                    else:
                        self.player_rect.x = self.player_target_pos[0]
                        self.player_rect.y = self.player_target_pos[1]
                        self.player_pos = [target_grid_y, target_grid_x]
                        self.player_target_pos = None
                else:
                    self.player_target_pos = None

            current_time = pygame.time.get_ticks()
            if self.player_target_pos is None and current_time - self.player_last_move >= self.player_move_delay:
                keys = pygame.key.get_pressed()
                new_x, new_y = self.player_pos[1], self.player_pos[0]
                if keys[pygame.K_LEFT] and 0 <= new_x - 1 < self.maze_width and self.maze[new_y][new_x - 1] == 0:
                    new_x -= 1
                if keys[pygame.K_RIGHT] and 0 <= new_x + 1 < self.maze_width and self.maze[new_y][new_x + 1] == 0:
                    new_x += 1
                if keys[pygame.K_UP] and 0 <= new_y - 1 < self.maze_height and self.maze[new_y - 1][new_x] == 0:
                    new_y -= 1
                if keys[pygame.K_DOWN] and 0 <= new_y + 1 < self.maze_height and self.maze[new_y + 1][new_x] == 0:
                    new_y += 1

                if [new_y, new_x] != self.player_pos:
                    self.player_pos = [new_y, new_x]
                    self.player_target_pos = (
                        self.player_pos[1] * self.cell_size + (self.cell_size - self.PLAYER_SIZE) // 2,
                        self.player_pos[0] * self.cell_size + (self.cell_size - self.PLAYER_SIZE) // 2
                    )
                    self.player_last_move = current_time

            # # Cập nhật quái vật
            maze_changed = False
            for enemy in self.enemies:
                enemy.move(self.player_pos, self.player_rect)

            # Xử lý chỉnh sửa tilemap
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

                self.maze = self.convert_tilemap_to_maze()
                maze_changed = True

            if maze_changed:
                for enemy in self.enemies:
                    enemy.on_maze_changed()

            # # Xử lý sự kiện
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()



            # # Render mê cung
            self.tilemap.render(self.display, render_scroll)

            # # Vẽ người chơi
            pygame.draw.rect(self.display, (255, 0, 0),
                            (self.player_rect.x - render_scroll[0],
                             self.player_rect.y - render_scroll[1],
                             self.PLAYER_SIZE, self.PLAYER_SIZE))

            # # Vẽ quái vật
            for enemy in self.enemies:
                enemy.draw(self.display, render_scroll)


            # Cập nhật màn hình
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)
