import pygame
from .bullet import Bullet

class Player:
    def __init__(self, x, y, maze=None):
        print(f"Khởi tạo Player tại vị trí ({x}, {y})")
        self.maze = maze
        self.gun_shot_sound = None
        self.walk_frames = {
            "right": [],
            "left": [],
            "up": [],
            "down": []
        }
        self.load_walk_frames()
        self.image = self.walk_frames["right"][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2.5
        self.bullets = 50
        self.bullet_list = []
        self.shoot_cooldown = 0
        self.direction = "right"
        self.frame_index = 0
        self.animation_speed = 0.2
        self.is_moving = False
        self.is_rolling = False
        self.roll_distance = 50
        self.roll_speed = 3.3
        self.roll_cooldown = 0
        self.roll_cooldown_max = 30
        self.roll_distance_moved = 0
        self.health = 100
        self.max_health = 100
        self.health_bar_width = 24
        self.health_bar_height = 6
        self.health_bar_offset = 8

    def load_walk_frames(self):
        player_size = (48, 48)
        for i in range(16):
            for direction, folder in [("down", "walkA"), ("right", "walkB"), ("up", "walkC"), ("left", "walkD")]:
                frame_path = f"assets/images/hero/{folder}/hero_{folder}_{str(i).zfill(4)}.png"
                try:
                    frame = pygame.image.load(frame_path)
                    frame = pygame.transform.scale(frame, player_size)
                    self.walk_frames[direction].append(frame)
                except pygame.error as e:
                    print(f"Không thể tải frame {frame_path}: {e}")
                    frame = pygame.Surface(player_size)
                    frame.fill((255, 255, 255))
                    self.walk_frames[direction].append(frame)

    def get_nearby_tiles(self, rect):
        """Lấy các ô gần vị trí nhân vật để kiểm tra va chạm"""
        nearby_tiles = []
        if not self.maze or not self.maze.tilemap:
            print("No maze or tilemap available for collision check")
            return nearby_tiles

        tile_size = self.maze.tile_size
        # Tính vị trí ô dựa trên trung tâm của nhân vật
        center_x, center_y = rect.center
        grid_x = center_x // tile_size[0]
        grid_y = center_y // tile_size[1]

        # Kiểm tra các ô trong lưới 3x3 xung quanh
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                tile_key = f"{int(grid_x + dx)};{int(grid_y + dy)}"
                if tile_key in self.maze.tilemap:
                    tile = self.maze.tilemap[tile_key]
                    # Chỉ thêm các ô là tường vào danh sách kiểm tra va chạm
                    if tile['type'] in ["WallStone", "WallBreakable"]:
                        nearby_tiles.append(tile)
                    
                        

        
        return nearby_tiles

    def move(self, keys):
        if self.roll_cooldown > 0:
            self.roll_cooldown -= 1

        if keys[pygame.K_b] and not self.is_rolling and self.roll_cooldown == 0:
            self.is_rolling = True
            self.roll_distance_moved = 0
            self.roll_cooldown = self.roll_cooldown_max
            print("Starting roll")

        if self.is_rolling:
            self._roll()
            return

        def get_collision_rect(rect, direction):
            shrink_w = 0.5  # Đủ nhỏ để len khe, nhưng không quá nhỏ
            new_w = int(rect.width * shrink_w)
            new_h = int(rect.height * 0.5)  # Gần bằng chiều cao thật
            new_x = rect.centerx - new_w // 2
            new_y = rect.bottom - new_h
            return pygame.Rect(new_x, new_y, new_w, new_h)

        moved = False
        orig_rect = self.rect.copy()
        new_rect = self.rect.copy()
        # Ưu tiên hướng theo phím nhấn cuối cùng
        direction_x = None
        direction_y = None
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction_x = "left"
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction_x = "right"
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction_y = "up"
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction_y = "down"
        # Ưu tiên hướng vừa nhấn cuối cùng
        last_dir = None
        for event in pygame.event.get([pygame.KEYDOWN]):
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_a, pygame.K_LEFT]:
                    last_dir = "left"
                elif event.key in [pygame.K_d, pygame.K_RIGHT]:
                    last_dir = "right"
                elif event.key in [pygame.K_w, pygame.K_UP]:
                    last_dir = "up"
                elif event.key in [pygame.K_s, pygame.K_DOWN]:
                    last_dir = "down"
        if last_dir:
            self.direction = last_dir
        elif direction_x:
            self.direction = direction_x
        elif direction_y:
            self.direction = direction_y

        # Di chuyển trục X trước
        if direction_x:
            test_rect = self.rect.copy()
            if direction_x == "left":
                test_rect.x -= self.speed
            elif direction_x == "right":
                test_rect.x += self.speed
            collision_rect = get_collision_rect(test_rect, direction_x)
            can_move_x = True
            nearby_tiles = self.get_nearby_tiles(collision_rect)
            for tile in nearby_tiles:
                if not isinstance(tile['pos'], (list, tuple)) or len(tile['pos']) != 2:
                    continue
                if 'scale' not in tile or not isinstance(tile['scale'], (list, tuple)) or len(tile['scale']) != 2:
                    tile['scale'] = self.maze.tile_size
                tile_rect = pygame.Rect(
                    tile['pos'][0] * self.maze.tile_size[0],
                    tile['pos'][1] * self.maze.tile_size[1],
                    tile['scale'][0],
                    tile['scale'][1]
                )
                if collision_rect.colliderect(tile_rect):
                    can_move_x = False
                    break
            if can_move_x:
                self.rect.x = test_rect.x
                moved = True
        # Di chuyển trục Y sau
        if direction_y:
            test_rect = self.rect.copy()
            if direction_y == "up":
                test_rect.y -= self.speed
            elif direction_y == "down":
                test_rect.y += self.speed
            collision_rect = get_collision_rect(test_rect, direction_y)
            can_move_y = True
            nearby_tiles = self.get_nearby_tiles(collision_rect)
            for tile in nearby_tiles:
                if not isinstance(tile['pos'], (list, tuple)) or len(tile['pos']) != 2:
                    continue
                if 'scale' not in tile or not isinstance(tile['scale'], (list, tuple)) or len(tile['scale']) != 2:
                    tile['scale'] = self.maze.tile_size
                tile_rect = pygame.Rect(
                    tile['pos'][0] * self.maze.tile_size[0],
                    tile['pos'][1] * self.maze.tile_size[1],
                    tile['scale'][0],
                    tile['scale'][1]
                )
                if collision_rect.colliderect(tile_rect):
                    can_move_y = False
                    break
            if can_move_y:
                self.rect.y = test_rect.y
                moved = True

        self.is_moving = moved
        if moved:
            self._update_image()

    def _roll(self):
        new_rect = self.rect.copy()
        if self.direction == "up":
            new_rect.y -= self.roll_speed
        elif self.direction == "down":
            new_rect.y += self.roll_speed
        elif self.direction == "left":
            new_rect.x -= self.roll_speed
        elif self.direction == "right":
            new_rect.x += self.roll_speed

        def get_collision_rect(rect, direction):
            if direction in ["left", "right"]:
                shrink_w = 0.6
                shrink_h = 0.4
            else:
                shrink_w = 0.4
                shrink_h = 0.6
            new_w = int(rect.width * shrink_w)
            new_h = int(rect.height * shrink_h)
            new_x = rect.centerx - new_w // 2
            new_y = rect.centery - new_h // 2
            return pygame.Rect(new_x, new_y, new_w, new_h)

        can_roll = True
        if self.maze:
            collision_rect = get_collision_rect(new_rect, self.direction)
            nearby_tiles = self.get_nearby_tiles(collision_rect)
            for tile in nearby_tiles:
                if not isinstance(tile['pos'], (list, tuple)) or len(tile['pos']) != 2:
                    print(f"Invalid tile position in roll: {tile['pos']} at {tile}, skipping collision")
                    continue
                if 'scale' not in tile or not isinstance(tile['scale'], (list, tuple)) or len(tile['scale']) != 2:
                    print(f"Invalid tile scale in roll: {tile.get('scale')} at {tile}, using default {self.maze.tile_size}")
                    tile['scale'] = self.maze.tile_size

                tile_rect = pygame.Rect(
                    tile['pos'][0] * self.maze.tile_size[0],
                    tile['pos'][1] * self.maze.tile_size[1],
                    tile['scale'][0],
                    tile['scale'][1]
                )
                if collision_rect.colliderect(tile_rect):
                    can_roll = False
                    print(f"Roll collision with tile at {tile['pos']} (type: {tile['type']}, scale: {tile['scale']})")
                    print(f"Player collision_rect: {collision_rect}, Tile rect: {tile_rect}")
                    break

        if can_roll:
            self.rect = new_rect
            print(f"Player rolled to {self.rect.topleft}")
        else:
            print(f"Roll blocked at {new_rect.topleft}")

        self.roll_distance_moved += self.roll_speed
        if self.roll_distance_moved >= self.roll_distance:
            self.is_rolling = False
            self.roll_distance_moved = 0
            print("Roll finished")

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

        # Giữ trung tâm của rect khi cập nhật hình ảnh
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
                image_path="assets/images/bullet/bullet.png",
                direction=self.direction,
                maze=self.maze,
                damage=4
            )
            self.bullet_list.append(bullet)
            self.bullets -= 1
            self.shoot_cooldown = 5
            print(f"Shot bullet, remaining bullets: {self.bullets}")
            if self.gun_shot_sound:
                self.gun_shot_sound.play()
                print("Playing gun shot sound")
            else:
                print("Gun shot sound not available")

    def update_bullets(self):
        for bullet in self.bullet_list[:]:
            bullet.move()
            if bullet.should_remove():
                self.bullet_list.remove(bullet)

    def collect_ammo(self, amount):
        self.bullets += amount
        print(f"Collected {amount} ammo. Total bullets: {self.bullets}")

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))
        if not self.is_rolling:
            health_ratio = self.health / self.max_health
            current_width = self.health_bar_width * health_ratio
            health_bar_x = self.rect.centerx - self.health_bar_width // 2 - offset[0]
            health_bar_y = self.rect.top - self.health_bar_offset - offset[1]
            pygame.draw.rect(screen, (255, 0, 0), (
                health_bar_x,
                health_bar_y,
                current_width,
                self.health_bar_height
            ))
        for bullet in self.bullet_list:
            bullet.draw(screen, offset=offset)