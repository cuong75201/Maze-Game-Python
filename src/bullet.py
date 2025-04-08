import pygame
import sys
import os

# Tính đường dẫn tuyệt đối đến thư mục Maze-Game-Python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import load_image  # Import load_image từ config.py

class Bullet:
    def __init__(self, x, y, image_path, direction, border_left, border_right, border_top, border_bottom, maze=None):
        try:
            self.image = load_image(image_path)  # Sử dụng load_image từ config.py
            self.image = pygame.transform.scale(self.image, (20, 20))  # Tăng kích thước đạn
        except pygame.error as e:
            print(f"Không thể tải hình ảnh đạn: {e}")
            self.image = pygame.Surface((20, 20))
            self.image.fill((255, 255, 0))

        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 10  # Tăng tốc độ đạn để phù hợp với kích thước lớn hơn
        self.border_left = border_left
        self.border_right = border_right
        self.border_top = border_top
        self.border_bottom = border_bottom
        self.maze = maze

    def move(self):
        if self.direction == "up":
            self.rect.y -= self.speed
        elif self.direction == "down":
            self.rect.y += self.speed
        elif self.direction == "left":
            self.rect.x -= self.speed
        elif self.direction == "right":
            self.rect.x += self.speed

        # Kiểm tra va chạm với tường
        if self.maze:
            for loc in self.maze.tilemap:
                tile = self.maze.tilemap[loc]
                if tile['type'] in ["WallStone", "WallBreakable"]:
                    tile_rect = pygame.Rect(
                        tile['pos'][0] * self.maze.tile_size[0],
                        tile['pos'][1] * self.maze.tile_size[1],
                        self.maze.tile_size[0],
                        tile.get('scale', self.maze.tile_size)[1]
                    )
                    if self.rect.colliderect(tile_rect):
                        return True  # Đạn va chạm với tường, sẽ bị xóa
        return False

    def should_remove(self):
        # Kiểm tra nếu đạn ra ngoài biên
        if (self.rect.right < self.border_left or
            self.rect.left > self.border_right or
            self.rect.bottom < self.border_top or
            self.rect.top > self.border_bottom):
            return True
        # Kiểm tra va chạm với tường
        return self.move()

    def draw(self, screen):
        screen.blit(self.image, self.rect)