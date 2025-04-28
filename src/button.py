import pygame   
class Button:
        def __init__(self, x, y,img,img_hover,scale):
            self.image=pygame.transform.scale(img,(int(img.get_width()*scale),int(img.get_height()*scale)))
            self.image_hover=pygame.transform.scale(img_hover,(int(img_hover.get_width()*scale),int(img_hover.get_height()*scale)))
            
            self.rect=self.image.get_rect()
            self.rect.topleft=(x,y)
            self.clicked = False
        def draw(self,surface,screen):
            action = False
            surface.blit(self.image, (self.rect.x, self.rect.y))
            #get mouse position
            pos = list(pygame.mouse.get_pos())
            surface_width, surface_height = surface.get_size()
            screen_width, screen_height = screen.get_size()

            scale_x = surface_width / screen_width
            scale_y = surface_height / screen_height
            
            pos[0]=pos[0]*scale_x
            pos[1]=pos[1]*scale_y
            

            # Kiểm tra chuột có ấn hay di chuyển vào khu vực không để đổi hình ảnh
            if self.rect.collidepoint(pos):
                if self.image_hover:
                            surface.blit(self.image_hover, (self.rect.x, self.rect.y))
                if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                    action = True
                    self.clicked = True
            if pygame.mouse.get_pressed()[0] == 0:
                self.clicked = False
            return action