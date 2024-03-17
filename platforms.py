import pygame
import math

from consts import *


class Platform:
    def __init__(self, coords: tuple[float, float], dims, win: pygame.surface.Surface, moving=False):
        self.x, self.y = coords
        self.width, self.height = dims
        self.win = win
        self.moving = moving
        self.x_vel = 1.5
        self.y_vel = 0
        self.has_rect = True

    @property
    def rect(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)
    
    def screen_rect(self, screen_coords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x - screen_coords[0], self.y - screen_coords[1], self.width, self.height)

    def draw(self, screen_coords):
        pygame.draw.rect(self.win, pygame.Color("black"), self.screen_rect(screen_coords))
        
    def tick(self, player):
        if self.moving:
            self.x += self.x_vel
            self.y += self.y_vel
        
        # if collide with player, move the player along so no longer colliding
        # this doesnt really work
        if player.rect.colliderect(self.rect):
            player.x += math.ceil(self.x_vel)
            player.y += math.ceil(self.y_vel)
        

class Circle:
    def __init__(self, coords: tuple[float, float], radius: float, win: pygame.surface.Surface, moving=False):
        self.x, self.y = coords
        self.radius = radius
        self.win = win
        self.moving = moving
        self.x_vel = 1.5
        self.y_vel = 0
        self.has_rect = False
        circle_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, pygame.Color("black"), (self.radius, self.radius), self.radius)
        self.mask = pygame.mask.from_surface(circle_surface)
        
    @property
    def x_tl(self):
        return self.x - self.radius
    
    @property
    def y_tl(self):
        return self.y - self.radius

    def draw(self, screen_coords):
        if (screen_coords[0] <= self.x and self.x - self.radius <= screen_coords[0] + WIDTH) \
            and (screen_coords[1] <= self.y + self.radius and self.y - self.radius <= screen_coords[1] + HEIGHT):
            pygame.draw.circle(self.win, pygame.Color("black"), (self.x - screen_coords[0], self.y - screen_coords[1]), self.radius)
        
    def tick(self, player):
        if self.moving:
            self.x += self.x_vel
            self.y += self.y_vel
        
        # if collide with player, move the player along so no longer colliding
        # circles are rects :(
        # if player.rect.colliderect(self.rect):
        #     player.x += math.ceil(self.x_vel)
        #     player.y += math.ceil(self.y_vel)
        
class ImageStage:
    def __init__(self, file_path: str, win: pygame.surface.Surface, coords: tuple[int, int]=(0, 0)):
        self.x, self.y = coords
        self.x_tl = self.x
        self.y_tl = self.y
        self.win = win
        self.image = pygame.image.load(file_path)
        self.mask = pygame.mask.from_surface(self.image)
        self.has_rect = False

    def draw(self, screen_coords):
        rect = self.image.get_rect()
        rect.x, rect.y = self.x - screen_coords[0], self.y - screen_coords[1]
        self.win.blit(self.image, rect)
        
    def tick(self, player):
        ...
