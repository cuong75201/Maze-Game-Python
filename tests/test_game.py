import pygame
import sys

# Khởi tạo Pygame
pygame.init()

# Cài đặt màn hình
WIDTH, HEIGHT = 600, 600
CELL_SIZE = 40
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Maze Game")

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Thiết kế mê cung (1 là tường, 0 là đường đi)
maze = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1], 
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Vị trí ban đầu của người chơi và đích đến
player_pos = [1, 1]  # [x, y]
goal_pos = [13, 13]

# Tạo hình vuông đại diện cho người chơi
PLAYER_SIZE = 30  # Kích thước hình vuông (nhỏ hơn CELL_SIZE để nhìn rõ hơn)
player_rect = pygame.Rect(
    player_pos[0] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2,
    player_pos[1] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2,
    PLAYER_SIZE,
    PLAYER_SIZE
)

# Hàm vẽ mê cung
def draw_maze():
    for y in range(len(maze)):
        for x in range(len(maze[y])):
            if maze[y][x] == 1:
                pygame.draw.rect(screen, BLACK, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            elif [x, y] == goal_pos:
                pygame.draw.rect(screen, GREEN, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

# Hàm vẽ người chơi (dùng hình vuông)
def draw_player():
    pygame.draw.rect(screen, RED, player_rect)

# Vòng lặp chính
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Lấy trạng thái phím bấm
    keys = pygame.key.get_pressed()

    # Tính toán vị trí mới của người chơi
    new_x, new_y = player_pos[0], player_pos[1]
    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and maze[player_pos[1]][player_pos[0] - 1] == 0:
        new_x -= 1  # Di chuyển trái
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and maze[player_pos[1]][player_pos[0] + 1] == 0:
        new_x += 1  # Di chuyển phải
    if (keys[pygame.K_UP] or keys[pygame.K_w]) and maze[player_pos[1] - 1][player_pos[0]] == 0:
        new_y -= 1  # Di chuyển lên
    if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and maze[player_pos[1] + 1][player_pos[0]] == 0:
        new_y += 1  # Di chuyển xuống

    # Cập nhật vị trí người chơi
    if [new_x, new_y] != [player_pos[0], player_pos[1]]:  # Chỉ cập nhật nếu có thay đổi
        player_pos[0], player_pos[1] = new_x, new_y
        # Cập nhật vị trí của hình vuông
        player_rect.x = player_pos[0] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2
        player_rect.y = player_pos[1] * CELL_SIZE + (CELL_SIZE - PLAYER_SIZE) // 2

    # Kiểm tra thắng
    if player_pos == goal_pos:
        print("Bạn đã thắng!")
        running = False

    # Vẽ lại màn hình
    screen.fill(WHITE)
    draw_maze()
    draw_player()
    pygame.display.flip()
    clock.tick(60)  # Giới hạn FPS

# Thoát game
pygame.quit()
sys.exit()