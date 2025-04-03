import pygame
import unittest
import sys
import os
import random

# Thêm thư mục src vào sys.path để import được các module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from enemy import Enemy

class TestGame(unittest.TestCase):
    def setUp(self):
        # Khởi tạo Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((900, 900))
        pygame.display.set_caption("Test Maze Game")
        self.clock = pygame.time.Clock()

        # Cài đặt màn hình
        self.WIDTH, self.HEIGHT = 900, 900
        self.CELL_SIZE = 30
        self.MAZE_WIDTH, self.MAZE_HEIGHT = 30, 30

        # Màu sắc
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)

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
        self.maze = generate_maze(self.MAZE_WIDTH, self.MAZE_HEIGHT)

        # Vị trí ban đầu của người chơi và đích đến
        self.player_pos = [1, 1]  # [x, y]
        self.goal_pos = [self.MAZE_WIDTH - 2, self.MAZE_HEIGHT - 2]

        # Tạo hình vuông đại diện cho người chơi
        self.PLAYER_SIZE = 20
        self.player_rect = pygame.Rect(
            self.player_pos[0] * self.CELL_SIZE + (self.CELL_SIZE - self.PLAYER_SIZE) // 2,
            self.player_pos[1] * self.CELL_SIZE + (self.CELL_SIZE - self.PLAYER_SIZE) // 2,
            self.PLAYER_SIZE,
            self.PLAYER_SIZE
        )

        # Tạo quái vật
        self.enemies = [
            Enemy(5, 5, self.CELL_SIZE, self.MAZE_WIDTH, self.MAZE_HEIGHT, self.maze),
            Enemy(15, 15, self.CELL_SIZE, self.MAZE_WIDTH, self.MAZE_HEIGHT, self.maze),
        ]

    def test_game_run(self):
        running = True
        frame_count = 0
        # Chạy cho đến khi người dùng đóng cửa sổ hoặc đạt đích
        while running:
            # Xử lý sự kiện
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

            # Lấy trạng thái phím bấm
            keys = pygame.key.get_pressed()

            # Tính toán vị trí mới của người chơi
            new_x, new_y = self.player_pos[0], self.player_pos[1]
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and 0 <= self.player_pos[1] < self.MAZE_HEIGHT and 0 <= self.player_pos[0] - 1 < self.MAZE_WIDTH and self.maze[self.player_pos[1]][self.player_pos[0] - 1] == 0:
                new_x -= 1
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and 0 <= self.player_pos[1] < self.MAZE_HEIGHT and 0 <= self.player_pos[0] + 1 < self.MAZE_WIDTH and self.maze[self.player_pos[1]][self.player_pos[0] + 1] == 0:
                new_x += 1
            if (keys[pygame.K_UP] or keys[pygame.K_w]) and 0 <= self.player_pos[1] - 1 < self.MAZE_HEIGHT and 0 <= self.player_pos[0] < self.MAZE_WIDTH and self.maze[self.player_pos[1] - 1][self.player_pos[0]] == 0:
                new_y -= 1
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and 0 <= self.player_pos[1] + 1 < self.MAZE_HEIGHT and 0 <= self.player_pos[0] < self.MAZE_WIDTH and self.maze[self.player_pos[1] + 1][self.player_pos[0]] == 0:
                new_y += 1

            # Cập nhật vị trí người chơi
            if [new_x, new_y] != [self.player_pos[0], self.player_pos[1]]:
                self.player_pos[0], self.player_pos[1] = new_x, new_y
                self.player_rect.x = self.player_pos[0] * self.CELL_SIZE + (self.CELL_SIZE - self.PLAYER_SIZE) // 2
                self.player_rect.y = self.player_pos[1] * self.CELL_SIZE + (self.CELL_SIZE - self.PLAYER_SIZE) // 2

            # Cập nhật quái vật
            for enemy in self.enemies:
                enemy.move(self.player_pos)

            # Kiểm tra thắng
            if self.player_pos == self.goal_pos:
                print("Bạn đã thắng!")
                running = False

            # Vẽ lại màn hình
            self.screen.fill(self.WHITE)
            for y in range(len(self.maze)):
                for x in range(len(self.maze[y])):
                    if self.maze[y][x] == 1:
                        pygame.draw.rect(self.screen, self.BLACK, (x * self.CELL_SIZE, y * self.CELL_SIZE, self.CELL_SIZE, self.CELL_SIZE))
                    elif [x, y] == self.goal_pos:
                        pygame.draw.rect(self.screen, self.GREEN, (x * self.CELL_SIZE, y * self.CELL_SIZE, self.CELL_SIZE, self.CELL_SIZE))
            pygame.draw.rect(self.screen, self.RED, self.player_rect)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

            frame_count += 1
            # Kiểm tra xem game đã chạy ít nhất 60 khung hình chưa
            if frame_count >= 60:
                break

        # Kiểm tra xem game có chạy được không
        self.assertTrue(frame_count >= 60, "Game ran successfully for at least 60 frames")

    def tearDown(self):
        pygame.quit()

if __name__ == "__main__":
    unittest.main()