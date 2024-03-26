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
        # speeds are in pixels per second
        self.x_accel = 1500
        self.terminal_x_vel = 480
        self.terminal_y_vel = 900
        self.gravity = 1800
        self.jump_strength = 800
        self.coyote_time = 0.1
        self.dash_strength = 2400
        self.dash_length = 0.08
        self.dash_cooldown = 0.8
        
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
        
        self.time_since_dash = 0           # used when the player is currently dashing, and to add a cooldown
        
        self.time_since_touched_floor = 10         # time since the floor was last touched (any less than 10 allows the player to jump)

    @property
    def rect(self) -> pygame.rect.Rect:
        # actual rect used for collisions
        return pygame.rect.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def mask(self):
        return pygame.mask.Mask((self.width, self.height), True)
    
    @property
    def can_jump(self) -> bool:
        return self.time_since_touched_floor < self.coyote_time
    
    @property
    def dashing(self) -> bool:
        return self.time_since_dash < self.dash_length
    
    def screen_rect(self, screen_coords) -> pygame.rect.Rect:
        # rect with regard to the coordinates (top left) of the screen so is used to draw
        return pygame.rect.Rect(self.x - screen_coords[0], self.y - screen_coords[1], self.width, self.height)

    def draw(self, screen_coords):
        # use screen rect
        #colour = pygame.Color("dark green") if self.can_jump else pygame.Color("red")      # for seeing when the player can jump
        colour = pygame.color.Color("red")
        pygame.draw.rect(self.win, colour, self.screen_rect(screen_coords))
        
        if self.time_since_dash > self.dash_cooldown:
            rect = pygame.rect.Rect(self.x - screen_coords[0] + self.width - 10, self.y - screen_coords[1] + 2, 5, self.height - 4)
            pygame.draw.rect(self.win, pygame.color.Color("dark green"), rect)
        else:
            percentage_dash = self.time_since_dash / self.dash_cooldown
            height = int((self.height - 4) * percentage_dash)
            rect = pygame.rect.Rect(self.x - screen_coords[0] + self.width - 10, self.y - screen_coords[1] + self.height - 2 - height, 5, height)
            pygame.draw.rect(self.win, pygame.color.Color("orange"), rect)
        
    def jump(self, override=False):
        # jump if touched floor in the last 10 frames (coyote time) or manual override (might be useful)
        # jump height is roughly 172 pixels
        if self.can_jump or override:
            self.y_vel = -self.jump_strength
            self.time_since_touched_floor += self.coyote_time    # any less than 10 allows player to jump immediately again
    
    def dash(self):
        if self.time_since_dash <= self.dash_cooldown:
            # only dash if it has been enough time
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
        
        self.x_vel = self.dash_strength * sign
        self.time_since_dash = 0
    
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
    
    def update_position(self, platforms: list[Platform | Circle | ImageStage], kill_areas: list[KillArea], dt):
        # splits movement into "divide" parts
        # keep moving the player in steps
        # if they overlap something, move them back 1 step and stop moving
        divide = 16
        change_x = True
        change_y = True
        for _ in range(divide):
            if change_x:
                slope = False
                self.x += (self.x_vel * dt) / divide
                valid = self.valid_position(platforms, kill_areas)
                if valid == "dead":
                    return "dead"
                if not valid:
                    for i in range(10):
                        # moving up slopes
                        self.y -= i
                        if not slope and (abs(self.y_vel) <= 1 or self.x_vel >= self.terminal_x_vel) and self.valid_position(platforms, kill_areas):
                            self.x_vel *= (i / 100 + 0.9)   # friction - needs to be updated to be physically accurate (friction = friction coefficient * normal force)
                            slope = True
                        else:
                            self.y += i
                            
                    if not slope:
                        self.x -= (self.x_vel * dt) / divide
                        self.x_vel = 0
                        change_x = False
                        if self.dashing:
                            self.time_since_dash = self.dash_length       # if wall is hit, stop dashing
            if change_y:
                self.y += (self.y_vel * dt) / divide
                valid = self.valid_position(platforms, kill_areas)
                if valid == "dead":
                    return "dead"
                if not valid:
                    self.y -= (self.y_vel * dt) / divide
                    if self.y_vel > 0:
                        self.time_since_touched_floor = 0  # if floor is hit, touched_floor is now 0
                    self.y_vel = 0
                    change_y = False
    
    def tick(self, platforms: list[Platform | Circle | ImageStage], kill_areas: list[KillArea], dt):
        # controls all the collision and stuff
        
        if self.dashing:
            pass
            
        # only change velocity if the player isnt dashing
        elif self.right and self.left or not self.right and not self.left:
            # if nothing (or both left + right) is pressed, slow the player to a halt
            if self.x_vel < 0:
                self.x_vel = min(self.x_vel + (self.x_accel * dt), 0)
            elif self.x_vel > 0:
                self.x_vel = max(self.x_vel - (self.x_accel * dt), 0)
        
        elif self.right:
            # if slowing down, twice the acceleration is used
            if self.x_vel < 0:
                self.x_vel = min(self.x_vel + (self.x_accel * 2 * dt), self.terminal_x_vel)
            else:
                self.x_vel = min(self.x_vel + (self.x_accel * dt), self.terminal_x_vel)
        
        elif self.left:
            # if slowing down, twice the acceleration is used
            if self.x_vel > 0:
                self.x_vel = max(self.x_vel - (self.x_accel * 2 * dt), -self.terminal_x_vel)
            else:
                self.x_vel = max(self.x_vel - (self.x_accel * dt), -self.terminal_x_vel)
        
        # terminal x vel
        if not self.dashing and self.x_vel < 0:
            self.x_vel = max(self.x_vel, -self.terminal_x_vel)
        elif not self.dashing and self.x_vel > 0:
            self.x_vel = min(self.x_vel, self.terminal_x_vel)
        
        self.time_since_touched_floor += dt
        self.time_since_dash += dt
        
        # move y vel down
        self.y_vel = min(self.y_vel + (self.gravity * dt), self.terminal_y_vel)
        
        if self.jumping:
            self.jump()
        
        dead = self.update_position(platforms, kill_areas, dt)
        if dead == "dead":
            self.reset()
        
        if self.recording:
            self.recorded_coords.append((self.x, self.y))
        