# player.py
import pygame
from bullet import Bullet


class Player:
    def __init__(self, x, y, maze=None, image_path=None):
        print(f"Khởi tạo Player tại vị trí ({x}, {y})")

        self.maze = maze

        self.walk_frames = {
            "right": [],
            "left": [],
            "up": [],
            "down": []
        }
        self.load_walk_frames()

        self.image = self.walk_frames["right"][0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
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
        self.health_bar_width = 40
        self.health_bar_height = 8
        self.health_bar_offset = 10

    def load_walk_frames(self):
        tile_width, tile_height = self.maze.tile_size
        for i in range(16):
            walkA_path = f"assets/images/hero/walkA/hero_walkA_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkA_path)
                frame = pygame.transform.scale(
                    frame, (tile_width, tile_height))
                self.walk_frames["down"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkA_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["down"].append(frame)

            walkB_path = f"assets/images/hero/walkB/hero_walkB_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkB_path)
                frame = pygame.transform.scale(
                    frame, (tile_width, tile_height))
                self.walk_frames["right"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkB_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["right"].append(frame)

            walkC_path = f"assets/images/hero/walkC/hero_walkC_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkC_path)
                frame = pygame.transform.scale(
                    frame, (tile_width, tile_height))
                self.walk_frames["up"].append(frame)
            except pygame.error as e:
                print(f"Không thể tải frame {walkC_path}: {e}")
                frame = pygame.Surface((tile_width, tile_height))
                frame.fill((255, 255, 255))
                self.walk_frames["up"].append(frame)

            walkD_path = f"assets/images/hero/walkD/hero_walkD_{str(i).zfill(4)}.png"
            try:
                frame = pygame.image.load(walkD_path)
                frame = pygame.transform.scale(
                    frame, (tile_width, tile_height))
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

        if moved and self.maze:
            player_tile_x = new_rect.centerx // self.maze.tile_size[0]
            player_tile_y = new_rect.centery // self.maze.tile_size[1]
            tile_key = f"{player_tile_x};{player_tile_y}"
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

        if moved:
            self.rect = new_rect

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

        can_roll = True
        if self.maze:
            player_tile_x = new_rect.centerx // self.maze.tile_size[0]
            player_tile_y = new_rect.centery // self.maze.tile_size[1]
            tile_key = f"{player_tile_x};{player_tile_y}"
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
                        can_roll = False

        if can_roll:
            self.rect = new_rect

        self.roll_distance_moved += self.roll_speed

        if self.roll_distance_moved >= self.roll_distance:
            self.is_rolling = False
            self.roll_distance_moved = 0

        self._update_image()

    def _update_image(self):
        current_animation_speed = self.animation_speed * \
            2 if self.is_rolling else self.animation_speed

        if self.is_moving or self.is_rolling:
            self.frame_index += current_animation_speed
            if self.frame_index >= len(self.walk_frames[self.direction]):
                self.frame_index = 0
            self.image = self.walk_frames[self.direction][int(
                self.frame_index)]
        else:
            self.frame_index = 0
            self.image = self.walk_frames[self.direction][0]

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
                damage=4  # Đổi sát thương từ 10 thành 4
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

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.rect.x -
                    offset[0], self.rect.y - offset[1]))

        if not self.is_rolling:
            health_ratio = self.health / self.max_health
            current_width = self.health_bar_width * health_ratio
            health_bar_x = self.rect.centerx - \
                self.health_bar_width // 2 - offset[0]
            health_bar_y = self.rect.top - self.health_bar_offset - offset[1]
            pygame.draw.rect(screen, (255, 0, 0), (health_bar_x,
                             health_bar_y, current_width, self.health_bar_height))

        for bullet in self.bullet_list:
            bullet.draw(screen, offset=offset)
