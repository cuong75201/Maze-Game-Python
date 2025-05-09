import sys
import os
import pygame
from src.maze import Maze
from src.bullet import Bullet
from src.enemy import Enemy
from src.player import Player
import random
import math
from config import config, load_config, save_config
from src.button import Button
from config import load_image

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

def main():
    pygame.init()
    pygame.mixer.init()
    WIDTH, HEIGHT = 1000, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Maze Shooter Game")

    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    load_config()
    game_speed = config.get('game_speed', 1)

    # Thêm biến để lưu trạng thái tạm dừng
    paused = False
    pause_font = pygame.font.SysFont('arial', 60, bold=True)
    pause_text = pause_font.render("PAUSED", True, BLACK)
    pause_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
    
    # Tạo các nút menu đơn giản
    menu_font = pygame.font.SysFont('arial', 40)
    play_text = menu_font.render("Play", True, BLACK)
    play_rect = play_text.get_rect(center=(WIDTH//2 - 100, HEIGHT//2))
    options_text = menu_font.render("Options", True, BLACK)
    options_rect = options_text.get_rect(center=(WIDTH//2 + 100, HEIGHT//2))
    menu_text = menu_font.render("Menu", True, BLACK)
    menu_rect = menu_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))

    # Lưu trạng thái game khi tạm dừng
    game_state = {
        'player_pos': None,
        'player_health': None,
        'player_bullets': None,
        'enemies': None,
        'ammo_boxes': None,
        'kills': None,
        'start_ticks': None
    }

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "..", "assets")
    SOUND_DIR = os.path.join(ASSETS_DIR, "sounds")

    background_music = None
    try:
        background_music = pygame.mixer.Sound(os.path.join(SOUND_DIR, "background_music.wav"))
        background_music.set_volume(config.get('music_volume', 50) / 100.0)
        background_music.play(-1)
    except pygame.error as e:
        print(f"Không thể tải nhạc nền: {e}")

    gun_shot_sound = None
    try:
        gun_shot_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "gun_shot.wav"))
        gun_shot_sound.set_volume(config.get('sfx_volume', 50) / 100.0)
    except pygame.error as e:
        print(f"Không thể tải âm thanh súng: {e}")

    try:
        player_icon = pygame.image.load(os.path.join(
            ASSETS_DIR, "images", "hero", "walkA", "hero_walkA_0000.png"))
        player_icon = pygame.transform.scale(player_icon, (50, 50))
    except pygame.error:
        player_icon = pygame.Surface((50, 50))
        player_icon.fill(WHITE)

    try:
        bullet_icon = pygame.image.load(
            os.path.join(ASSETS_DIR, "images", "bullet", "bullet.png"))
        bullet_icon = pygame.transform.scale(bullet_icon, (30, 35))
    except pygame.error:
        bullet_icon = pygame.Surface((30, 35))
        bullet_icon.fill((255, 255, 0))

    try:
        ammo_box_image = pygame.image.load(
            os.path.join(ASSETS_DIR, "images", "bullet", "ammo_box.png"))
        ammo_box_image = pygame.transform.scale(
            ammo_box_image, (30, 35))
    except pygame.error as e:
        print(f"Không thể tải ammo_box.png: {e}")
        ammo_box_image = pygame.Surface((30, 35))
        ammo_box_image.fill((0, 255, 0))

    ICON_X, ICON_Y = 10, HEIGHT - 100
    AMMO_ICON_X, AMMO_ICON_Y = ICON_X, ICON_Y + 50
    AMMO_TEXT_X, AMMO_TEXT_Y = AMMO_ICON_X + 40, AMMO_ICON_Y + 5
    HP_TEXT_X, HP_TEXT_Y = ICON_X + 51, ICON_Y + 15

    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()
    FPS = 60

    TILE_SIZE = (34, 24)

    game_assets = {
        "WallStone": [
            pygame.transform.scale(pygame.image.load(os.path.join(
                ASSETS_DIR, "images", "level", "WallStone", "wallStone.png")), TILE_SIZE),
            pygame.transform.scale(pygame.image.load(os.path.join(
                ASSETS_DIR, "images", "level", "WallStone", "wallStone_fence.png")), TILE_SIZE)
        ],
        "WallBreakable": [
            pygame.transform.scale(pygame.image.load(os.path.join(
                ASSETS_DIR, "images", "level", "WallBreakable", "wallBreakable.png")), TILE_SIZE),
            pygame.transform.scale(pygame.image.load(os.path.join(
                ASSETS_DIR, "images", "level", "WallBreakable", "wallBreakable_small.png")), TILE_SIZE)
        ],
        "Earth": [
            pygame.transform.scale(pygame.image.load(os.path.join(
                ASSETS_DIR, "images", "level", "Earth", "groundEarth_checkered.png")), TILE_SIZE),
            pygame.transform.scale(pygame.image.load(os.path.join(
                ASSETS_DIR, "images", "level", "Earth", "groundExit.png")), TILE_SIZE)
        ]
    }

    maze = Maze(game={"assets": game_assets}, tile_size=TILE_SIZE)
    try:
        maze.load("maps/map1_scaled.json")
    except Exception as e:
        print(f"Error loading map: {e}")
        return

    CONGRATS_BG_PATH = os.path.join(ASSETS_DIR, "images", "congratulations.png")
    try:
        congrats_bg = pygame.image.load(CONGRATS_BG_PATH)
        congrats_bg = pygame.transform.scale(congrats_bg, (WIDTH, HEIGHT))
    except Exception:
        congrats_bg = None

    WIN_ANIMATION_FRAMES = []
    for i in range(17):
        frame_path = os.path.join(ASSETS_DIR, "images", "hero", "winA", f"hero_winA_{i:04d}.png")
        try:
            frame = pygame.image.load(frame_path).convert_alpha()
            WIN_ANIMATION_FRAMES.append(frame)
        except Exception:
            pass

    GAME_OVER_GIF_FRAMES = []
    try:
        import glob
        gif_dir = os.path.join(ASSETS_DIR, "images", "gameover_gif")
        gif_frame_paths = sorted(glob.glob(os.path.join(gif_dir, "*.png")))
        for path in gif_frame_paths:
            frame = pygame.image.load(path).convert_alpha()
            GAME_OVER_GIF_FRAMES.append(frame)
    except Exception:
        pass

    class AmmoBox:
        def __init__(self, x, y):
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
                    tile.get('scale', maze.tile_size)[0],
                    tile.get('scale', maze.tile_size)[1]
                )
                if rect.colliderect(tile_rect):
                    print(f"Invalid position ({x}, {y}) due to collision with tile at {tile['pos']}")
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
                print(f"Found valid position for spawn: ({pixel_x}, {pixel_y})")
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
    player.gun_shot_sound = gun_shot_sound
    player.speed *= game_speed
    player.roll_speed *= game_speed
    if gun_shot_sound:
        print("Đã gán âm thanh súng cho player")
    else:
        print("Không thể gán âm thanh súng cho player vì gun_shot_sound là None")

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
            enemy.speed *= game_speed
            enemy.base_speed *= game_speed
            enemies.append(enemy)
            print(f"Đã đặt {enemy_type} tại vị trí ({enemy_x}, {enemy_y})")
        except ValueError as e:
            print(f"Không thể đặt {enemy_type}: {e}")

    ammo_boxes = []
    MAX_AMMO_BOXES = 20
    AMMO_BOX_SPAWN_CHANCE = 0.01
    PLAYER_MAX_BULLETS = 150

    class EndGameMessage:
        def __init__(self, text, font, color=BLACK):
            self.text = text
            self.font = font
            self.color = color
            self.surface = self.font.render(self.text, True, self.color)
            self.rect = self.surface.get_rect(center=(WIDTH // 2 + WIDTH // 4, HEIGHT // 2))

        def draw(self, screen):
            screen.blit(self.surface, self.rect)

    start_ticks = pygame.time.get_ticks()
    kills = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                    if paused:
                        # Lưu trạng thái game khi tạm dừng
                        game_state['player_pos'] = (player.rect.x, player.rect.y)
                        game_state['player_health'] = player.health
                        game_state['player_bullets'] = player.bullets
                        game_state['enemies'] = [(e.rect.x, e.rect.y, e.enemy_type, e.hp) for e in enemies]
                        game_state['ammo_boxes'] = [(a.rect.x, a.rect.y) for a in ammo_boxes]
                        game_state['kills'] = kills
                        game_state['start_ticks'] = pygame.time.get_ticks() - start_ticks
                    else:
                        # Khôi phục trạng thái game khi tiếp tục
                        if game_state['player_pos']:
                            player.rect.x, player.rect.y = game_state['player_pos']
                            player.health = game_state['player_health']
                            player.bullets = game_state['player_bullets']
                            enemies.clear()
                            for e_x, e_y, e_type, e_hp in game_state['enemies']:
                                enemy = Enemy(
                                    x=e_x // TILE_SIZE[0],
                                    y=e_y // TILE_SIZE[1],
                                    cell_size=TILE_SIZE[0],
                                    maze_width=maze_width,
                                    maze_height=maze_height,
                                    maze=maze_grid,
                                    enemy_type=e_type
                                )
                                enemy.rect.x = e_x
                                enemy.rect.y = e_y
                                enemy.hp = e_hp
                                enemy.speed *= game_speed
                                enemy.base_speed *= game_speed
                                enemies.append(enemy)
                            ammo_boxes.clear()
                            for a_x, a_y in game_state['ammo_boxes']:
                                ammo_box = AmmoBox(a_x, a_y)
                                ammo_boxes.append(ammo_box)
                            kills = game_state['kills']
                            start_ticks = pygame.time.get_ticks() - game_state['start_ticks']
            elif event.type == pygame.MOUSEBUTTONDOWN and paused:
                mouse_pos = pygame.mouse.get_pos()
                if play_rect.collidepoint(mouse_pos):
                    paused = False
                    # Khôi phục trạng thái game
                    if game_state['player_pos']:
                        player.rect.x, player.rect.y = game_state['player_pos']
                        player.health = game_state['player_health']
                        player.bullets = game_state['player_bullets']
                        enemies.clear()
                        for e_x, e_y, e_type, e_hp in game_state['enemies']:
                            enemy = Enemy(
                                x=e_x // TILE_SIZE[0],
                                y=e_y // TILE_SIZE[1],
                                cell_size=TILE_SIZE[0],
                                maze_width=maze_width,
                                maze_height=maze_height,
                                maze=maze_grid,
                                enemy_type=e_type
                            )
                            enemy.rect.x = e_x
                            enemy.rect.y = e_y
                            enemy.hp = e_hp
                            enemy.speed *= game_speed
                            enemy.base_speed *= game_speed
                            enemies.append(enemy)
                        ammo_boxes.clear()
                        for a_x, a_y in game_state['ammo_boxes']:
                            ammo_box = AmmoBox(a_x, a_y)
                            ammo_boxes.append(ammo_box)
                        kills = game_state['kills']
                        start_ticks = pygame.time.get_ticks() - game_state['start_ticks']
                elif options_rect.collidepoint(mouse_pos):
                    # Mở menu tùy chọn
                    from src.options import OptionsMenu
                    options_menu = OptionsMenu(config)
                    options_menu.run()
                    # Lưu các thay đổi cấu hình
                    save_config()
                    load_config()
                    # Cập nhật âm lượng
                    if background_music:
                        background_music.set_volume(config.get('music_volume', 50) / 100.0)
                    if gun_shot_sound:
                        gun_shot_sound.set_volume(config.get('sfx_volume', 50) / 100.0)
                elif menu_rect.collidepoint(mouse_pos):
                    # Dừng nhạc nền
                    if background_music:
                        background_music.stop()
                    # Quay về menu chính
                    return

        if not paused:
            keys = pygame.key.get_pressed()
            player.move(keys)
            if keys[pygame.K_SPACE]:
                player.shoot()

            player.update_bullets()

        player_grid_x = player.rect.centerx // TILE_SIZE[0]
        player_grid_y = player.rect.centery // TILE_SIZE[1]
        player_pos = (player_grid_y, player_grid_x)

        tile_key = f"{player_grid_x};{player_grid_y}"
        if tile_key in maze.tilemap:
            tile = maze.tilemap[tile_key]
            if tile['type'] == 'Earth' and tile.get('variant', 0) == 1:
                if background_music:
                    background_music.stop()
                fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                for alpha in range(0, 256, 4):
                    if congrats_bg:
                        temp_bg = congrats_bg.copy()
                        temp_bg.set_alpha(alpha)
                        screen.blit(temp_bg, (0, 0))
                    else:
                        fade_surface.fill((255, 255, 255, alpha))
                        screen.blit(fade_surface, (0, 0))
                    frame_idx = (alpha // 8) % len(WIN_ANIMATION_FRAMES) if WIN_ANIMATION_FRAMES else 0
                    if WIN_ANIMATION_FRAMES:
                        win_frame = pygame.transform.scale(WIN_ANIMATION_FRAMES[frame_idx], (180, 180))
                        win_frame.set_alpha(alpha)
                        player_img_rect = win_frame.get_rect()
                        player_img_rect.center = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2)
                        screen.blit(win_frame, player_img_rect)
                    end_message = EndGameMessage("Congratulations! You Win!", font)
                    end_message.surface.set_alpha(alpha)
                    end_message.rect.midtop = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 100)
                    end_message.draw(screen)
                    pygame.display.flip()
                    pygame.time.delay(30)
                waiting = True
                anim_idx = 0
                play_time = (pygame.time.get_ticks() - start_ticks) // 1000
                minutes = play_time // 60
                seconds = play_time % 60
                info_texts = [
                    f"Time: {minutes:02d}:{seconds:02d}",
                    f"Enemies Defeated: {kills}"
                ]
                info_surfaces = [font.render(text, True, (0,0,0)) for text in info_texts]
                info_rects = [surf.get_rect(midtop=(WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 150 + i*50)) for i, surf in enumerate(info_surfaces)]
                for idx, (surf, rect) in enumerate(zip(info_surfaces, info_rects)):
                    for alpha in range(0, 256, 16):
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                waiting = False
                                running = False
                        if congrats_bg:
                            screen.blit(congrats_bg, (0, 0))
                        else:
                            screen.fill(WHITE)
                        if WIN_ANIMATION_FRAMES:
                            win_frame = pygame.transform.scale(WIN_ANIMATION_FRAMES[anim_idx % len(WIN_ANIMATION_FRAMES)], (180, 180))
                            win_frame.set_alpha(255)
                            player_img_rect = win_frame.get_rect()
                            player_img_rect.center = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2)
                            screen.blit(win_frame, player_img_rect)
                        end_message.surface.set_alpha(255)
                        end_message.rect.midtop = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 100)
                        end_message.draw(screen)
                        temp_surf = surf.copy()
                        temp_surf.set_alpha(alpha)
                        screen.blit(temp_surf, rect)
                        for j in range(idx):
                            screen.blit(info_surfaces[j], info_rects[j])
                        pygame.display.flip()
                        pygame.time.delay(40)
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
                    if WIN_ANIMATION_FRAMES:
                        win_frame = pygame.transform.scale(WIN_ANIMATION_FRAMES[anim_idx % len(WIN_ANIMATION_FRAMES)], (180, 180))
                        win_frame.set_alpha(255)
                        player_img_rect = win_frame.get_rect()
                        player_img_rect.center = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2)
                        screen.blit(win_frame, player_img_rect)
                        anim_idx += 1
                    end_message.surface.set_alpha(255)
                    end_message.rect.midtop = (WIDTH // 2 + WIDTH // 4, HEIGHT // 2 + 100)
                    end_message.draw(screen)
                    for surf, rect in zip(info_surfaces, info_rects):
                        screen.blit(surf, rect)
                    pygame.display.flip()
                    pygame.time.delay(80)
                return

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
            enemy.move(player_pos, player.rect, dt)
            if enemy.is_visible and enemy.rect.colliderect(player.rect):
                player.health -= 50
                if player.health <= 0:
                    if background_music:
                        background_music.stop()
                    fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
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
                        go_font = pygame.font.SysFont('arialblack', 60)
                        go_text = go_font.render("Game Over", True, (255, 0, 0))
                        go_text.set_alpha(alpha)
                        go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
                        screen.blit(go_text, go_rect)
                        pygame.display.flip()
                        pygame.time.delay(30)
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
                    return

            for bullet in player.bullet_list[:]:
                if enemy.is_visible and bullet.rect.colliderect(enemy.rect):
                    enemy.hp -= bullet.damage
                    enemy.create_particles(bullet.rect.centerx, bullet.rect.centery, (255, 255, 0))
                    player.bullet_list.remove(bullet)
                    if enemy.hp <= 0:
                        enemies.remove(enemy)
                        enemy.create_particles(enemy.rect.centerx, enemy.rect.centery, (255, 0, 0))
                        kills += 1
                    break

            if hasattr(enemy, 'projectiles'):
                for projectile in enemy.projectiles:
                    if projectile["rect"].colliderect(player.rect):
                        if enemy.enemy_type in ["skeleton", "ghost"]:
                            player.health -= 50
                        else:
                            player.health -= 5
                        enemy.projectiles.remove(projectile)
                        if player.health <= 0:
                            if background_music:
                                background_music.stop()
                            running = False
                            print("Người chơi đã bị hạ gục bởi đạn quái vật!")
                        break

        map_width = maze_width * TILE_SIZE[0]
        map_height = maze_height * TILE_SIZE[1]

        camera_offset_x = player.rect.centerx - WIDTH // 2
        camera_offset_y = player.rect.centery - HEIGHT // 2

        camera_offset_x = max(0, min(camera_offset_x, map_width - WIDTH))
        camera_offset_y = max(0, min(camera_offset_y, map_height - HEIGHT))

        offset = (camera_offset_x, camera_offset_y)

        screen.fill(WHITE)
        maze.render(screen, offset=offset)
        screen.blit(player_icon, (ICON_X, ICON_Y))

        hp_text = font.render(f"{int(player.health)}/100", True, BLACK)
        screen.blit(hp_text, (HP_TEXT_X, HP_TEXT_Y))

        screen.blit(ammo_box_image, (AMMO_ICON_X, AMMO_ICON_Y))
        ammo_text = font.render(f": {player.bullets}/{PLAYER_MAX_BULLETS}", True, BLACK)
        screen.blit(ammo_text, (AMMO_TEXT_X, AMMO_TEXT_Y))

        player.draw(screen, offset=offset)
        for enemy in enemies:
            enemy.draw(screen, offset=offset)
        for ammo_box in ammo_boxes:
            ammo_box.draw(screen, offset=offset)

        # Hiển thị màn hình tạm dừng
        if paused:
            # Tạo surface bán trong suốt
            pause_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pause_surface.fill((255, 255, 255, 128))
            screen.blit(pause_surface, (0, 0))
            screen.blit(pause_text, pause_rect)
            
            # Vẽ các nút menu
            pygame.draw.rect(screen, (200, 200, 200), play_rect.inflate(20, 10))
            pygame.draw.rect(screen, (200, 200, 200), options_rect.inflate(20, 10))
            pygame.draw.rect(screen, (200, 200, 200), menu_rect.inflate(20, 10))
            screen.blit(play_text, play_rect)
            screen.blit(options_text, options_rect)
            screen.blit(menu_text, menu_rect)

        pygame.display.flip()

    if background_music:
        background_music.stop()

if __name__ == "__main__":
    main()