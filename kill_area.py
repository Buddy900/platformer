import pygame

from consts import *


class KillArea:
    def __init__(self, coords: tuple[float, float], dims, win: pygame.surface.Surface, moving=False):
        self.x, self.y = coords
        self.width, self.height = dims
        self.win = win
        self.moving = moving
        self.x_vel = 1.5
        self.y_vel = 0

    @property
    def rect(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)
    
    def screen_rect(self, screen_cords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x - screen_cords[0], self.y - screen_cords[1], self.width, self.height)

    def draw(self, screen_coords):
        pygame.draw.rect(self.win, pygame.Color("green"), self.screen_rect(screen_coords))
        
    def tick(self):
        if self.moving:
            self.x += self.x_vel
            self.y += self.y_vel
