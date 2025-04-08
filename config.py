import pygame
import os

# Lấy đường dẫn thư mục chứa config.py (thư mục cha của src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Tạo đường dẫn đến thư mục assets/images
BASE_IMG_PATH = os.path.join(BASE_DIR, 'assets', 'images') + os.sep

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img

def load_images(path):
    images = []
    full_path = os.path.join(BASE_IMG_PATH, path)
    for img_name in os.listdir(full_path):
        # Chuyển tên file về chữ thường để so sánh
        img_name_lower = img_name.lower()
        # Chỉ tải các file có đuôi .png
        if img_name_lower.endswith('.png'):
            images.append(load_image(os.path.join(path, img_name)))
    return images