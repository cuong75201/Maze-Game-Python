import pygame
import sys
import random
import os
import math

# Thêm thư mục src vào sys.path để import được các module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from enemy import Enemy
except ImportError as e:
    print(f"Error importing Enemy: {e}")
    sys.exit(1)

# Khởi tạo Pygame
pygame.init()

# Cài đặt màn hình
WIDTH, HEIGHT = 900, 900
CELL_SIZE = 30
MAZE_WIDTH, MAZE_HEIGHT = 30, 30
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Game")

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Tạo mê cung bằng thuật toán Recursive Backtracking
def generate_maze(width, height):
    maze = [[1 for _ in range(width)] for _ in range(height)]
    start_x, start_y = 1, 1
    maze[start_y][start_x] = 0
    stack = [(start_x, start_y)]
    directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
    while stack:
        x, y = stack[-1]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 < nx < width - 1 and 0 < ny < height - 1 and maze[ny][nx] == 1:
                neighbors.append((nx, ny))
        if neighbors:
            nx, ny = random.choice(neighbors)
            maze[ny][nx] = 0
            maze[y + (ny - y) // 2][x + (nx - x) // 2] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    return maze

# Tạo mê cung
maze = generate_maze(MAZE_WIDTH, MAZE_HEIGHT)

# Vị trí ban đầu của người chơi và đích đến
player_pos = [1, 1]
goal_pos = [MAZE_WIDTH - 2, MAZE_HEIGHT - 2]

# Tạo hình vuông đại diện cho người chơi
PLAYER_SIZE = 20
player_rect = pygame.Rect(
    player_pos[0] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2,
    player_pos[1] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2,
    PLAYER_SIZE,
    PLAYER_SIZE
)

# Thêm các biến để làm chậm di chuyển của người chơi
player_target_pos = None
player_speed = 120
player_last_move = 0
player_move_delay = 0

# Hàm tìm vị trí trống gần một tọa độ mục tiêu
def find_safe_spawn_position(maze, maze_width, maze_height, target_x, target_y):
    for dy in range(0, 3):
        for dx in range(0, 3):
            x = target_x - dx
            y = target_y - dy
            if 0 <= x < maze_width and 0 <= y < maze_height and maze[y][x] == 0:
                return x, y
    return target_x, target_y

# Tạo quái vật
enemies = [
    Enemy(x=6, y=5, cell_size=CELL_SIZE, maze_width=MAZE_WIDTH, maze_height=MAZE_HEIGHT, maze=maze, enemy_type="slime"),
    Enemy(x=10, y=2, cell_size=CELL_SIZE, maze_width=MAZE_WIDTH, maze_height=MAZE_HEIGHT, maze=maze, enemy_type="slime"),
    Enemy(x=28, y=2, cell_size=CELL_SIZE, maze_width=MAZE_WIDTH, maze_height=MAZE_HEIGHT, maze=maze, enemy_type="skeleton"),
    Enemy(x=2, y=28, cell_size=CELL_SIZE, maze_width=MAZE_WIDTH, maze_height=MAZE_HEIGHT, maze=maze, enemy_type="zombie"),
    Enemy(x=14, y=10, cell_size=CELL_SIZE, maze_width=MAZE_WIDTH, maze_height=MAZE_HEIGHT, maze=maze, enemy_type="giant"),
]

# Spawn Ghost ở góc dưới-phải (28,28)
ghost_x, ghost_y = find_safe_spawn_position(maze, MAZE_WIDTH, MAZE_HEIGHT, 28, 28)
enemies.append(Enemy(x=ghost_x, y=ghost_y, cell_size=CELL_SIZE, maze_width=MAZE_WIDTH, maze_height=MAZE_HEIGHT, maze=maze, enemy_type="ghost"))
print(f"Spawned Ghost at ({ghost_x}, {ghost_y})")

# Vòng lặp chính
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if player_target_pos:
        dx = player_target_pos[0] - player_rect.x
        dy = player_target_pos[1] - player_rect.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > 1:
            speed_per_frame = player_speed / 60
            if distance <= speed_per_frame:
                player_rect.x = player_target_pos[0]
                player_rect.y = player_target_pos[1]
                player_pos[0] = player_rect.x // CELL_SIZE
                player_pos[1] = player_rect.y // CELL_SIZE
                player_target_pos = None
            else:
                direction_x = dx / distance
                direction_y = dy / distance
                player_rect.x += direction_x * speed_per_frame
                player_rect.y += direction_y * speed_per_frame
        else:
            player_rect.x = player_target_pos[0]
            player_rect.y = player_target_pos[1]
            player_pos[0] = player_rect.x // CELL_SIZE
            player_pos[1] = player_rect.y // CELL_SIZE
            player_target_pos = None

    current_time = pygame.time.get_ticks()
    if player_target_pos is None and current_time - player_last_move >= player_move_delay:
        keys = pygame.key.get_pressed()
        new_x, new_y = player_pos[0], player_pos[1]

        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and 0 <= player_pos[1] < MAZE_HEIGHT and 0 <= player_pos[0] - 1 < MAZE_WIDTH and maze[player_pos[1]][player_pos[0] - 1] == 0:
            new_x -= 1
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and 0 <= player_pos[1] < MAZE_HEIGHT and 0 <= player_pos[0] + 1 < MAZE_WIDTH and maze[player_pos[1]][player_pos[0] + 1] == 0:
            new_x += 1
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and 0 <= player_pos[1] - 1 < MAZE_HEIGHT and 0 <= player_pos[0] < MAZE_WIDTH and maze[player_pos[1] - 1][player_pos[0]] == 0:
            new_y -= 1
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and 0 <= player_pos[1] + 1 < MAZE_HEIGHT and 0 <= player_pos[0] < MAZE_WIDTH and maze[player_pos[1] + 1][player_pos[0]] == 0:
            new_y += 1

        if [new_x, new_y] != [player_pos[0], player_pos[1]]:
            player_pos[0], player_pos[1] = new_x, new_y
            player_target_pos = (
                player_pos[0] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2,
                player_pos[1] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2
            )
            player_last_move = current_time

    for enemy in enemies:
        enemy.move(player_pos, player_rect)

    # Kiểm tra va chạm giữa người chơi và quái vật
    for enemy in enemies:
        if enemy.is_visible and player_rect.colliderect(enemy.rect):
            print("Bạn đã thua!")
            running = False
            break
        # Kiểm tra va chạm giữa người chơi và thanh kiếm của Skeleton
        if enemy.enemy_type == "skeleton":
            for projectile in enemy.projectiles:
                if player_rect.colliderect(projectile["rect"]):
                    print("Bạn bị trúng kiếm! Bạn đã thua!")
                    running = False
                    break
        # Kiểm tra va chạm giữa người chơi và magic của Ghost
        if enemy.enemy_type == "ghost":
            for projectile in enemy.projectiles:
                if player_rect.colliderect(projectile["rect"]):
                    print("Bạn bị trúng magic! Bạn đã thua!")
                    running = False
                    break
        # Kiểm tra va chạm giữa người chơi và sóng xung kích của Giant
        if enemy.enemy_type == "giant" and enemy.shockwave:
            shockwave_center = enemy.shockwave["center"]
            shockwave_radius = enemy.shockwave["radius"]
            player_center = (player_rect.centerx, player_rect.centery)
            distance_to_shockwave = math.sqrt(
                (player_center[0] - shockwave_center[0])**2 +
                (player_center[1] - shockwave_center[1])**2
            )
            if distance_to_shockwave <= shockwave_radius:
                print("Bạn bị trúng sóng xung kích của Giant! Bạn đã thua!")
                running = False
                break

    if player_pos == goal_pos:
        print("Bạn đã thắng!")
        running = False

    screen.fill(WHITE)
    for y in range(len(maze)):
        for x in range(len(maze[y])):
            if maze[y][x] == 1:
                pygame.draw.rect(screen, BLACK, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif [x, y] == goal_pos:
                pygame.draw.rect(screen, GREEN, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, RED, player_rect)
    for enemy in enemies:
        enemy.draw(screen)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()