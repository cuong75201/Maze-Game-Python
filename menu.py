import sys
import os
import pygame
from config import load_image, load_images, config, save_config, load_config
from src.button import Button
from editor import Editor
from src.options import OptionsMenu
from src.game import main as run_game  # Import hàm main từ game.py

# Ngăn hiển thị thông báo hỗ trợ của Pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

class Menu:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()  # Khởi tạo mixer để phát âm thanh
        pygame.display.set_caption("Maze-Game with Enemies")
        self.screen = pygame.display.set_mode((960, 720))
        self.clock = pygame.time.Clock()
        self.display = pygame.Surface((320, 240))

        # Tải cấu hình
        load_config()
        
        # Hình nền
        self.background = load_image("background.png")
        
        # Tải nhạc nền
        try:
            self.background_music = pygame.mixer.Sound("assets/sounds/background_music.wav")
            self.background_music.set_volume(config.get('music_volume', 50) / 100.0)  # Chuyển đổi từ 0-100 sang 0.0-1.0
            self.background_music.play(-1)  # Phát lặp vô hạn
        except pygame.error as e:
            print(f"Không thể tải nhạc nền: {e}")
            self.background_music = None

        # Tải âm thanh súng cho nhấn nút
        try:
            self.button_click_sound = pygame.mixer.Sound("assets/sounds/gun_shot.wav")
            self.button_click_sound.set_volume(config.get('sfx_volume', 50) / 100.0)  # Chuyển đổi từ 0-100 sang 0.0-1.0
        except pygame.error as e:
            print(f"Không thể tải âm thanh súng: {e}")
            self.button_click_sound = None

        # Nút
        self.btn_play = Button(95, 155, load_image("button/PlayBtn.png"), load_image("button/PlayClick.png"), 0.08)
        self.btn_opt = Button(170, 155, load_image("button/OptBtn.png"), load_image("button/OptClick.png"), 0.08)

        self.editor = Editor()

    def start_game(self):
        """Chạy game.py trong cùng tiến trình"""
        # Lưu cấu hình hiện tại
        save_config()
        # Dừng nhạc nền trước khi chạy game
        if self.background_music:
            self.background_music.stop()
        try:
            # Gọi hàm main từ game.py
            run_game()
        except Exception as e:
            print(f"Lỗi khi chạy game.py: {e}")
            # Hiển thị thông báo lỗi trên màn hình
            error_font = pygame.font.SysFont('arial', 30)
            error_text = error_font.render("Lỗi: Không thể chạy trò chơi!", True, (255, 0, 0))
            self.screen.blit(error_text, (100, 300))
            pygame.display.flip()
            pygame.time.wait(2000)  # Hiển thị lỗi trong 2 giây
        finally:
            # Tải lại cấu hình
            load_config()
            # Đặt lại màn hình và hiển thị
            pygame.display.init()
            self.screen = pygame.display.set_mode((960, 720))
            pygame.display.set_caption("Maze-Game with Enemies")
            self.display = pygame.Surface((320, 240))
            # Phát lại nhạc nền với âm lượng mới
            if self.background_music:
                self.background_music.set_volume(config.get('music_volume', 50) / 100.0)
                self.background_music.play(-1)

    def run(self):
        running = True
        while running:
            self.display.blit(pygame.transform.scale(self.background, self.display.get_size()), (0, 0))
            
            # Xử lý nhấn nút
            if self.btn_play.draw(self.display, self.screen):
                if self.button_click_sound:
                    self.button_click_sound.play()
                self.start_game()
                # Đảm bảo hiển thị được đặt lại sau khi trò chơi kết thúc
                self.display = pygame.Surface((320, 240))
            
            if self.btn_opt.draw(self.display, self.screen):
                if self.button_click_sound:
                    self.button_click_sound.play()
                # Mở menu tùy chọn
                options_menu = OptionsMenu(config)
                options_menu.run()
                # Lưu các thay đổi cấu hình
                save_config()
                # Tải lại cấu hình
                load_config()
                # Cập nhật âm lượng nhạc nền và âm thanh nút
                if self.background_music:
                    self.background_music.set_volume(config.get('music_volume', 50) / 100.0)
                if self.button_click_sound:
                    self.button_click_sound.set_volume(config.get('sfx_volume', 50) / 100.0)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # Hiển thị menu
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

        # Dừng nhạc nền khi thoát
        if self.background_music:
            self.background_music.stop()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    Menu().run()