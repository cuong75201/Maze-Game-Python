import pygame

class Bullet:
    def __init__(self, x, y, image_path, direction, maze=None):
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.scale(self.image, (20, 20))
        except pygame.error as e:
            print(f"Không thể tải hình ảnh đạn: {e}")
            self.image = pygame.Surface((20, 20))
            self.image.fill((255, 255, 0))

        self.rect = self.image.get_rect(center=(x, y))
        self.direction = direction
        self.speed = 10
        self.maze = maze

    def move(self):
        if self.direction == "up":
            self.rect.y -= self.speed
        elif self.direction == "down":
            self.rect.y += self.speed
        elif self.direction == "left":
            self.rect.x -= self.speed
        elif self.direction == "right":
            self.rect.x += self.speed

        if self.maze:
            for loc in self.maze.tilemap:
                tile = self.maze.tilemap[loc]
                if tile['type'] in ["WallStone", "WallBreakable"]:
                    tile_rect = pygame.Rect(
                        tile['pos'][0] * self.maze.tile_size[0],
                        tile['pos'][1] * self.maze.tile_size[1],
                        self.maze.tile_size[0],
                        tile.get('scale', self.maze.tile_size)[1]
                    )
                    if self.rect.colliderect(tile_rect):
                        return True
        return False

    def should_remove(self):
        return self.move()

    def draw(self, screen, offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - offset[0], self.rect.y - offset[1]))
