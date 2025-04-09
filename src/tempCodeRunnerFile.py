import pygame
from player import Player
from maze import Maze

# Khởi tạo Pygame
pygame.init()

# Thiết lập màn hình
WIDTH, HEIGHT = 1000, 1000
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Shooter Game")

# Màu sắc
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Tải hình ảnh giao diện người dùng
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

# Vị trí giao diện người dùng
ICON_X, ICON_Y = 10, HEIGHT - 100
BULLET_ICON_X, BULLET_ICON_Y = ICON_X, ICON_Y + 50
AMMO_TEXT_X, AMMO_TEXT_Y = BULLET_ICON_X + 40, BULLET_ICON_Y + 5

# Font để hiển thị số đạn
font = pygame.font.Font(None, 36)

# FPS
clock = pygame.time.Clock()
FPS = 60

# Khởi tạo game assets
game_assets = {
    "WallStone": [
        pygame.transform.scale(pygame.image.load("assets/images/level/WallStone/wallStone.png"), (17, 12)),
        pygame.transform.scale(pygame.image.load("assets/images/level/WallStone/wallStone_fence.png"), (17, 12))
    ],
    "WallBreakable": [
        pygame.transform.scale(pygame.image.load("assets/images/level/WallBreakable/wallBreakable.png"), (17, 12)),
        pygame.transform.scale(pygame.image.load("assets/images/level/WallBreakable/wallBreakable_small.png"), (17, 12))
    ],
    "Earth": [
        pygame.transform.scale(pygame.image.load("assets/images/level/Earth/groundEarth_checkered.png"), (17, 12)),
        pygame.transform.scale(pygame.image.load("assets/images/level/Earth/groundExit.png"), (17, 12))
    ]
}

# Khởi tạo mê cung
maze = Maze(game={"assets": game_assets}, tile_size=(17, 12))
maze.load("map1.json")

# Hàm kiểm tra vị trí hợp lệ
def is_position_valid(maze, x, y, player_rect):
    player_rect.center = (x, y)
    for loc in maze.tilemap:
        tile = maze.tilemap[loc]
        if tile['type'] in ["WallStone", "WallBreakable"]:
            tile_rect = pygame.Rect(
                tile['pos'][0] * maze.tile_size[0],
                tile['pos'][1] * maze.tile_size[1],
                maze.tile_size[0],
                tile.get('scale', maze.tile_size)[1]
            )
            if player_rect.colliderect(tile_rect):
                return False
    return True

# Tìm vị trí khởi tạo hợp lệ cho nhân vật
def find_valid_starting_position(maze, player_size=(50, 50)):
    tile_size = maze.tile_size
    valid_positions = []

    # Thu thập tất cả các ô "Earth"
    for loc in maze.tilemap:
        tile = maze.tilemap[loc]
        if tile['type'] == "Earth":
            pos_x, pos_y = tile['pos']
            pixel_x = pos_x * tile_size[0] + tile_size[0] // 2
            pixel_y = pos_y * tile_size[1] + tile_size[1] // 2
            valid_positions.append((pixel_x, pixel_y))

    if not valid_positions:
        raise ValueError("Không tìm thấy ô 'Earth' nào trong mê cung!")

    # Sắp xếp theo khoảng cách từ góc trên cùng bên trái
    valid_positions.sort(key=lambda pos: (pos[0], pos[1]))

    # Kiểm tra từng vị trí
    player_rect = pygame.Rect(0, 0, player_size[0], player_size[1])
    for pixel_x, pixel_y in valid_positions:
        if is_position_valid(maze, pixel_x, pixel_y, player_rect):
            return pixel_x, pixel_y

    raise ValueError("Không tìm thấy vị trí hợp lệ nào để đặt nhân vật!")

# Khởi tạo nhân vật
try:
    player_x, player_y = find_valid_starting_position(maze)
    print(f"Đặt nhân vật tại ({player_x}, {player_y})")
except ValueError as e:
    print(e)
    player_x, player_y = maze.tile_size[0] * 1.5, maze.tile_size[1] * 1.5  # Vị trí tạm thời
    print(f"Đặt tạm nhân vật tại ({player_x}, {player_y}) - Vui lòng kiểm tra file map1.json!")

player = Player(player_x, player_y, maze=maze)

# Vòng lặp chính của game
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Xử lý đầu vào
    keys = pygame.key.get_pressed()
    player.move(keys)
    if keys[pygame.K_SPACE]:
        player.shoot()

    # Cập nhật trạng thái
    player.update_bullets()

    # Vẽ giao diện
    screen.fill(WHITE)
    maze.render(screen)
    screen.blit(player_icon, (ICON_X, ICON_Y))
    screen.blit(bullet_icon, (BULLET_ICON_X, BULLET_ICON_Y))
    ammo_text = font.render(f": {player.bullets}", True, BLACK)
    screen.blit(ammo_text, (AMMO_TEXT_X, AMMO_TEXT_Y))
    player.draw(screen)

    # Cập nhật màn hình
    pygame.display.flip()
    clock.tick(FPS)

# Thoát game
pygame.quit()