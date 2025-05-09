import pygame
import sys
from config import load_image

def draw_text_outline(surface, text, font, pos, text_color, outline_color, outline_width=2):
    base = font.render(text, True, text_color)
    x, y = pos
    for dx in [-outline_width, 0, outline_width]:
        for dy in [-outline_width, 0, outline_width]:
            if dx != 0 or dy != 0:
                outline = font.render(text, True, outline_color)
                surface.blit(outline, (x+dx, y+dy))
    surface.blit(base, pos)

class OptionsMenu:
    def __init__(self, config):
        pygame.init()
        self.screen = pygame.display.set_mode((960, 720))
        pygame.display.set_caption("Maze Shooter Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('arial', 40, bold=True)
        self.config = config
        self.background = load_image("background.png")
        # Layout constants
        self.label_x = 180
        self.input_y = 120
        self.slider1_y = 220
        self.slider2_y = 320
        self.speed_y = 470
        self.label_width = 260
        self.slider_width = 300
        self.slider_height = 16
        self.input_box = pygame.Rect(self.label_x + self.label_width, self.input_y, 300, 50)
        self.input_active = False
        self.name = config.get('player_name', 'Player')
        self.edit_btn = pygame.Rect(self.input_box.right + 20, self.input_box.y + (self.input_box.height - 50)//2, 80, 50)
        self.editing = False
        self.speed_choices = [0.5, 1, 1.5, 2]
        speed_idx = 1
        if 'game_speed' in config and config['game_speed'] in self.speed_choices:
            speed_idx = self.speed_choices.index(config['game_speed'])
        self.sliders = [
            ["Music Volume", 0, 100, config.get('music_volume', 50), pygame.Rect(self.label_x + self.label_width, self.slider1_y, self.slider_width, self.slider_height)],
            ["SFX Volume", 0, 100, config.get('sfx_volume', 50), pygame.Rect(self.label_x + self.label_width, self.slider2_y, self.slider_width, self.slider_height)],
        ]
        self.speed_idx = speed_idx
        self.selected_slider = None
        self.running = True

    def draw_slider(self, label, minv, maxv, value, rect, y):
        # Label
        draw_text_outline(self.screen, label, self.font, (self.label_x, y-10), (0,0,0), (255,255,255))
        # Slider
        pygame.draw.rect(self.screen, (180,180,180), rect)
        pos = int((value-minv)/(maxv-minv)*rect.width)
        pygame.draw.rect(self.screen, (50,150,255), (rect.x, rect.y, pos, rect.height))
        pygame.draw.circle(self.screen, (0,0,0), (rect.x+pos, rect.y+rect.height//2), 12)
        # Value (number) bên phải slider, cách slider 30px
        value_txt = self.font.render(str(value), True, (0,0,0))
        value_rect = value_txt.get_rect(midleft=(rect.right+30, rect.y+rect.height//2))
        self.screen.blit(value_txt, value_rect)

    def draw_speed_selector(self):
        # Label
        draw_text_outline(self.screen, "Game Speed:", self.font, (self.label_x, self.speed_y-25), (0,0,0), (255,255,255))
        # Các số selector bắt đầu ngay sau label, thẳng hàng với label
        start_x = self.label_x + self.label_width + 40
        y = self.speed_y
        for i, val in enumerate(self.speed_choices):
            x = start_x + i*120
            color = (0,200,0) if i == self.speed_idx else (180,180,180)
            pygame.draw.circle(self.screen, color, (x, y), 30)
            txt = self.font.render(str(val), True, (0,0,0))
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def run(self):
        while self.running:
            # Draw background and overlay
            self.screen.blit(pygame.transform.scale(self.background, self.screen.get_size()), (0, 0))
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((255,255,255, 180))
            self.screen.blit(overlay, (0,0))
            # Player Name label
            draw_text_outline(self.screen, "Player Name:", self.font, (self.label_x, self.input_y+5), (0,0,0), (255,255,255))
            # Input box (no fill, no border)
            if self.editing:
                pygame.draw.rect(self.screen, (0,0,0), self.input_box, 2)
            name_txt = self.font.render(self.name, True, (0,0,0))
            self.screen.blit(name_txt, (self.input_box.x+5, self.input_box.y+5))
            # Edit/Save button (centered vertically)
            pygame.draw.rect(self.screen, (0,150,255), self.edit_btn, border_radius=8)
            btn_label = "Save" if self.editing else "Edit"
            edit_txt = self.font.render(btn_label, True, (255,255,255))
            edit_txt_rect = edit_txt.get_rect(center=self.edit_btn.center)
            self.screen.blit(edit_txt, edit_txt_rect)
            # Sliders
            self.draw_slider("Music Volume", 0, 100, self.sliders[0][3], self.sliders[0][4], self.slider1_y)
            self.draw_slider("SFX Volume", 0, 100, self.sliders[1][3], self.sliders[1][4], self.slider2_y)
            # Speed selector
            self.draw_speed_selector()
            # Save button (centered)
            save_btn = pygame.Rect(430, 600, 120, 60)
            pygame.draw.rect(self.screen, (0,200,0), save_btn, border_radius=12)
            save_txt = self.font.render("Save", True, (255,255,255))
            save_txt_rect = save_txt.get_rect(center=save_btn.center)
            self.screen.blit(save_txt, save_txt_rect)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Nhấn Edit/Save hoặc click vào input box đều cho phép nhập
                    if self.edit_btn.collidepoint(event.pos) or self.input_box.collidepoint(event.pos):
                        if self.editing:
                            self.input_active = False
                            self.editing = False
                        else:
                            self.input_active = True
                            self.editing = True
                    else:
                        self.input_active = False
                    for i, (_,_,_,_,rect) in enumerate(self.sliders):
                        if rect.collidepoint(event.pos):
                            self.selected_slider = i
                    # Game speed selector
                    start_x = self.label_x + self.label_width + 40
                    y = self.speed_y
                    for i, val in enumerate(self.speed_choices):
                        x = start_x + i*120
                        if (event.pos[0]-x)**2 + (event.pos[1]-y)**2 <= 30**2:
                            self.speed_idx = i
                    if save_btn.collidepoint(event.pos):
                        self.config['player_name'] = self.name
                        self.config['music_volume'] = self.sliders[0][3]
                        self.config['sfx_volume'] = self.sliders[1][3]
                        self.config['game_speed'] = self.speed_choices[self.speed_idx]
                        self.running = False
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.selected_slider = None
                elif event.type == pygame.MOUSEMOTION and self.selected_slider is not None:
                    label, minv, maxv, value, rect = self.sliders[self.selected_slider]
                    rel_x = event.pos[0] - rect.x
                    rel_x = max(0, min(rect.width, rel_x))
                    new_value = int(minv + (maxv-minv)*rel_x/rect.width)
                    self.sliders[self.selected_slider][3] = new_value
                elif event.type == pygame.KEYDOWN and self.editing:
                    if event.key == pygame.K_BACKSPACE:
                        self.name = self.name[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.input_active = False
                        self.editing = False
                    else:
                        if len(self.name) < 16:
                            self.name += event.unicode
            pygame.display.flip()
            self.clock.tick(60) 