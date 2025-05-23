import pygame
import random
import math
import sys

class Enemy:
    ENEMY_TYPES = {
        "slime": {
            "image_path": "assets/images/enemy/slime_monster_preview.png",
            "hp": 30,
            "speed": 42,
            "size": (21, 21)
        },
        "skeleton": {
            "image_path": "assets/images/enemy/skeleton.png",
            "hp": 60,
            "speed": 56,
            "size": (32, 22)
        },
        "zombie": {
            "image_path": "assets/images/enemy/zombie.png",
            "hp": 90,
            "speed": 56,
            "size": (28, 28)
        },
        "ghost": {
            "image_path": "assets/images/enemy/ghost.png",
            "hp": 60,
            "speed": 35,
            "size": (25, 25)
        },
        "giant": {
            "image_path": "assets/images/enemy/giant.png",
            "hp": 180,
            "speed": 14,
            "size": (42, 49)
        }
    }

    def __init__(self, x, y, cell_size, maze_width, maze_height, maze, enemy_type):
        self.enemy_type = enemy_type
        self.cell_size = cell_size

        enemy_data = self.ENEMY_TYPES[enemy_type]
        try:
            self.image = pygame.image.load(enemy_data["image_path"]).convert_alpha()
        except pygame.error as e:
            print(f"Error loading image for {enemy_type}: {e}")
            pygame.quit()
            sys.exit(1)
        self.hp = enemy_data["hp"]
        self.speed = enemy_data["speed"]
        self.image = pygame.transform.scale(self.image, enemy_data["size"])

        self.original_image = self.image
        self.facing_right = True

        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))

        self.exclamation_mark = pygame.image.load("assets/images/enemy/exclamation_mark.png").convert_alpha()
        self.exclamation_mark = pygame.transform.scale(self.exclamation_mark, (18, 18))
        self.show_exclamation = False

        self.bounce_offset = 0
        self.bounce_speed = 0.05
        self.bounce_amplitude = 3
        self.bounce_timer = 0

        if enemy_type == "ghost":
            self.is_visible = True
            self.visibility_timer = pygame.time.get_ticks()
            self.visibility_interval = 5000
            self.magic_image = pygame.image.load("assets/images/enemy/magic.png").convert_alpha()
            self.magic_image = pygame.transform.scale(self.magic_image, (20, 16))
            self.projectiles = []
            self.last_attack = 0
            self.attack_delay = 3000
        else:
            self.is_visible = True
            self.visibility_timer = 0
            self.visibility_interval = 0

        if enemy_type == "skeleton":
            self.sword_image = pygame.image.load("assets/images/enemy/sword.png").convert_alpha()
            self.sword_image = pygame.transform.scale(self.sword_image, (18, 14))
            self.projectiles = []
            self.last_attack = 0
            self.attack_delay = 3000

        if enemy_type == "giant":
            self.shockwave = None
            self.stomp_warning = None
            self.last_stomp = 0
            self.stomp_delay = 5000
            self.warning_duration = 60
            try:
                self.shockwave_image = pygame.image.load("assets/images/enemy/shockwave.png").convert_alpha()
                self.shockwave_image = pygame.transform.scale(self.shockwave_image, (140, 140))
            except pygame.error as e:
                print(f"Error loading shockwave image: {e}")
                self.shockwave_image = None

        self.particles = []

        self.maze_width = maze_width
        self.maze_height = maze_height
        self.maze = maze
        self.vision_range = 16.5 * cell_size
        self.base_speed = self.speed

        # Biến để hỗ trợ patrol
        self.patrol_direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])  # Hướng ban đầu ngẫu nhiên
        self.patrol_timer = 0
        self.patrol_duration = random.randint(60, 120)  # Thời gian di chuyển theo một hướng (1-2 giây)

    def update_visibility(self):
        if self.enemy_type == "ghost":
            current_time = pygame.time.get_ticks()
            if current_time - self.visibility_timer >= self.visibility_interval:
                self.is_visible = not self.is_visible
                self.visibility_timer = current_time
                print(f"Ghost visibility: {self.is_visible}")

    def update_bounce(self):
        self.bounce_timer += self.bounce_speed
        self.bounce_offset = math.sin(self.bounce_timer) * self.bounce_amplitude

    def create_particles(self, x, y, color):
        num_particles = random.randint(5, 10)
        for _ in range(num_particles):
            particle = {
                "pos": [x, y],
                "velocity": [random.uniform(-2, 2), random.uniform(-2, 2)],
                "radius": random.randint(2, 4),
                "color": color,
                "lifetime": 30
            }
            self.particles.append(particle)

    def update_particles(self):
        for particle in self.particles[:]:
            particle["pos"][0] += particle["velocity"][0]
            particle["pos"][1] += particle["velocity"][1]
            particle["lifetime"] -= 1
            particle["velocity"][0] *= 0.95
            particle["velocity"][1] *= 0.95
            if particle["lifetime"] <= 0:
                self.particles.remove(particle)

    def stomp(self, player_pos):
        if self.enemy_type != "giant":
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.last_stomp >= self.stomp_delay:
            dx = player_pos[1] * self.cell_size - self.rect.x
            dy = player_pos[0] * self.cell_size - self.rect.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance <= self.vision_range and not self.stomp_warning:
                self.stomp_warning = {
                    "center": (self.rect.centerx, self.rect.centery),
                    "radius": 105,
                    "lifetime": self.warning_duration
                }
                self.last_stomp = current_time

    def update_stomp_warning(self):
        if self.enemy_type != "giant" or not self.stomp_warning:
            return

        self.stomp_warning["lifetime"] -= 1
        if self.stomp_warning["lifetime"] <= 0:
            self.shockwave = {
                "center": (self.rect.centerx, self.rect.centery),
                "radius": 0,
                "max_radius": 105,
                "lifetime": 60
            }
            self.create_particles(self.rect.centerx, self.rect.centery, (128, 128, 128))
            self.stomp_warning = None

    def update_shockwave(self):
        if self.enemy_type != "giant" or not self.shockwave:
            return

        self.shockwave["radius"] += self.shockwave["max_radius"] / self.shockwave["lifetime"]
        if self.shockwave["radius"] > self.shockwave["max_radius"]:
            self.shockwave["radius"] = self.shockwave["max_radius"]
        self.shockwave["lifetime"] -= 1
        if self.shockwave["lifetime"] <= 0:
            self.shockwave = None

    def attack(self, player_rect):
        if self.enemy_type == "skeleton":
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack >= self.attack_delay:
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                distance = math.sqrt(dx**2 + dy**2)
                if distance <= self.vision_range:
                    direction_x = dx / distance if distance != 0 else 0
                    direction_y = dy / distance if distance != 0 else 0
                    projectile = {
                        "rect": pygame.Rect(self.rect.centerx, self.rect.centery, 14, 7),
                        "direction": (direction_x, direction_y),
                        "speed": 120,
                        "rotation_angle": 0,
                        "rotation_speed": 10
                    }
                    self.projectiles.append(projectile)
                    self.create_particles(self.rect.centerx, self.rect.centery, (255, 0, 0))
                    self.last_attack = current_time
        elif self.enemy_type == "ghost" and self.is_visible:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack >= self.attack_delay:
                dx = player_rect.centerx - self.rect.centerx
                dy = player_rect.centery - self.rect.centery
                distance = math.sqrt(dx**2 + dy**2)
                if distance <= self.vision_range:
                    direction_x = dx / distance if distance != 0 else 0
                    direction_y = dy / distance if distance != 0 else 0
                    projectile = {
                        "rect": pygame.Rect(self.rect.centerx, self.rect.centery, 14, 14),
                        "direction": (direction_x, direction_y),
                        "speed": 120,
                        "rotation_angle": 0,
                        "rotation_speed": 10
                    }
                    self.projectiles.append(projectile)
                    self.create_particles(self.rect.centerx, self.rect.centery, (128, 0, 128))
                    self.last_attack = current_time

    def update_projectiles(self):
        if self.enemy_type == "skeleton":
            for projectile in self.projectiles[:]:
                projectile["rect"].x += projectile["direction"][0] * (projectile["speed"] * 1/60)
                projectile["rect"].y += projectile["direction"][1] * (projectile["speed"] * 1/60)
                projectile["rotation_angle"] += projectile["rotation_speed"]
                if (projectile["rect"].x < 0 or projectile["rect"].x > 900 or
                    projectile["rect"].y < 0 or projectile["rect"].y > 900):
                    self.projectiles.remove(projectile)
        elif self.enemy_type == "ghost":
            for projectile in self.projectiles[:]:
                projectile["rect"].x += projectile["direction"][0] * (projectile["speed"] * 1/60)
                projectile["rect"].y += projectile["direction"][1] * (projectile["speed"] * 1/60)
                projectile["rotation_angle"] += projectile["rotation_speed"]
                if (projectile["rect"].x < 0 or projectile["rect"].x > 900 or
                    projectile["rect"].y < 0 or projectile["rect"].y > 900):
                    self.projectiles.remove(projectile)

    def is_position_valid(self, x, y):
        grid_x = int(x // self.cell_size)
        grid_y = int(y // self.cell_size)
        if not (0 <= grid_y < self.maze_height and 0 <= grid_x < self.maze_width):
            return False
        return self.maze[grid_y][grid_x] == 0

    def on_maze_changed(self):
        current_grid_x = int(self.rect.x // self.cell_size)
        current_grid_y = int(self.rect.y // self.cell_size)
        if (0 <= current_grid_y < self.maze_height and 0 <= current_grid_x < self.maze_width and
                self.maze[current_grid_y][current_grid_x] == 1):
            print(f"Enemy {self.enemy_type} stuck after maze change at ({self.rect.x}, {self.rect.y})")

    def move(self, player_pos, player_rect, dt=1/60):
        # Tính khoảng cách trực tiếp bằng pixel (dùng player_rect thay vì player_pos)
        dx = self.rect.centerx - player_rect.centerx
        dy = self.rect.centery - player_rect.centery
        distance_to_player_px = math.sqrt(dx**2 + dy**2)

        # Cập nhật trạng thái đuổi theo
        if distance_to_player_px <= self.vision_range:
            self.show_exclamation = True
            self.speed = self.base_speed * 1.2  # Tốc độ khi đuổi theo
        else:
            self.show_exclamation = False
            self.speed = self.base_speed

        self.update_visibility()
        self.update_bounce()
        self.attack(player_rect)  # Sử dụng player_rect thay vì player_pos
        self.stomp(player_pos)
        self.update_projectiles()
        self.update_particles()
        self.update_stomp_warning()
        self.update_shockwave()

        # Logic di chuyển (chạy mỗi frame)
        speed_per_frame = self.speed * dt  # Tốc độ mỗi frame, dựa trên dt

        if distance_to_player_px <= self.vision_range:
            # Đuổi theo người chơi: di chuyển trực tiếp về phía người chơi
            if distance_to_player_px > 0:  # Chỉ cần đảm bảo không chia cho 0
                # Chuẩn hóa vector hướng
                direction_x = dx / distance_to_player_px
                direction_y = dy / distance_to_player_px

                # Tính vị trí mới
                new_x = self.rect.x - direction_x * speed_per_frame
                new_y = self.rect.y - direction_y * speed_per_frame

                # Nếu rất gần người chơi, kiểm tra va chạm trực tiếp
                temp_rect = self.rect.copy()
                temp_rect.x = new_x
                temp_rect.y = new_y
                if temp_rect.colliderect(player_rect):
                    # Nếu va chạm với người chơi, không cần di chuyển thêm
                    # Va chạm sẽ được xử lý trong game.py
                    pass
                elif distance_to_player_px <= self.rect.width:  # Nếu rất gần (trong vòng 1 ô)
                    # Di chuyển trực tiếp mà không kiểm tra tường
                    self.rect.x = new_x
                    self.rect.y = new_y
                else:
                    # Kiểm tra vị trí mới có hợp lệ không
                    if self.is_position_valid(new_x, new_y):
                        self.rect.x = new_x
                        self.rect.y = new_y
                    else:
                        # Thử trượt dọc theo tường
                        # Di chuyển theo trục x
                        temp_x = self.rect.x - direction_x * speed_per_frame
                        if self.is_position_valid(temp_x, self.rect.y):
                            self.rect.x = temp_x
                        # Di chuyển theo trục y
                        temp_y = self.rect.y - direction_y * speed_per_frame
                        if self.is_position_valid(self.rect.x, temp_y):
                            self.rect.y = temp_y

                # Cập nhật hướng quay mặt
                if direction_x > 0:
                    self.facing_right = False
                    self.image = pygame.transform.flip(self.original_image, True, False)
                elif direction_x < 0:
                    self.facing_right = True
                    self.image = self.original_image
        else:
            # Patrol: di chuyển qua lại
            self.patrol_timer += 1
            if self.patrol_timer >= self.patrol_duration:
                # Chọn hướng mới ngẫu nhiên sau khi hết thời gian
                self.patrol_direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                self.patrol_timer = 0
                self.patrol_duration = random.randint(60, 120)

            # Di chuyển theo hướng patrol
            dx, dy = self.patrol_direction
            new_x = self.rect.x + dx * speed_per_frame
            new_y = self.rect.y + dy * speed_per_frame

            # Kiểm tra vị trí mới có hợp lệ không
            if self.is_position_valid(new_x, new_y):
                self.rect.x = new_x
                self.rect.y = new_y
                # Cập nhật hướng quay mặt
                if dx > 0:
                    self.facing_right = True
                    self.image = self.original_image
                elif dx < 0:
                    self.facing_right = False
                    self.image = pygame.transform.flip(self.original_image, True, False)
            else:
                # Nếu va chạm tường, đảo hướng patrol
                self.patrol_direction = (-dx, -dy)
                self.patrol_timer = 0  # Reset timer để tránh lặp lại ngay lập tức

    def draw(self, screen, offset=(0, 0)):
        if self.is_visible:
            draw_rect = self.rect.copy()
            draw_rect.x -= offset[0]
            draw_rect.y -= offset[1] + self.bounce_offset
            screen.blit(self.image, draw_rect)
            if self.show_exclamation:
                exclamation_pos = (
                    draw_rect.centerx - self.exclamation_mark.get_width() // 2,
                    draw_rect.top - self.exclamation_mark.get_height()
                )
                screen.blit(self.exclamation_mark, exclamation_pos)
            if self.enemy_type == "skeleton":
                for projectile in self.projectiles:
                    rotated_sword = pygame.transform.rotate(self.sword_image, projectile["rotation_angle"])
                    rotated_rect = rotated_sword.get_rect(center=projectile["rect"].center)
                    rotated_rect.x -= offset[0]
                    rotated_rect.y -= offset[1]
                    screen.blit(rotated_sword, rotated_rect)
            elif self.enemy_type == "ghost":
                for projectile in self.projectiles:
                    rotated_magic = pygame.transform.rotate(self.magic_image, projectile["rotation_angle"])
                    rotated_rect = rotated_magic.get_rect(center=projectile["rect"].center)
                    rotated_rect.x -= offset[0]
                    rotated_rect.y -= offset[1]
                    screen.blit(rotated_magic, rotated_rect)
            elif self.enemy_type == "giant":
                if self.stomp_warning:
                    alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.01))
                    pygame.draw.circle(screen, (255, 0, 0, alpha),
                                      (self.stomp_warning["center"][0] - offset[0],
                                       self.stomp_warning["center"][1] - offset[1]),
                                      int(self.stomp_warning["radius"]), 5)
                if self.shockwave and self.shockwave_image:
                    scale = (self.shockwave["radius"] * 2) / 210
                    if scale > 1:
                        scale = 1
                    scaled_image = pygame.transform.scale(self.shockwave_image,
                                                         (int(210 * scale), int(210 * scale)))
                    alpha = int(255 * (self.shockwave["lifetime"] / 60))
                    scaled_image.set_alpha(alpha)
                    image_rect = scaled_image.get_rect(center=self.shockwave["center"])
                    image_rect.x -= offset[0]
                    image_rect.y -= offset[1]
                    screen.blit(scaled_image, image_rect)
            for particle in self.particles:
                pygame.draw.circle(screen, particle["color"],
                                  (int(particle["pos"][0] - offset[0]),
                                   int(particle["pos"][1] - offset[1])),
                                  particle["radius"])