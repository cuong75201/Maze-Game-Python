import pygame
import sys
import os

# Tính đường dẫn tuyệt đối đến thư mục Maze-Game-Python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from bullet import Bullet
from config import load_image  # Import load_image từ config.py

class Player:
    def __init__(self, x, y, border_left, border_right, border_top, border_bottom, maze=None, image_path=None):
        print(f"Khởi tạo Player tại vị trí ({x}, {y})")
        
        # Lưu các giá trị biên và maze
        self.border_left = border_left
        self.border_right = border_right
        self.border_top = border_top
        self.border_bottom = border_bottom
        self.maze = maze  # Lưu đối tượng maze

        # Tải các frame hoạt ảnh từ 4 thư mục walkA, walkB, walkC, walkD
        self.walk_frames = {
            "right": [],  # walkB (phím D)
            "left": [],   # walkD (phím A)
            "up": [],     # walkC (phím W)
            "down": []    # walkA (phím S)
        }
        self.load_walk_frames()

        # Khởi tạo hình ảnh ban đầu với kích thước tile_size
        self.image = self.walk_frames["right"][0] if self.walk_frames["right"] else pygame.Surface(self.maze.tile_size)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
        self.bullets = 50
        self.bullet_list = []
        self.shoot_cooldown = 0
        self.direction = "right"
        self.frame_index = 0
        self.animation_speed = 0.2
        self.is_moving = False

        # Thuộc tính cho tính năng lộn người
        self.is_rolling = False
        self.roll_distance = 50
        self.roll_speed = 3.3
        self.roll_cooldown = 0
        self.roll_cooldown_max = 30
        self.roll_distance_moved = 0

        # Thuộc tính cho thanh máu
        self.health = 100  # Máu tối đa là 100
        self.max_health = 100
        self.health_bar_width = 40  # Chiều rộng thanh máu
        self.health_bar_height = 8  # Chiều cao thanh máu
        self.health_bar_offset = 10  # Khoảng cách từ đỉnh nhân vật đến thanh máu

    def load_walk_frames(self):
        tile_width, tile_height = self.maze.tile_size  # Sử dụng tile_size từ maze
        for i in range(16):
            # Tải frame cho walkA (xuống)
            walkA_path = f"hero/walkA/hero_walkA_{str(i).zfill(4)}.png"
            try:
                frame = load_image(walkA_path)  # Sử dụng load_image từ config.py
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["down"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkA_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["down"].append(frame)

            # Tải frame cho walkB (phải)
            walkB_path = f"hero/walkB/hero_walkB_{str(i).zfill(4)}.png"
            try:
                frame = load_image(walkB_path)
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["right"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkB_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["right"].append(frame)

            # Tải frame cho walkC (lên)
            walkC_path = f"hero/walkC/hero_walkC_{str(i).zfill(4)}.png"
            try:
                frame = load_image(walkC_path)
                frame = pygame.transform.scale(frame, (tile_width, tile_height))
                self.walk_frames["up"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkC_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["up"].append(frame)

            # Tải frame cho walkD (trái)
            walkD_path = f"hero/walkD/hero_walkD_{str(i).zfill(4)}.png"
            try:
                frame = load_image(walkD_path)
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

        # Kiểm tra va chạm với các ô gần nhân vật
        if moved and self.maze:
            player_tile_x = new_rect.centerx // self.maze.tile_size[0]
            player_tile_y = new_rect.centery // self.maze.tile_size[1]
            # Kiểm tra các ô lân cận (3x3 quanh nhân vật)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    tile_key = f"{player_tile_x + dx};{player_tile_y + dy}"
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
                                break
                if not moved:
                    break

        if moved:
            self.rect = new_rect

        # Giới hạn trong biên
        self.rect.x = max(self.border_left, min(self.rect.x, self.border_right - self.rect.width))
        self.rect.y = max(self.border_top, min(self.rect.y, self.border_bottom - self.rect.height))

        self.is_moving = moved
        if moved:
            self._update_image()

    def _roll(self):
        if self.direction == "up":
            self.rect.y -= self.roll_speed
        elif self.direction == "down":
            self.rect.y += self.roll_speed
        elif self.direction == "left":
            self.rect.x -= self.roll_speed
        elif self.direction == "right":
            self.rect.x += self.roll_speed

        self.roll_distance_moved += self.roll_speed

        # Sử dụng các giá trị biên đã được truyền vào
        self.rect.x = max(self.border_left, min(self.rect.x, self.border_right - self.rect.width))
        self.rect.y = max(self.border_top, min(self.rect.y, self.border_bottom - self.rect.height))

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

        # Giữ nguyên tâm của rect khi cập nhật hình ảnh
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
                image_path="bullet/bullet_1.png",  # Sửa thành bullet_1.png dựa trên cấu trúc thư mục
                direction=self.direction,
                border_left=self.border_left,
                border_right=self.border_right,
                border_top=self.border_top,
                border_bottom=self.border_bottom,
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

    def draw(self, screen):
        # Vẽ nhân vật
        screen.blit(self.image, self.rect)

        # Vẽ thanh máu nếu không đang lộn người
        if not self.is_rolling:
            health_ratio = self.health / self.max_health
            current_width = self.health_bar_width * health_ratio
            health_bar_x = self.rect.centerx - self.health_bar_width // 2
            health_bar_y = self.rect.top - self.health_bar_offset
            pygame.draw.rect(screen, (255, 0, 0), (health_bar_x, health_bar_y, current_width, self.health_bar_height))

        # Vẽ các viên đạn
        for bullet in self.bullet_list:
            bullet.draw(screen)