import pygame

from consts import *
from platforms import Platform, Circle, ImageStage
from kill_area import KillArea


class Player:
    def __init__(self, win: pygame.surface.Surface):
        self.win = win
        
        self.width = 40
        self.height = 40
        
        # constants, idk why they arent capital, i might change them at some point
        self.x_accel = 0.25
        self.terminal_vel = 11
        self.gravity = 0.3
        
        self.recording = False
        self.recorded_coords = []
        
        self.reset()
    
    def reset(self, coords: tuple[float, float] | None=None):
        if coords is None:
            coords = (100, 100)
        
        self.x, self.y = coords

        self.x_vel = 0
        self.y_vel = 0
        
        self.right = self.left = self.up = self.down = self.jumping = False
        self.dashing = False
        self.dashing_tick = 0           # used when the player is currently dashing
        self.dashing_cooldown = 0       # used to wait a little between dashes
        
        self.touched_floor = 10         # time since the floor was last touched (any less than 10 allows the player to jump)

    @property
    def rect(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def mask(self):
        return pygame.mask.Mask((self.width, self.height), True)
    
    @property
    def can_jump(self) -> bool:
        return self.touched_floor < 10
    
    def screen_rect(self, screen_cords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x - screen_cords[0], self.y - screen_cords[1], self.width, self.height)

    def draw(self, screen_coords):
        # use screen rect
        #colour = pygame.Color("dark green") if self.can_jump else pygame.Color("red")      # for seeing when the player can jump
        colour = pygame.color.Color("red")
        pygame.draw.rect(self.win, colour, self.screen_rect(screen_coords))
        
    def jump(self, override=False):
        # jump if touched floor in the last 10 frames (coyote time) or manual override (might be useful)
        # jump height is roughly 172 pixels
        if self.can_jump or override:
            self.y_vel = -10        # this should be a variable, not -10
            self.touched_floor += 10    # any less than 10 allows player to jump immediately again
    
    def dash(self):
        if self.dashing_cooldown != 0:
            # only dash if the cooldown is 0
            return
        # get direction of dash
        elif self.left and not self.right:
            sign = -1
        elif not self.left and self.right:
            sign = 1
        elif self.x_vel != 0:
            # if both left and right or neither are pressed, dash in the current direction of movement
            sign = 1 if self.x_vel == abs(self.x_vel) else -1
        else:
            return
        
        self.x_vel = 40 * sign
        self.dashing = True
        self.dashing_tick = 4
        self.dashing_cooldown = 30
    
    def valid_position(self, platforms: list[Platform | Circle | ImageStage], kill_areas: list[KillArea]) -> str | bool:
        """returns "dead" if dead, otherwise True or False whether position is valid or not"""
        
        if self.rect.collidelist([kill_area.rect for kill_area in kill_areas]) != -1:
            return "dead"
        
        platform_rects = []
        other_platforms = []
        for platform in platforms:
            if isinstance(platform, Platform):
                platform_rects.append(platform.rect)
            else:
                other_platforms.append(platform)
        
        if self.rect.collidelist(platform_rects) != -1:
            return False
        
        mask = self.mask
        for platform in other_platforms:
            offset_x = self.x - platform.x_tl
            offset_y = self.y - platform.y_tl
            if platform.mask.overlap(mask, (offset_x, offset_y)):
                return False
        
        return True
    
    def update_position(self, platforms: list[Platform | Circle | ImageStage], kill_areas: list[KillArea]):
        # splits movement into "divide" parts
        # keep moving the player in steps
        # if they overlap something, move them back 1 step and stop moving
        divide = 16
        change_x = True
        change_y = True
        for _ in range(divide):
            if change_x:
                slope = False
                self.x += self.x_vel / divide
                valid = self.valid_position(platforms, kill_areas)
                if valid == "dead":
                    return "dead"
                if not valid:
                    for i in range(10):
                        # moving up slopes
                        self.y -= i
                        if not slope and abs(self.y_vel) <= 1 and self.valid_position(platforms, kill_areas):
                            self.x_vel *= (i / 100 + 0.9)   # slow down the player a bit
                            slope = True
                        else:
                            self.y += i
                            
                    if not slope:
                        self.x -= self.x_vel / divide
                        self.x_vel = 0
                        change_x = False
                        self.dashing_tick = 0       # if wall is hit, stop dashing
            if change_y:
                self.y += self.y_vel / divide
                valid = self.valid_position(platforms, kill_areas)
                if valid == "dead":
                    return "dead"
                if not valid:
                    self.y -= self.y_vel / divide
                    if self.y_vel > 0:
                        self.touched_floor = 0  # if floor is hit, touched_floor is now 0
                    self.y_vel = 0
                    change_y = False
    
    def tick(self, platforms: list[Platform | Circle | ImageStage], kill_areas: list[KillArea]):
        # controls all the collision and stuff
        
        if self.dashing_cooldown > 0:
            self.dashing_cooldown -= 1
        
        if self.dashing:
            self.dashing_tick -= 1
            
        # only change velocity if the player isnt dashing
        elif self.right and self.left or not self.right and not self.left:
            # if nothing (or both left + right) is pressed, slow the player to a halt
            if self.x_vel < 0:
                self.x_vel = min(self.x_vel + self.x_accel, 0)
            elif self.x_vel > 0:
                self.x_vel = max(self.x_vel - self.x_accel, 0)
        
        elif self.right:
            # if slowing down, twice the acceleration is used
            if self.x_vel < 0:
                self.x_vel = min(self.x_vel + self.x_accel * 2, self.terminal_vel)
            else:
                self.x_vel = min(self.x_vel + self.x_accel, self.terminal_vel)
        
        elif self.left:
            # if slowing down, twice the acceleration is used
            if self.x_vel > 0:
                self.x_vel = max(self.x_vel - self.x_accel * 2, -self.terminal_vel)
            else:
                self.x_vel = max(self.x_vel - self.x_accel, -self.terminal_vel)
        
        # terminal x vel
        if not self.dashing and self.x_vel < 0:
            self.x_vel = max(self.x_vel, -self.terminal_vel)
        elif not self.dashing and self.x_vel > 0:
            self.x_vel = min(self.x_vel, self.terminal_vel)
        
        self.touched_floor += 1
        
        # move y vel down
        self.y_vel = min(self.y_vel + self.gravity, self.terminal_vel)
        
        if self.dashing_tick <= 0:
            self.dashing = False
        
        if self.jumping:
            self.jump()
        
        dead = self.update_position(platforms, kill_areas)
        if dead == "dead":
            self.reset()
        
        if self.recording:
            self.recorded_coords.append((self.x, self.y))
        