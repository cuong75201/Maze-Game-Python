import pygame
from maze import Maze
from bullet import Bullet
from enemy import Enemy
import random
import math
import sys

pygame.init()
WIDTH, HEIGHT = 1000, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Shooter Game")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

try:
    player_icon = pygame.image.load("assets/images/hero/walkA/hero_walkA_0000.png")
    player_icon = pygame.transform.scale(player_icon, (50, 50))
except pygame.error:
    player_icon = pygame.Surface((50, 50))
    player_icon.fill(WHITE)

try:
    bullet_icon = pygame.image.load("assets/images/bullet/bullet.png")
    bullet_icon = pygame.transform.scale(bullet_icon, (30, 35))
except pygame.error:
    bullet_icon = pygame.Surface((30, 35))
    bullet_icon.fill((255, 255, 0))

ICON_X, ICON_Y = 10, HEIGHT - 100
BULLET_ICON_X, BULLET_ICON_Y = ICON_X, ICON_Y + 50
AMMO_TEXT_X, AMMO_TEXT_Y = BULLET_ICON_X + 40, BULLET_ICON_Y + 5

font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()
FPS = 60

TILE_SIZE = (17, 12)

game_assets = {
    "WallStone": [
        pygame.transform.scale(pygame.image.load("assets/images/level/WallStone/wallStone.png"), TILE_SIZE),
        pygame.transform.scale(pygame.image.load("assets/images/level/WallStone/wallStone_fence.png"), TILE_SIZE)
    ],
    "WallBreakable": [
        pygame.transform.scale(pygame.image.load("assets/images/level/WallBreakable/wallBreakable.png"), TILE_SIZE),
        pygame.transform.scale(pygame.image.load("assets/images/level/WallBreakable/wallBreakable_small.png"), TILE_SIZE)
    ],
    "Earth": [
        pygame.transform.scale(pygame.image.load("assets/images/level/Earth/groundEarth_checkered.png"), TILE_SIZE),
        pygame.transform.scale(pygame.image.load("assets/images/level/Earth/groundExit.png"), TILE_SIZE)
    ]
}

maze = Maze(game={"assets": game_assets}, tile_size=TILE_SIZE)
maze.load("map1.json")

class Player:
    def __init__(self, x, y, maze=None, image_path=None):
        print(f"Khởi tạo Player tại vị trí ({x}, {y})")
        
        self.maze = maze

        self.walk_frames = {
            "right": [],
            "left": [],
            "up": [],
            "down": []
        }
        self.load_walk_frames()

        self.image = self.walk_frames["right"][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
        self.bullets = 50
        self.bullet_list = []
        self.shoot_cooldown = 0
        self.direction = "right"
        self.frame_index = 0
        self.animation_speed = 0.2
        self.is_moving = False

        self.is_rolling = False
        self.roll_distance = 50
        self.roll_speed = 3.3
        self.roll_cooldown = 0
        self.roll_cooldown_max = 30
        self.roll_distance_moved = 0

        self.health = 100
        self.max_health = 100
        self.health_bar_width = 40
        self.health_bar_height = 8
        self.health_bar_offset = 10

    def load_walk_frames(self):
        tile_width, tile_height = self.maze.tile_size
        for i in range(16):
            walkA_path = f"assets/images/hero/walkA/hero_walkA_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkA_path)
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["down"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkA_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["down"].append(frame)

            walkB_path = f"assets/images/hero/walkB/hero_walkB_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkB_path)
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["right"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkB_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["right"].append(frame)

            walkC_path = f"assets/images/hero/walkC/hero_walkC_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkC_path)
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["up"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkC_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["up"].append(frame)

            walkD_path = f"assets/images/hero/walkD/hero_walkD_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkD_path)
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["left"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkD_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["left"].append(frame)

    def move(self, keys):
        if self.roll_cooldown > 0:
            self.roll_cooldown -= 1

        if keys[pygame.K_b] and not self.is_rolling and self.roll_cooldown == 0:
            self.is_rolling = True
            self.roll_distance_moved = 0
            self.roll_cooldown = self.roll_cooldown_max

        if self.is_rolling:
            self._roll()
            return

        moved = False
        new_rect = self.rect.copy()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            new_rect.y -= self.speed
            self.direction = "up"
            moved = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            new_rect.y += self.speed
            self.direction = "down"
            moved = True
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            new_rect.x -= self.speed
            self.direction = "left"
            moved = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            new_rect.x += self.speed
            self.direction = "right"
            moved = True

        if moved and self.maze:
            player_tile_x = new_rect.centerx // self.maze.tile_size[0]
            player_tile_y = new_rect.centery // self.maze.tile_size[1]
            tile_key = f"{player_tile_x};{player_tile_y}"
            if tile_key in self.maze.tilemap:
                tile = self.maze.tilemap[tile_key]
                if tile['type'] in ["WallStone", "WallBreakable"]:
                    tile_rect = pygame.Rect(
                        tile['pos'][0] * self.maze.tile_size[0],
                        tile['pos'][1] * self.maze.tile_size[1],
                        self.maze.tile_size[0],
                        tile.get('scale', self.maze.tile_size)[1]
                    )
                    if new_rect.colliderect(tile_rect):
                        moved = False

        if moved:
            self.rect = new_rect

        self.is_moving = moved
        if moved:
            self._update_image()

    def _roll(self):
        new_rect = self.rect.copy()
        if self.direction == "up":
            new_rect.y -= self.roll_speed
        elif self.direction == "down":
            new_rect.y += self.roll_speed
        elif self.direction == "left":
            new_rect.x -= self.roll_speed
        elif self.direction == "right":
            new_rect.x += self.roll_speed

        can_roll = True
        if self.maze:
            player_tile_x = new_rect.centerx // self.maze.tile_size[0]
            player_tile_y = new_rect.centery // self.maze.tile_size[1]
            tile_key = f"{player_tile_x};{player_tile_y}"
            if tile_key in self.maze.tilemap:
                tile = self.maze.tilemap[tile_key]
                if tile['type'] in ["WallStone", "WallBreakable"]:
                    tile_rect = pygame.Rect(
                        tile['pos'][0] * self.maze.tile_size[0],
                        tile['pos'][1] * self.maze.tile_size[1],
                        self.maze.tile_size[0],
                        tile.get('scale', self.maze.tile_size)[1]
                    )
                    if new_rect.colliderect(tile_rect):
                        can_roll = False

        if can_roll:
            self.rect = new_rect

        self.roll_distance_moved += self.roll_speed

        if self.roll_distance_moved >= self.roll_distance:
            self.is_rolling = False
            self.roll_distance_moved = 0

        self._update_image()

    def _update_image(self):
        current_animation_speed = self.animation_speed * 2 if self.is_rolling else self.animation_speed

        if self.is_moving or self.is_rolling:
            self.frame_index += current_animation_speed
            if self.frame_index >= len(self.walk_frames[self.direction]):
                self.frame_index = 0
            self.image = self.walk_frames[self.direction][int(self.frame_index)]
        else:
            self.frame_index = 0
            self.image = self.walk_frames[self.direction][0]

        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def shoot(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            return
        if self.bullets > 0:
            bullet = Bullet(
                self.rect.centerx,
                self.rect.centery,
                image_path="assets/images/bullet/bullet.png",
                direction=self.direction,
                maze=self.maze
            )
            self.bullet_list.append(bullet)
            self.bullets -= 1
            self.shoot_cooldown = 5

    def update_bullets(self):
        for bullet in self.bullet_list[:]:
            bullet.move()
            if bullet.should_remove():
                self.bullet_list.remove(bullet)

    def collect_ammo(self, amount):
        self.bullets += amount
        print(f"Nhặt thêm {amount} đạn. Tổng đạn: {self.bullets}")

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))

        if not self.is_rolling:
            health_ratio = self.health / self.max_health
            current_width = self.health_bar_width * health_ratio
            health_bar_x = self.rect.centerx - self.health_bar_width // 2 - offset[0]
            health_bar_y = self.rect.top - self.health_bar_offset - offset[1]
            pygame.draw.rect(screen, (255, 0, 0), (health_bar_x, health_bar_y, current_width, self.health_bar_height))

        for bullet in self.bullet_list:
            bullet.draw(screen, offset=offset)

def is_position_valid(maze, x, y, rect):
    rect.center = (x, y)
    for loc in maze.tilemap:
        tile = maze.tilemap[loc]
        if tile['type'] in ["WallStone", "WallBreakable"]:
            tile_rect = pygame.Rect(
                tile['pos'][0] * maze.tile_size[0],
                tile['pos'][1] * maze.tile_size[1],
                maze.tile_size[0],
                tile.get('scale', maze.tile_size)[1]
            )
            if rect.colliderect(tile_rect):
                return False
    return True

def find_valid_starting_position(maze, size, occupied_positions, maze_width, maze_height, initial_min_distance=5):
    tile_size = maze.tile_size
    valid_positions = []
    for loc in maze.tilemap:
        tile = maze.tilemap[loc]
        if tile['type'] == "Earth":
            pos_x, pos_y = tile['pos']
            pixel_x = pos_x * tile_size[0] + tile_size[0] // 2
            pixel_y = pos_y * tile_size[1] + tile_size[1] // 2
            # Kiểm tra xem vị trí có nằm trong biên mê cung và cách biên ít nhất 1 ô
            grid_x = pixel_x // tile_size[0]
            grid_y = pixel_y // tile_size[1]
            if (1 <= grid_x < maze_width - 1 and 1 <= grid_y < maze_height - 1):
                valid_positions.append((pixel_x, pixel_y))

    if not valid_positions:
        raise ValueError("Không tìm thấy ô 'Earth' nào trong mê cung!")

    valid_positions.sort(key=lambda pos: (pos[0], pos[1]))
    temp_rect = pygame.Rect(0, 0, size[0], size[1])
    max_attempts = 100  # Giới hạn số lần thử
    attempts = 0
    min_distance = initial_min_distance  # Bắt đầu với khoảng cách tối thiểu mong muốn

    while attempts < max_attempts:
        # Lấy ngẫu nhiên một vị trí từ danh sách
        pixel_x, pixel_y = random.choice(valid_positions)
        if not is_position_valid(maze, pixel_x, pixel_y, temp_rect):
            attempts += 1
            continue

        # Chuyển vị trí pixel thành tọa độ lưới để kiểm tra khoảng cách
        grid_x = pixel_x // tile_size[0]
        grid_y = pixel_y // tile_size[1]

        # Kiểm tra khoảng cách với các vị trí đã spawn
        too_close = False
        for occ_x, occ_y in occupied_positions:
            occ_grid_x = occ_x // tile_size[0]
            occ_grid_y = occ_y // tile_size[1]
            distance = math.sqrt((grid_x - occ_grid_x) ** 2 + (grid_y - occ_grid_y) ** 2)
            if distance < min_distance:
                too_close = True
                break

        if not too_close:
            return pixel_x, pixel_y

        attempts += 1
        # Nếu không tìm được vị trí sau 50 lần thử, giảm min_distance
        if attempts == 50 and min_distance > 1:
            min_distance -= 1
            attempts = 0  # Reset số lần thử để thử lại với min_distance mới
            print(f"Giảm min_distance xuống {min_distance} để tìm vị trí spawn")

    # Nếu không tìm được vị trí phù hợp, trả về vị trí đầu tiên hợp lệ (không kiểm tra khoảng cách)
    for pixel_x, pixel_y in valid_positions:
        if is_position_valid(maze, pixel_x, pixel_y, temp_rect):
            print(f"Không thể tìm vị trí với min_distance, sử dụng vị trí hợp lệ tại ({pixel_x}, {pixel_y})")
            return pixel_x, pixel_y

    raise ValueError("Không tìm thấy vị trí hợp lệ nào để đặt nhân vật!")

try:
    player_x, player_y = find_valid_starting_position(
        maze,
        size=(TILE_SIZE[0], TILE_SIZE[1]),
        occupied_positions=[],
        maze_width=0,  # Không cần kiểm tra biên cho người chơi
        maze_height=0
    )
except ValueError as e:
    print(e)
    player_x, player_y = maze.tile_size[0] * 1.5, maze.tile_size[1] * 1.5

player = Player(player_x, player_y, maze=maze)

def convert_tilemap_to_maze(maze):
    maze_width = max([int(loc.split(';')[0]) for loc in maze.tilemap.keys()]) + 1
    maze_height = max([int(loc.split(';')[1]) for loc in maze.tilemap.keys()]) + 1
    grid = [[1 for _ in range(maze_width)] for _ in range(maze_height)]
    for loc, tile in maze.tilemap.items():
        x, y = map(int, loc.split(';'))
        if 0 <= x < maze_width and 0 <= y < maze_height:
            if tile['type'] == 'Earth':
                grid[y][x] = 0
            else:
                grid[y][x] = 1
    return grid, maze_width, maze_height

maze_grid, maze_width, maze_height = convert_tilemap_to_maze(maze)

enemies = []
occupied_positions = []  # Danh sách các vị trí đã được sử dụng

# Danh sách các quái vật: 4 Slime, 2 Skeleton, 2 Zombie, 2 Ghost, 1 Giant
enemy_list = ["slime", "slime", "slime", "slime", "skeleton", "skeleton", "zombie", "zombie", "ghost", "ghost", "giant"]

for enemy_type in enemy_list:
    try:
        enemy_size = Enemy.ENEMY_TYPES[enemy_type]["size"]
        # Tìm vị trí spawn, truyền vào danh sách các vị trí đã chiếm
        enemy_x, enemy_y = find_valid_starting_position(
            maze,
            size=enemy_size,
            occupied_positions=occupied_positions,
            maze_width=maze_width,
            maze_height=maze_height,
            initial_min_distance=5  # Khoảng cách tối thiểu ban đầu
        )
        # Thêm vị trí vừa tìm được vào danh sách occupied_positions
        occupied_positions.append((enemy_x, enemy_y))
        enemy = Enemy(
            x=enemy_x // TILE_SIZE[0],
            y=enemy_y // TILE_SIZE[1],
            cell_size=TILE_SIZE[0],
            maze_width=maze_width,
            maze_height=maze_height,
            maze=maze_grid,
            enemy_type=enemy_type
        )
        enemies.append(enemy)
        print(f"Đã đặt {enemy_type} tại vị trí ({enemy_x}, {enemy_y})")
    except ValueError as e:
        print(f"Không thể đặt {enemy_type}: {e}")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.move(keys)
    if keys[pygame.K_SPACE]:
        player.shoot()

    player.update_bullets()

    # Tính tọa độ lưới của người chơi
    player_grid_x = player.rect.centerx // TILE_SIZE[0]
    player_grid_y = player.rect.centery // TILE_SIZE[1]
    player_pos = (player_grid_y, player_grid_x)

    for enemy in enemies[:]:
        enemy.move(player_pos, player.rect)

        for bullet in player.bullet_list[:]:
            if enemy.is_visible and bullet.rect.colliderect(enemy.rect):
                enemy.hp -= 10
                player.bullet_list.remove(bullet)
                if enemy.hp <= 0:
                    enemies.remove(enemy)
                break

        if hasattr(enemy, 'projectiles'):
            for projectile in enemy.projectiles[:]:
                if projectile["rect"].colliderect(player.rect):
                    player.health -= 5
                    enemy.projectiles.remove(projectile)
                    if player.health <= 0:
                        running = False
                    break

    camera_offset_x = max(0, player.rect.centerx - WIDTH // 2)
    camera_offset_y = max(0, player.rect.centery - HEIGHT // 2)
    offset = (camera_offset_x, camera_offset_y)

    screen.fill(WHITE)
    maze.render(screen, offset=offset)
    screen.blit(player_icon, (ICON_X, ICON_Y))
    screen.blit(bullet_icon, (BULLET_ICON_X, BULLET_ICON_Y))
    ammo_text = font.render(f": {player.bullets}", True, BLACK)
    screen.blit(ammo_text, (AMMO_TEXT_X, AMMO_TEXT_Y))
    player.draw(screen, offset=offset)
    for enemy in enemies:
        enemy.draw(screen, offset=offset)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()