import pygame

from consts import *


class Portal:
    def __init__(self, coords_1: tuple[float, float], coords_2: tuple[float, float], dims, win: pygame.surface.Surface):
        self.x_1, self.y_1 = coords_1
        self.x_2, self.y_2 = coords_2
        self.width, self.height = dims
        self.win = win
        self.vertical = self.width <= self.height

    @property
    def rect_1(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x_1, self.y_1, self.width, self.height)

    @property
    def rect_2(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x_2, self.y_2, self.width, self.height)

    def screen_rect_1(self, screen_cords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x_1 - screen_cords[0], self.y_1 - screen_cords[1], self.width, self.height)

    def screen_rect_2(self, screen_cords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x_2 - screen_cords[0], self.y_2 - screen_cords[1], self.width, self.height)

    def draw(self, screen_coords):
        pygame.draw.rect(self.win, pygame.Color("blue"), self.screen_rect_1(screen_coords))
        pygame.draw.rect(self.win, pygame.Color("orange"), self.screen_rect_2(screen_coords))
        
    def tick(self, player):
        pass
