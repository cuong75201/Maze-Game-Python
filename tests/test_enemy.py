import pygame
import random
import math
import sys
from heapq import heappush, heappop

class Enemy:
    ENEMY_TYPES = {
        "slime": {
            "image_path": "assets/images/enemy/slime_monster_preview.png",
            "hp": 20,  # Giảm từ 40 xuống 20
            "speed": 42,
            "size": (21, 21)
        },
        "skeleton": {
            "image_path": "assets/images/enemy/skeleton.png",
            "hp": 40,  # Giảm từ 80 xuống 40
            "speed": 56,
            "size": (32, 22)
        },
        "zombie": {
            "image_path": "assets/images/enemy/zombie.png",
            "hp": 60,  # Giảm từ 120 xuống 60
            "speed": 56,
            "size": (28, 28)
        },
        "ghost": {
            "image_path": "assets/images/enemy/ghost.png",
            "hp": 40,  # Giảm từ 80 xuống 40
            "speed": 35,
            "size": (25, 25)
        },
        "giant": {
            "image_path": "assets/images/enemy/giant.png",
            "hp": 120,  # Giảm từ 240 xuống 120
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
            self.magic_image = pygame.transform.scale(self.magic_image, (14, 14))
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

        self.last_move = 0
        self.move_delay = 500
        self.maze_width = maze_width
        self.maze_height = maze_height
        self.maze = maze
        self.vision_range = 33 * cell_size
        self.base_speed = self.speed
        self.target_pos = None
        self.current_grid_pos = (y, x)
        self.path = []

        current_grid_x = int(self.rect.x // self.cell_size)
        current_grid_y = int(self.rect.y // self.cell_size)
        if (0 <= current_grid_y < self.maze_height and 0 <= current_grid_x < self.maze_width and
                self.maze[current_grid_y][current_grid_x] == 1):
            new_x, new_y = self.find_nearest_valid_position()
            self.rect.x = new_x
            self.rect.y = new_y
            self.current_grid_pos = (int(new_y // self.cell_size), int(new_x // self.cell_size))

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

    def attack(self, player_pos):
        if self.enemy_type == "skeleton":
            current_time = pygame.time.get_ticks()
            if current_time - self.last_attack >= self.attack_delay:
                dx = player_pos[1] * self.cell_size - self.rect.x
                dy = player_pos[0] * self.cell_size - self.rect.y
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
                dx = player_pos[1] * self.cell_size - self.rect.x
                dy = player_pos[0] * self.cell_size - self.rect.y
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

    def find_nearest_valid_position(self):
        current_grid_x = int(self.rect.x // self.cell_size)
        current_grid_y = int(self.rect.y // self.cell_size)
        queue = [(current_grid_y, current_grid_x)]
        visited = set()
        visited.add((current_grid_y, current_grid_x))
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        while queue:
            y, x = queue.pop(0)
            if (0 <= y < self.maze_height and 0 <= x < self.maze_width and
                    self.maze[y][x] == 0):
                return (x * self.cell_size, y * self.cell_size)
            for dy, dx in directions:
                next_y, next_x = y + dy, x + dx
                if (0 <= next_y < self.maze_height and 0 <= next_x < self.maze_width and
                        (next_y, next_x) not in visited):
                    queue.append((next_y, next_x))
                    visited.add((next_y, next_x))
        print(f"Warning: Could not find a valid position for {self.enemy_type} at ({current_grid_x}, {current_grid_y})")
        return (self.rect.x, self.rect.y)

    def on_maze_changed(self):
        self.target_pos = None
        self.path = []
        current_grid_x = int(self.rect.x // self.cell_size)
        current_grid_y = int(self.rect.y // self.cell_size)
        if (0 <= current_grid_y < self.maze_height and 0 <= current_grid_x < self.maze_width and
                self.maze[current_grid_y][current_grid_x] == 1):
            new_x, new_y = self.find_nearest_valid_position()
            self.rect.x = new_x
            self.rect.y = new_y
            self.current_grid_pos = (int(new_y // self.cell_size), int(new_x // self.cell_size))

    def a_star(self, start, goal):
        open_set = []
        heappush(open_set, (0, start))
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}
        came_from = {}

        closed_set = set()

        while open_set:
            current_f, current = heappop(open_set)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            closed_set.add(current)

            y, x = current
            neighbors = [(y + dy, x + dx) for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]]

            for next_y, next_x in neighbors:
                if not (0 <= next_y < self.maze_height and 0 <= next_x < self.maze_width):
                    continue
                if self.maze[next_y][next_x] == 1:
                    continue
                if (next_y, next_x) in closed_set:
                    continue

                tentative_g_score = g_score[current] + 1

                if (next_y, next_x) not in g_score or tentative_g_score < g_score[(next_y, next_x)]:
                    came_from[(next_y, next_x)] = current
                    g_score[(next_y, next_x)] = tentative_g_score
                    f_score[(next_y, next_x)] = tentative_g_score + self.manhattan_distance((next_y, next_x), goal)
                    heappush(open_set, (f_score[(next_y, next_x)], (next_y, next_x)))

        return []

    def manhattan_distance(self, pos1, pos2):
        y1, x1 = pos1
        y2, x2 = pos2
        return abs(x1 - x2) + abs(y1 - y2)

    def is_position_valid(self, x, y):
        grid_x = int(x // self.cell_size)
        grid_y = int(y // self.cell_size)
        if not (0 <= grid_y < self.maze_height and 0 <= grid_x < self.maze_width):
            return False
        return self.maze[grid_y][grid_x] == 0

    def move(self, player_pos, player_rect):
        current_time = pygame.time.get_ticks()

        dx = self.rect.x - (player_pos[1] * self.cell_size)
        dy = self.rect.y - (player_pos[0] * self.cell_size)
        distance_to_player_px = math.sqrt(dx**2 + dy**2)

        if distance_to_player_px <= self.vision_range:
            self.show_exclamation = True
            self.speed = self.base_speed * 2.4
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

        current_grid_x = int(self.rect.x // self.cell_size)
        current_grid_y = int(self.rect.y // self.cell_size)
        self.current_grid_pos = (current_grid_y, current_grid_x)

        if (0 <= current_grid_y < self.maze_height and 0 <= current_grid_x < self.maze_width and
                self.maze[current_grid_y][current_grid_x] == 1):
            new_x, new_y = self.find_nearest_valid_position()
            self.rect.x = new_x
            self.rect.y = new_y
            self.current_grid_pos = (int(new_y // self.cell_size), int(new_x // self.cell_size))
            self.target_pos = None
            self.path = []
            return

        if self.target_pos is None and current_time - self.last_move >= self.move_delay:
            self.last_move = current_time

            enemy_grid_pos = self.current_grid_pos

            if distance_to_player_px <= self.vision_range:
                self.path = self.a_star(enemy_grid_pos, player_pos)
                if not self.path:
                    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                    random.shuffle(directions)
                    moved = False
                    new_grid_x, new_grid_y = enemy_grid_pos[1], enemy_grid_pos[0]
                    for dx, dy in directions:
                        next_x = enemy_grid_pos[1] + dx
                        next_y = enemy_grid_pos[0] + dy
                        if (0 <= next_y < self.maze_height and 0 <= next_x < self.maze_width and
                                self.maze[next_y][next_x] == 0):
                            new_grid_x, new_grid_y = next_x, next_y
                            moved = True
                            break
                    if moved:
                        self.path = [enemy_grid_pos, (new_grid_y, new_grid_x)]
            else:
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                random.shuffle(directions)
                moved = False
                new_grid_x, new_grid_y = enemy_grid_pos[1], enemy_grid_pos[0]

                for dx, dy in directions:
                    next_x = enemy_grid_pos[1] + dx
                    next_y = enemy_grid_pos[0] + dy
                    if (0 <= next_y < self.maze_height and 0 <= next_x < self.maze_width and
                            self.maze[next_y][next_x] == 0):
                        new_grid_x, new_grid_y = next_x, next_y
                        moved = True
                        break

                if moved:
                    self.path = [enemy_grid_pos, (new_grid_y, new_grid_x)]
                else:
                    self.path = []

            if len(self.path) > 1:
                next_pos = self.path[1]
                self.target_pos = (next_pos[1] * self.cell_size, next_pos[0] * self.cell_size)
            else:
                self.target_pos = None
                self.path = []

        if self.target_pos:
            dx = self.target_pos[0] - self.rect.x
            dy = self.target_pos[1] - self.rect.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 1:
                speed_per_frame = self.speed / 60
                if distance <= speed_per_frame:
                    if self.is_position_valid(self.target_pos[0], self.target_pos[1]):
                        self.rect.x = self.target_pos[0]
                        self.rect.y = self.target_pos[1]
                        self.current_grid_pos = (int(self.target_pos[1] // self.cell_size),
                                                int(self.target_pos[0] // self.cell_size))
                    else:
                        self.target_pos = None
                        self.path = []
                        return
                else:
                    direction_x = dx / distance
                    direction_y = dy / distance
                    new_x = self.rect.x + direction_x * speed_per_frame
                    new_y = self.rect.y + direction_y * speed_per_frame

                    if self.is_position_valid(new_x, new_y):
                        self.rect.x = new_x
                        self.rect.y = new_y
                        self.current_grid_pos = (int(self.rect.y // self.cell_size),
                                                int(self.rect.x // self.cell_size))
                        if direction_x > 0:
                            self.facing_right = True
                            self.image = self.original_image
                        elif direction_x < 0:
                            self.facing_right = False
                            self.image = pygame.transform.flip(self.original_image, True, False)
                    else:
                        self.target_pos = None
                        self.path = []
                        new_x, new_y = self.find_nearest_valid_position()
                        self.rect.x = new_x
                        self.rect.y = new_y
                        self.current_grid_pos = (int(new_y // self.cell_size), int(new_x // self.cell_size))
                        return
            else:
                if self.is_position_valid(self.target_pos[0], self.target_pos[1]):
                    self.rect.x = self.target_pos[0]
                    self.rect.y = self.target_pos[1]
                    self.current_grid_pos = (int(self.target_pos[1] // self.cell_size),
                                            int(self.target_pos[0] // self.cell_size))
                else:
                    self.target_pos = None
                    self.path = []
                    return

            if abs(self.rect.x - self.target_pos[0]) < 1 and abs(self.rect.y - self.target_pos[1]) < 1:
                self.target_pos = None
                if self.path:
                    self.path.pop(0)
                if len(self.path) > 1:
                    next_pos = self.path[1]
                    self.target_pos = (next_pos[1] * self.cell_size, next_pos[0] * self.cell_size)

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