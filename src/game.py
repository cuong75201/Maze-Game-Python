import pygame
from maze import Maze
from bullet import Bullet
from enemy import Enemy
from player import Player
import random
import math
import sys
import os

pygame.init()
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Shooter Game")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Xác định đường dẫn cơ sở dựa trên vị trí file game.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "..", "assets", "images")

try:
    player_icon = pygame.image.load(os.path.join(
        ASSETS_DIR, "hero", "walkA", "hero_walkA_0000.png"))
    player_icon = pygame.transform.scale(player_icon, (50, 50))
except pygame.error:
    player_icon = pygame.Surface((50, 50))
    player_icon.fill(WHITE)

try:
    bullet_icon = pygame.image.load(
        os.path.join(ASSETS_DIR, "bullet", "bullet.png"))
    bullet_icon = pygame.transform.scale(bullet_icon, (30, 35))
except pygame.error:
    bullet_icon = pygame.Surface((30, 35))
    bullet_icon.fill((255, 255, 0))

# Thêm hình ảnh cho hộp đạn
try:
    ammo_box_image = pygame.image.load(
        os.path.join(ASSETS_DIR, "bullet", "ammo_box.png"))
    ammo_box_image = pygame.transform.scale(
        ammo_box_image, (30, 35))  # Kích thước tương tự bullet_icon
except pygame.error as e:
    print(f"Không thể tải ammo_box.png: {e}")
    ammo_box_image = pygame.Surface((30, 35))
    ammo_box_image.fill((0, 255, 0))  # Màu xanh lá nếu không tìm thấy file

ICON_X, ICON_Y = 10, HEIGHT - 100
AMMO_ICON_X, AMMO_ICON_Y = ICON_X, ICON_Y + 50  # Vị trí hình hộp đạn
AMMO_TEXT_X, AMMO_TEXT_Y = AMMO_ICON_X + 40, AMMO_ICON_Y + 5  # Vị trí văn bản số đạn
# Vị trí văn bản HP (bên cạnh icon nhân vật)
HP_TEXT_X, HP_TEXT_Y = ICON_X + 51, ICON_Y + 15

font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()
FPS = 60
 
TILE_SIZE = (17, 12)

game_assets = {
    "WallStone": [
        pygame.transform.scale(pygame.image.load(os.path.join(
            ASSETS_DIR, "level", "WallStone", "wallStone.png")), TILE_SIZE),
        pygame.transform.scale(pygame.image.load(os.path.join(
            ASSETS_DIR, "level", "WallStone", "wallStone_fence.png")), TILE_SIZE)
    ],
    "WallBreakable": [
        pygame.transform.scale(pygame.image.load(os.path.join(
            ASSETS_DIR, "level", "WallBreakable", "wallBreakable.png")), TILE_SIZE),
        pygame.transform.scale(pygame.image.load(os.path.join(
            ASSETS_DIR, "level", "WallBreakable", "wallBreakable_small.png")), TILE_SIZE)
    ],
    "Earth": [
        pygame.transform.scale(pygame.image.load(os.path.join(
            ASSETS_DIR, "level", "Earth", "groundEarth_checkered.png")), TILE_SIZE),
        pygame.transform.scale(pygame.image.load(os.path.join(
            ASSETS_DIR, "level", "Earth", "groundExit.png")), TILE_SIZE)
    ]
}

maze = Maze(game={"assets": game_assets}, tile_size=TILE_SIZE)
maze.load("maps/map1.json")


class AmmoBox:
    def __init__(self, x, y):
        # Kích thước nhỏ hơn khi spawn trên bản đồ
        self.image = pygame.transform.scale(ammo_box_image, (20, 20))
        self.rect = self.image.get_rect(center=(x, y))
        self.ammo_amount = 15

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))


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
            grid_x = pixel_x // tile_size[0]
            grid_y = pixel_y // tile_size[1]
            if (1 <= grid_x < maze_width - 1 and 1 <= grid_y < maze_height - 1):
                valid_positions.append((pixel_x, pixel_y))

    if not valid_positions:
        raise ValueError("Không tìm thấy ô 'Earth' nào trong mê cung!")

    valid_positions.sort(key=lambda pos: (pos[0], pos[1]))
    temp_rect = pygame.Rect(0, 0, size[0], size[1])
    max_attempts = 100
    attempts = 0
    min_distance = initial_min_distance

    while attempts < max_attempts:
        pixel_x, pixel_y = random.choice(valid_positions)
        if not is_position_valid(maze, pixel_x, pixel_y, temp_rect):
            attempts += 1
            continue

        grid_x = pixel_x // tile_size[0]
        grid_y = pixel_y // tile_size[1]

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
        if attempts == 50 and min_distance > 1:
            min_distance -= 1
            attempts = 0
            print(f"Giảm min_distance xuống {min_distance} để tìm vị trí spawn")

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
        maze_width=0,
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
occupied_positions = []

enemy_list = ["slime", "slime", "slime", "slime", "skeleton", "skeleton", "zombie", "zombie", "ghost", "ghost", "giant"]

for enemy_type in enemy_list:
    try:
        enemy_size = Enemy.ENEMY_TYPES[enemy_type]["size"]
        enemy_x, enemy_y = find_valid_starting_position(
            maze,
            size=enemy_size,
            occupied_positions=occupied_positions,
            maze_width=maze_width,
            maze_height=maze_height,
            initial_min_distance=5
        )
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

ammo_boxes = []
MAX_AMMO_BOXES = 20
AMMO_BOX_SPAWN_CHANCE = 0.01
PLAYER_MAX_BULLETS = 150

running = True
while running:
    dt = clock.tick(FPS) / 1000  # Tính dt (thời gian giữa các frame, tính bằng giây)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    player.move(keys)
    if keys[pygame.K_SPACE]:
        player.shoot()

    player.update_bullets()

    player_grid_x = player.rect.centerx // TILE_SIZE[0]
    player_grid_y = player.rect.centery // TILE_SIZE[1]
    player_pos = (player_grid_y, player_grid_x)

    if len(ammo_boxes) < MAX_AMMO_BOXES and random.random() < AMMO_BOX_SPAWN_CHANCE:
        try:
            ammo_x, ammo_y = find_valid_starting_position(
                maze,
                size=(20, 20),
                occupied_positions=[(player.rect.centerx, player.rect.centery)] + [
                    (e.rect.centerx, e.rect.centery) for e in enemies],
                maze_width=maze_width,
                maze_height=maze_height,
                initial_min_distance=5
            )
            ammo_boxes.append(AmmoBox(ammo_x, ammo_y))
            print(f"Đã spawn hộp đạn tại ({ammo_x}, {ammo_y})")
        except ValueError as e:
            print(f"Không thể spawn hộp đạn: {e}")

    for ammo_box in ammo_boxes[:]:
        if player.rect.colliderect(ammo_box.rect):
            if player.bullets < PLAYER_MAX_BULLETS:
                ammo_to_add = min(ammo_box.ammo_amount, PLAYER_MAX_BULLETS - player.bullets)
                player.bullets += ammo_to_add
                print(f"Nhặt hộp đạn, cộng {ammo_to_add} đạn. Tổng đạn: {player.bullets}")
            ammo_boxes.remove(ammo_box)

    for enemy in enemies[:]:
        enemy.move(player_pos, player.rect, dt)  # Truyền dt vào move

        # Kiểm tra va chạm giữa quái vật và người chơi
        if enemy.is_visible and enemy.rect.colliderect(player.rect):
            player.health -= 50  # Trừ nửa cây máu (50 HP) khi quái vật chạm
            if player.health <= 0:
                running = False
                print("Người chơi đã bị hạ gục!")
            # Tạm dừng ngắn để tránh trừ máu liên tục
            enemy.rect.x += (enemy.rect.centerx - player.rect.centerx) * 0.1
            enemy.rect.y += (enemy.rect.centery - player.rect.centery) * 0.1

        for bullet in player.bullet_list[:]:
            if enemy.is_visible and bullet.rect.colliderect(enemy.rect):
                enemy.hp -= bullet.damage
                enemy.create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 255, 0))
                player.bullet_list.remove(bullet)
                if enemy.hp <= 0:
                    enemies.remove(enemy)
                    enemy.create_particles(enemy.rect.centerx, enemy.rect.centery, (255, 0, 0))
                break

        if hasattr(enemy, 'projectiles'):
            for projectile in enemy.projectiles[:]:
                if projectile["rect"].colliderect(player.rect):
                    # Trừ nửa cây máu nếu trúng kiếm (skeleton) hoặc ma thuật (ghost)
                    if enemy.enemy_type in ["skeleton", "ghost"]:
                        player.health -= 50
                    else:
                        player.health -= 5  # Các loại đạn khác (nếu có)
                    enemy.projectiles.remove(projectile)
                    if player.health <= 0:
                        running = False
                        print("Người chơi đã bị hạ gục bởi đạn quái vật!")
                    break

    # Tính kích thước pixel của bản đồ
    map_width = maze_width * TILE_SIZE[0]
    map_height = maze_height * TILE_SIZE[1]

    # Tính offset của camera với giới hạn trên và dưới
    camera_offset_x = player.rect.centerx - WIDTH // 2
    camera_offset_y = player.rect.centery - HEIGHT // 2

    # Giới hạn offset để không vượt ra ngoài bản đồ
    camera_offset_x = max(0, min(camera_offset_x, map_width - WIDTH))
    camera_offset_y = max(0, min(camera_offset_y, map_height - HEIGHT))

    offset = (camera_offset_x, camera_offset_y)

    screen.fill(WHITE)
    maze.render(screen, offset=offset)
    screen.blit(player_icon, (ICON_X, ICON_Y))

    # Hiển thị HP bên cạnh icon nhân vật
    hp_text = font.render(f"{int(player.health)}/100", True, BLACK)
    screen.blit(hp_text, (HP_TEXT_X, HP_TEXT_Y))

    # Hiển thị số đạn với hình hộp đạn
    screen.blit(ammo_box_image, (AMMO_ICON_X, AMMO_ICON_Y))
    ammo_text = font.render(f": {player.bullets}/{PLAYER_MAX_BULLETS}", True, BLACK)
    screen.blit(ammo_text, (AMMO_TEXT_X, AMMO_TEXT_Y))

    player.draw(screen, offset=offset)
    for enemy in enemies:
        enemy.draw(screen, offset=offset)
    for ammo_box in ammo_boxes:
        ammo_box.draw(screen, offset=offset)

    pygame.display.flip()

pygame.quit()