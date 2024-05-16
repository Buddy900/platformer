import pygame
import math

from consts import *


class Platform:
    def __init__(self, coords: tuple[float, float], dims, win: pygame.surface.Surface, vel_path: list[tuple[tuple[float, float], float]] | None=None):
        self.x, self.y = coords
        self.width, self.height = dims
        self.win = win
        self.vel_pointer = 0
        self.time_since_vel_change = 0
        if vel_path is None:
            self.vel_path: list[tuple[tuple[float, float], float]] = []
        else:
            self.vel_path: list[tuple[tuple[float, float], float]] = vel_path # type: ignore
        self.has_rect = True
        self.mask = pygame.mask.Mask((0, 0))
    
    @property
    def rect(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def x_tl(self):
        return self.x
    
    @property
    def y_tl(self):
        return self.y
    
    def screen_rect(self, screen_coords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x - screen_coords[0], self.y - screen_coords[1], self.width, self.height)

    def draw(self, screen_coords):
        pygame.draw.rect(self.win, pygame.Color("black"), self.screen_rect(screen_coords))
        
    def tick(self, player, dt):
        self.time_since_vel_change += dt
        if len(self.vel_path) == 0:
            x_vel = y_vel = 0
        else:
            if self.time_since_vel_change > self.vel_path[self.vel_pointer][1]:
                next_pointer = self.vel_pointer + 1
                if next_pointer > len(self.vel_path) - 1:
                    next_pointer = 0
                self.vel_pointer = next_pointer
                self.time_since_vel_change = 0
            x_vel, y_vel = self.vel_path[self.vel_pointer][0]
        
        self.x += x_vel * dt
        self.y += y_vel * dt
        
        player_collide = False
        if self == player.platform_touching:
            player_collide = True
        elif self.has_rect:
            rect = self.rect
            #rect.x += 1
            #rect.y += 1
            #rect.width -= 2
            #rect.height -= 2
            player_collide = rect.colliderect(player.rect)
        else:
            offset_x = player.x - self.x_tl
            offset_y = player.y - self.y_tl
            player_collide = self.mask.overlap(player.mask, (offset_x, offset_y))
        
        if player_collide:
            player.x += x_vel * dt
            player.y += y_vel * dt


class Rectangle(Platform):
    def __init__(self, coords: tuple[float, float], dims, win: pygame.surface.Surface, vel_path: list[tuple[tuple[float, float], float]] | None=None):
        self.x, self.y = coords
        self.width, self.height = dims
        self.win = win
        self.vel_pointer = 0
        self.time_since_vel_change = 0
        if vel_path is None:
            self.vel_path: list[tuple[tuple[float, float], float]] = []
        else:
            self.vel_path: list[tuple[tuple[float, float], float]] = vel_path # type: ignore
        self.has_rect = True
        
        
class Circle(Platform):
    def __init__(self, coords: tuple[float, float], radius: float, win: pygame.surface.Surface, vel_path: list[tuple[tuple[float, float], float]] | None=None):
        self.x, self.y = coords
        self.radius = radius
        self.win = win
        self.vel_pointer = 0
        self.time_since_vel_change = 0
        if vel_path is None:
            self.vel_path: list[tuple[tuple[float, float], float]] = []
        else:
            self.vel_path: list[tuple[tuple[float, float], float]] = vel_path # type: ignore
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
        
        
class ImageStage(Platform):
    def __init__(self, file_path: str, win: pygame.surface.Surface, coords: tuple[int, int]=(0, 0), vel_path: list[tuple[tuple[float, float], float]] | None=None):
        self.x, self.y = coords
        self.win = win
        self.image = pygame.image.load(file_path).convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        self.has_rect = False
        self.vel_pointer = 0
        self.time_since_vel_change = 0
        if vel_path is None:
            self.vel_path: list[tuple[tuple[float, float], float]] = []
        else:
            self.vel_path: list[tuple[tuple[float, float], float]] = vel_path # type: ignore

    def draw(self, screen_coords):
        rect = self.image.get_rect()
        rect.x, rect.y = self.x - screen_coords[0], self.y - screen_coords[1]
        self.win.blit(self.image, rect)
