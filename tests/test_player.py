import pygame
import os

class Player:
    def __init__(self, x, y):
        # Lấy đường dẫn đến thư mục gốc
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_path = os.path.join(BASE_DIR, "assets", "images", "test_avatar.png")
        
        # Load ảnh
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except Exception as e:
            print(f"Lỗi khi load ảnh: {e}")
            raise
        
        # Tạo rect cho nhân vật
        self.rect = self.image.get_rect(topleft=(x, y))
        self.bullets = []

    def move(self, keys, speed):
        if keys[pygame.K_w] and self.rect.y > 0:
            self.rect.y -= speed
        if keys[pygame.K_s] and self.rect.y < 600 - self.rect.height:
            self.rect.y += speed
        if keys[pygame.K_a] and self.rect.x > 0:
            self.rect.x -= speed
        if keys[pygame.K_d] and self.rect.x < 800 - self.rect.width:
            self.rect.x += speed