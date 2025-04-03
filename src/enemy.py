import pygame
import random
import math
import sys

class Enemy:
    ENEMY_TYPES = {
        "slime": {
            "image_path": "assets/images/slime_monster_preview.png",
            "hp": 6,
            "speed": 60,
            "size": (30, 30)
        },
        "skeleton": {
            "image_path": "assets/images/skeleton.png",
            "hp": 10,
            "speed": 80,
            "size": (45, 32)
        },
        "zombie": {
            "image_path": "assets/images/zombie.png",
            "hp": 10,
            "speed": 80,
            "size": (40, 40)
        },
        "ghost": {
            "image_path": "assets/images/ghost.png",
            "hp": 8,
            "speed": 50,
            "size": (35, 35)
        },
        "giant": {
            "image_path": "assets/images/giant.png",
            "hp": 50,
            "speed": 20,
            "size": (60, 70)
        }
    }

    def __init__(self, x, y, cell_size, maze_width, maze_height, maze, enemy_type):
        self.enemy_type = enemy_type
        self.cell_size = cell_size

        # Tải hình ảnh và thuộc tính từ dictionary
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

        # Lưu hình ảnh gốc để lật
        self.original_image = self.image
        self.facing_right = True

        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))

        # Tải hình ảnh "dấu chấm than"
        self.exclamation_mark = pygame.image.load("assets/images/exclamation_mark.png").convert_alpha()
        self.exclamation_mark = pygame.transform.scale(self.exclamation_mark, (25, 25))
        self.show_exclamation = False

        # Hiệu ứng nảy
        self.bounce_offset = 0
        self.bounce_speed = 0.05
        self.bounce_amplitude = 3
        self.bounce_timer = 0

        # Khả năng tàng hình cho Ghost
        if enemy_type == "ghost":
            self.is_visible = True
            self.visibility_timer = pygame.time.get_ticks()
            self.visibility_interval = 5000
            self.magic_image = pygame.image.load("assets/images/magic.png").convert_alpha()
            self.magic_image = pygame.transform.scale(self.magic_image, (20, 20))
            self.projectiles = []
            self.last_attack = 0
            self.attack_delay = 3000
        else:
            self.is_visible = True
            self.visibility_timer = 0
            self.visibility_interval = 0

        # Khả năng phi kiếm cho Skeleton
        if enemy_type == "skeleton":
            self.sword_image = pygame.image.load("assets/images/sword.png").convert_alpha()
            self.sword_image = pygame.transform.scale(self.sword_image, (25, 20))
            self.projectiles = []
            self.last_attack = 0
            self.attack_delay = 3000

        # Khả năng dậm đất cho Giant (Boss)
        if enemy_type == "giant":
            self.shockwave = None
            self.stomp_warning = None
            self.last_stomp = 0
            self.stomp_delay = 5000
            self.warning_duration = 60
            # Tải hình ảnh PNG cho sóng xung kích
            try:
                self.shockwave_image = pygame.image.load("assets/images/shockwave.png").convert_alpha()
                self.shockwave_image = pygame.transform.scale(self.shockwave_image, (200, 200))
            except pygame.error as e:
                print(f"Error loading shockwave image: {e}")
                self.shockwave_image = None

        # Danh sách hạt (particles) cho hiệu ứng
        self.particles = []

        self.last_move = 0
        self.move_delay = 500
        self.maze_width = maze_width
        self.maze_height = maze_height
        self.maze = maze
        self.vision_range = 5 * cell_size
        self.base_speed = self.speed
        self.target_pos = None
        self.current_grid_pos = (y, x)

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
            dx = player_pos[0] * self.cell_size - self.rect.x
            dy = player_pos[1] * self.cell_size - self.rect.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance <= self.vision_range and not self.stomp_warning:
                self.stomp_warning = {
                    "center": (self.rect.centerx, self.rect.centery),
                    "radius": 150,  # Tăng bán kính vùng đỏ từ 100 lên 150
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
                "max_radius": 150,  # Tăng bán kính tối đa của sóng xung kích từ 100 lên 150
                "lifetime": 60
            }
            self.create_particles(self.rect.centerx, self.rect.centery, (128, 128, 128))
            self.stomp_warning = None

    def update_shockwave(self):
        if self.enemy_type != "giant" or not self.shockwave:
            return

        self.shockwave["radius"] += self.shockwave["max_radius"] / self.shockwave["lifetime"]
        # Giới hạn radius không vượt quá max_radius
        if self.shockwave["radius"] > self.shockwave["max_radius"]:
            self.shockwave["radius"] = self.shockwave["max_radius"]
        self.shockwave["lifetime"] -= 1
        if self.shockwave["lifetime"] <= 0:
            self.shockwave = None

    def attack(self, player_pos):
        if self.enemy_type == "skeleton":
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack >= self.attack_delay:
                dx = player_pos[0] * self.cell_size - self.rect.x
                dy = player_pos[1] * self.cell_size - self.rect.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance <= self.vision_range:
                    direction_x = dx / distance if distance != 0 else 0
                    direction_y = dy / distance if distance != 0 else 0
                    projectile = {
                        "rect": pygame.Rect(self.rect.centerx, self.rect.centery, 20, 10),
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
                dx = player_pos[0] * self.cell_size - self.rect.x
                dy = player_pos[1] * self.cell_size - self.rect.y
                distance = math.sqrt(dx**2 + dy**2)
                if distance <= self.vision_range:
                    direction_x = dx / distance if distance != 0 else 0
                    direction_y = dy / distance if distance != 0 else 0
                    projectile = {
                        "rect": pygame.Rect(self.rect.centerx, self.rect.centery, 20, 20),
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
                projectile["rect"].x += projectile["direction"][0] * (projectile["speed"] / 60)
                projectile["rect"].y += projectile["direction"][1] * (projectile["speed"] / 60)
                projectile["rotation_angle"] += projectile["rotation_speed"]
                if (projectile["rect"].x < 0 or projectile["rect"].x > 900 or
                    projectile["rect"].y < 0 or projectile["rect"].y > 900):
                    self.projectiles.remove(projectile)
        elif self.enemy_type == "ghost":
            for projectile in self.projectiles[:]:
                projectile["rect"].x += projectile["direction"][0] * (projectile["speed"] / 60)
                projectile["rect"].y += projectile["direction"][1] * (projectile["speed"] / 60)
                projectile["rotation_angle"] += projectile["rotation_speed"]
                if (projectile["rect"].x < 0 or projectile["rect"].x > 900 or
                    projectile["rect"].y < 0 or projectile["rect"].y > 900):
                    self.projectiles.remove(projectile)

    def move(self, player_pos, player_rect):
        current_time = pygame.time.get_ticks()
        enemy_grid_pos = (self.rect.y // self.cell_size, self.rect.x // self.cell_size)
        player_grid_pos = (player_rect.y // self.cell_size, player_rect.x // self.cell_size)

        dx = self.rect.x - player_rect.x
        dy = self.rect.y - player_rect.y
        distance_to_player_px = math.sqrt(dx**2 + dy**2)

        print(f"Enemy ({self.enemy_type}) pos: {enemy_grid_pos}, Player pos: {player_grid_pos}, Distance (px): {distance_to_player_px:.2f}, Speed: {self.speed}, Delay: {self.move_delay}")

        if distance_to_player_px <= self.vision_range:
            self.show_exclamation = True
            self.speed = self.base_speed * 0.5 if self.enemy_type == "skeleton" else self.base_speed * 1.5
            self.move_delay = 60
        else:
            self.show_exclamation = False
            self.speed = self.base_speed
            self.move_delay = 500

        self.update_visibility()
        self.update_bounce()
        self.attack(player_pos)
        self.stomp(player_pos)
        self.update_projectiles()
        self.update_particles()
        self.update_stomp_warning()
        self.update_shockwave()

        if self.target_pos:
            dx = self.target_pos[0] - self.rect.x
            dy = self.target_pos[1] - self.rect.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 1:
                speed_per_frame = self.speed / 60
                if distance <= speed_per_frame:
                    self.rect.x = self.target_pos[0]
                    self.rect.y = self.target_pos[1]
                    self.current_grid_pos = (self.rect.y // self.cell_size, self.rect.x // self.cell_size)
                    self.target_pos = None
                else:
                    direction_x = dx / distance
                    direction_y = dy / distance
                    self.rect.x += direction_x * speed_per_frame
                    self.rect.y += direction_y * speed_per_frame
                    if direction_x > 0:
                        self.facing_right = True
                        self.image = self.original_image
                    elif direction_x < 0:
                        self.facing_right = False
                        self.image = pygame.transform.flip(self.original_image, True, False)
            else:
                self.rect.x = self.target_pos[0]
                self.rect.y = self.target_pos[1]
                self.current_grid_pos = (self.rect.y // self.cell_size, self.rect.x // self.cell_size)
                self.target_pos = None

        if self.target_pos is None and current_time - self.last_move >= self.move_delay:
            self.last_move = current_time

            if self.enemy_type == "skeleton":
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
            else:
                if distance_to_player_px <= self.vision_range:
                    directions = []
                    if player_grid_pos[1] < enemy_grid_pos[1]:
                        directions.append((-1, 0))
                    elif player_grid_pos[1] > enemy_grid_pos[1]:
                        directions.append((1, 0))
                    if player_grid_pos[0] < enemy_grid_pos[0]:
                        directions.append((0, -1))
                    elif player_grid_pos[0] > enemy_grid_pos[0]:
                        directions.append((0, 1))
                    all_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    for direction in all_directions:
                        if direction not in directions:
                            directions.append(direction)
                else:
                    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    random.shuffle(directions)

            moved = False
            new_grid_x, new_grid_y = enemy_grid_pos[1], enemy_grid_pos[0]

            for dx, dy in directions:
                next_x, next_y = enemy_grid_pos[1] + dx, enemy_grid_pos[0] + dy
                if (0 <= next_y < self.maze_height and 0 <= next_x < self.maze_width and
                        self.maze[next_y][next_x] == 0):
                    new_grid_x, new_grid_y = next_x, next_y
                    moved = True
                    break

            if moved:
                self.target_pos = (new_grid_x * self.cell_size, new_grid_y * self.cell_size)
                print(f"Enemy ({self.enemy_type}) moving to: ({new_grid_x}, {new_grid_y})")
            else:
                print(f"Enemy ({self.enemy_type}) cannot move: no valid direction available")

    def draw(self, screen):
        if self.is_visible:
            draw_rect = self.rect.copy()
            draw_rect.y += self.bounce_offset
            screen.blit(self.image, draw_rect)
            if self.show_exclamation:
                exclamation_pos = (draw_rect.centerx - self.exclamation_mark.get_width() // 2, 
                                  draw_rect.top - self.exclamation_mark.get_height())
                screen.blit(self.exclamation_mark, exclamation_pos)
            # Vẽ thanh kiếm của Skeleton
            if self.enemy_type == "skeleton":
                for projectile in self.projectiles:
                    rotated_sword = pygame.transform.rotate(self.sword_image, projectile["rotation_angle"])
                    rotated_rect = rotated_sword.get_rect(center=projectile["rect"].center)
                    screen.blit(rotated_sword, rotated_rect)
            # Vẽ magic của Ghost
            elif self.enemy_type == "ghost":
                for projectile in self.projectiles:
                    rotated_magic = pygame.transform.rotate(self.magic_image, projectile["rotation_angle"])
                    rotated_rect = rotated_magic.get_rect(center=projectile["rect"].center)
                    screen.blit(rotated_magic, rotated_rect)
            # Vẽ cảnh báo và sóng xung kích của Giant
            elif self.enemy_type == "giant":
                # Vẽ cảnh báo (vòng tròn đỏ nhấp nháy)
                if self.stomp_warning:
                    alpha = 128 + int(127 * math.sin(pygame.time.get_ticks() * 0.01))
                    pygame.draw.circle(screen, (255, 0, 0, alpha), 
                                     self.stomp_warning["center"], 
                                     int(self.stomp_warning["radius"]), 5)
                # Vẽ sóng xung kích
                if self.shockwave:
                    if self.shockwave_image:
                        # Tính tỷ lệ scale dựa trên bán kính hiện tại
                        scale = (self.shockwave["radius"] * 2) / 300  # Điều chỉnh để đường kính tối đa là 300 pixel
                        # Giới hạn scale không vượt quá 1 (đảm bảo kích thước tối đa là 300x300 pixel)
                        if scale > 1:
                            scale = 1
                        scaled_image = pygame.transform.scale(self.shockwave_image, 
                                                            (int(300 * scale), int(300 * scale)))  # Đường kính tối đa 300 pixel
                        # Tạo hiệu ứng mờ dần
                        alpha = int(255 * (self.shockwave["lifetime"] / 60))
                        scaled_image.set_alpha(alpha)
                        image_rect = scaled_image.get_rect(center=self.shockwave["center"])
                        screen.blit(scaled_image, image_rect)
                    else:
                        pygame.draw.circle(screen, (128, 128, 128, 128), 
                                         self.shockwave["center"], 
                                         int(self.shockwave["radius"]), 5)
            # Vẽ các hạt
            for particle in self.particles:
                pygame.draw.circle(screen, particle["color"], 
                                 (int(particle["pos"][0]), int(particle["pos"][1])), 
                                 particle["radius"])