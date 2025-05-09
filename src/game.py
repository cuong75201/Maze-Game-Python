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

# Thêm biến đường dẫn ảnh chúc mừng
CONGRATS_BG_PATH = os.path.join(ASSETS_DIR, "congratulations.png")  # Đặt tên file phù hợp với ảnh bạn lưu
try:
    congrats_bg = pygame.image.load(CONGRATS_BG_PATH)
    congrats_bg = pygame.transform.scale(congrats_bg, (WIDTH, HEIGHT))
except Exception:
    congrats_bg = None

# Load win animation frames cho phần kết thúc
WIN_ANIMATION_FRAMES = []
for i in range(17):
    frame_path = os.path.join(ASSETS_DIR, "hero", "winA", f"hero_winA_{i:04d}.png")
    try:
        frame = pygame.image.load(frame_path).convert_alpha()
        WIN_ANIMATION_FRAMES.append(frame)
    except Exception:
        pass

# Load các frame của GIF Game Over (Hungry Game Over GIF by Ocean Park)
GAME_OVER_GIF_FRAMES = []
try:
    import glob
    gif_dir = os.path.join(ASSETS_DIR, "gameover_gif")  # Thư mục chứa các frame đã tách từ gif
    gif_frame_paths = sorted(glob.glob(os.path.join(gif_dir, "*.png")))
    for path in gif_frame_paths:
        frame = pygame.image.load(path).convert_alpha()
        GAME_OVER_GIF_FRAMES.append(frame)
except Exception:
    pass

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

enemy_list = ["slime", "slime", "slime", "slime", "skeleton", "skeleton", "skeleton", "zombie", "zombie", "zombie", "zombie", "ghost", "ghost", "ghost", "giant", "giant", "giant"]

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

# Thêm class hiển thị thông báo kết thúc
class EndGameMessage:
    def __init__(self, text, font, color=BLACK):
        self.text = text
        self.font = font
        self.color = color
        self.surface = self.font.render(self.text, True, self.color)
        self.rect = self.surface.get_rect(center=(WIDTH // 2 + WIDTH // 4, HEIGHT // 2))

    def draw(self, screen):
        screen.blit(self.surface, self.rect)

# Thêm biến lưu thời gian bắt đầu và số quái vật bị hạ
start_ticks = pygame.time.get_ticks()
kills = 0

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

    # Kiểm tra nếu player chạm vào ô groundExit
    tile_key = f"{player_grid_x};{player_grid_y}"
    if tile_key in maze.tilemap:
        tile = maze.tilemap[tile_key]
        # Kiểm tra nếu là groundExit (ô Earth thứ 2 trong assets)
        if tile['type'] == 'Earth' and tile.get('variant', 0) == 1:
            # Fade in hiệu ứng kết thúc (lâu hơn và nhân vật lớn hơn, dùng animation win)
            fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for alpha in range(0, 256, 4):
                if congrats_bg:
                    temp_bg = congrats_bg.copy()
                    temp_bg.set_alpha(alpha)
                    screen.blit(temp_bg, (0, 0))
                else:
                    fade_surface.fill((255, 255, 255, alpha))
                    screen.blit(fade_surface, (0, 0))
                # Animation nhân vật chiến thắng
                frame_idx = (alpha // 8) % len(WIN_ANIMATION_FRAMES) if WIN_ANIMATION_FRAMES else 0
                if WIN_ANIMATION_FRAMES:
                    win_frame = pygame.transform.scale(WIN_ANIMATION_FRAMES[frame_idx], (180, 180))
                    win_frame.set_alpha(alpha)
                    player_img_rect = win_frame.get_rect()
                    player_img_rect.center = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2)
                    screen.blit(win_frame, player_img_rect)
                # Dòng chữ tiếng Anh bên dưới
                end_message = EndGameMessage("Congratulations! You Win!", font)
                end_message.surface.set_alpha(alpha)
                end_message.rect.midtop = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 100)
                end_message.draw(screen)
                pygame.display.flip()
                pygame.time.delay(30)
            # Hiển thị màn hình kết thúc với animation cho đến khi người chơi nhấn phím hoặc đóng cửa sổ
            waiting = True
            anim_idx = 0
            # Tính thời gian chơi
            play_time = (pygame.time.get_ticks() - start_ticks) // 1000
            minutes = play_time // 60
            seconds = play_time % 60
            # Chuẩn bị các thông tin
            info_texts = [
                f"Time: {minutes:02d}:{seconds:02d}",
                f"Enemies Defeated: {kills}"
            ]
            info_surfaces = [font.render(text, True, (0,0,0)) for text in info_texts]
            info_rects = [surf.get_rect(midtop=(WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 150 + i*50)) for i, surf in enumerate(info_surfaces)]
            # Hiệu ứng xuất hiện từng dòng thông tin
            for idx, (surf, rect) in enumerate(zip(info_surfaces, info_rects)):
                for alpha in range(0, 256, 16):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            waiting = False
                            running = False
                            break
                    if congrats_bg:
                        screen.blit(congrats_bg, (0, 0))
                    else:
                        screen.fill(WHITE)
                    # Animation nhân vật chiến thắng (lặp)
                    if WIN_ANIMATION_FRAMES:
                        win_frame = pygame.transform.scale(WIN_ANIMATION_FRAMES[anim_idx % len(WIN_ANIMATION_FRAMES)], (180, 180))
                        win_frame.set_alpha(255)
                        player_img_rect = win_frame.get_rect()
                        player_img_rect.center = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2)
                        screen.blit(win_frame, player_img_rect)
                    # Dòng chữ chúc mừng
                    end_message.surface.set_alpha(255)
                    end_message.rect.midtop = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 100)
                    end_message.draw(screen)
                    # Dòng thông tin hiện tại
                    temp_surf = surf.copy()
                    temp_surf.set_alpha(alpha)
                    screen.blit(temp_surf, rect)
                    # Các dòng thông tin đã hiện trước đó
                    for j in range(idx):
                        screen.blit(info_surfaces[j], info_rects[j])
                    pygame.display.flip()
                    pygame.time.delay(40)
            # Sau khi hiện xong, cho phép nhấn phím để thoát
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        waiting = False
                        running = False
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        waiting = False
                if congrats_bg:
                    screen.blit(congrats_bg, (0, 0))
                else:
                    screen.fill(WHITE)
                # Animation nhân vật chiến thắng (lặp)
                if WIN_ANIMATION_FRAMES:
                    win_frame = pygame.transform.scale(WIN_ANIMATION_FRAMES[anim_idx % len(WIN_ANIMATION_FRAMES)], (180, 180))
                    win_frame.set_alpha(255)
                    player_img_rect = win_frame.get_rect()
                    player_img_rect.center = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2)
                    screen.blit(win_frame, player_img_rect)
                    anim_idx += 1
                # Dòng chữ chúc mừng
                end_message.surface.set_alpha(255)
                end_message.rect.midtop = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 100)
                end_message.draw(screen)
                # Các dòng thông tin
                for surf, rect in zip(info_surfaces, info_rects):
                    screen.blit(surf, rect)
                pygame.display.flip()
                pygame.time.delay(80)
            continue

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
                # Hiệu ứng Game Over bằng GIF
                fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                # Fade in Game Over GIF
                for alpha in range(0, 256, 8):
                    if GAME_OVER_GIF_FRAMES:
                        frame_idx = (alpha // 8) % len(GAME_OVER_GIF_FRAMES)
                        gif_frame = pygame.transform.scale(GAME_OVER_GIF_FRAMES[frame_idx], (240, 240))
                        gif_frame.set_alpha(alpha)
                        gif_rect = gif_frame.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
                        screen.fill((30, 30, 30))
                        screen.blit(gif_frame, gif_rect)
                    else:
                        fade_surface.fill((0, 0, 0, alpha))
                        screen.blit(fade_surface, (0, 0))
                    # Dòng chữ Game Over
                    go_font = pygame.font.SysFont('arialblack', 60)
                    go_text = go_font.render("Game Over", True, (255, 0, 0))
                    go_text.set_alpha(alpha)
                    go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
                    screen.blit(go_text, go_rect)
                    pygame.display.flip()
                    pygame.time.delay(30)
                # Lặp animation cho đến khi nhấn phím hoặc đóng cửa sổ
                waiting = True
                anim_idx = 0
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            waiting = False
                            running = False
                        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                            waiting = False
                    screen.fill((30, 30, 30))
                    if GAME_OVER_GIF_FRAMES:
                        gif_frame = pygame.transform.scale(GAME_OVER_GIF_FRAMES[anim_idx % len(GAME_OVER_GIF_FRAMES)], (240, 240))
                        gif_rect = gif_frame.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
                        screen.blit(gif_frame, gif_rect)
                        anim_idx += 1
                    go_font = pygame.font.SysFont('arialblack', 60)
                    go_text = go_font.render("Game Over", True, (255, 0, 0))
                    go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
                    screen.blit(go_text, go_rect)
                    pygame.display.flip()
                    pygame.time.delay(80)
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
                    kills += 1  # Tăng số quái vật bị hạ
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
