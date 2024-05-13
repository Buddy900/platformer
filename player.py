import pygame

from consts import *
from platforms import Platform, Rectangle, Circle, ImageStage
from kill_area import KillArea


class Player:
    def __init__(self, win: pygame.surface.Surface):
        self.win = win
        
        self.width = 40
        self.height = 40
        
        # constants, idk why they arent capital, i might change them at some point
        # speeds are in pixels per second
        self.mass = 10
        self.friction = 0.2
        self.x_accel = 1500
        self.terminal_x_vel = 480
        self.terminal_y_vel = 900
        self.wall_slide_vel = 200
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
        
        self.time_since_touched_floor = self.coyote_time         # time since the floor was last touched (any less than self.coyote_time allows the player to jump)
        self.time_since_touched_wall = self.coyote_time          # time since the wall was last touched (any less than self.coyote_time allows the player to wall jump)
        
        self.wall_jump_dir = 0
        
        self.platform_touching = None

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
    def can_wall_jump(self) -> bool:
        return self.time_since_touched_wall < self.coyote_time
    
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
        
    def jump(self, wall_jump=False, override=False):
        # jump if touched floor in the last 10 frames (coyote time) or manual override (might be useful)
        # jump height is roughly 172 pixels
        if self.can_jump or override:
            # normal jump
            self.y_vel = -self.jump_strength
            self.time_since_touched_floor += self.coyote_time    # any less than 10 allows player to jump immediately again
        
        elif wall_jump and self.can_wall_jump:
            # wall jump
            self.y_vel = -self.jump_strength
            self.time_since_touched_floor += self.coyote_time    # any less than 10 allows player to jump immediately again
            self.x_vel = self.wall_jump_dir * 300
    
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
    
    def touching(self, platforms: list[Platform], kill_areas: list[KillArea]):
        """returns "dead" if dead, otherwise True or False whether position is valid or not"""
        
        if self.rect.collidelist([kill_area.rect for kill_area in kill_areas]) != -1:
            return "dead"
        
        other_platforms = []
        for platform in platforms:
            if platform.has_rect:
                if self.rect.colliderect(platform.rect):
                    return platform
            else:
                offset_x = self.x - platform.x_tl
                offset_y = self.y - platform.y_tl
                if platform.mask.overlap(self.mask, (offset_x, offset_y)):
                    return platform
        
        return -1
    
    def update_position(self, platforms: list[Platform], kill_areas: list[KillArea], dt):
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
                touching = self.touching(platforms, kill_areas)
                if touching == "dead":
                    return "dead"
                if touching != -1:
                    for i in range(6):
                        # moving up slopes
                        self.y -= i
                        if not slope and (abs(self.y_vel) <= 1 or self.x_vel >= self.terminal_x_vel) and self.touching(platforms, kill_areas) == -1:
                            # self.x_vel *= (i / 100 + 0.9)   # slow down when moving up a slope - slightly dodgy
                            slope = True
                        else:
                            self.y += i
                            
                    if not slope:
                        self.x -= (self.x_vel * dt) / divide
                        self.wall_jump_dir = 0 if self.x_vel == 0 else - int(self.x_vel / abs(self.x_vel))
                        self.time_since_touched_wall = 0
                        self.x_vel = 0
                        change_x = False
                        if self.dashing:
                            self.time_since_dash = self.dash_length       # if wall is hit, stop dashing
                        self.y_vel = min(self.y_vel, self.wall_slide_vel)      # slide down walls
            if change_y:
                self.y += (self.y_vel * dt) / divide
                touching = self.touching(platforms, kill_areas)
                if touching == "dead":
                    return "dead"
                elif isinstance(touching, Platform):
                    self.platform_touching = touching
                if touching != -1:
                    self.y -= (self.y_vel * dt) / divide
                    if self.y_vel > 0:
                        self.time_since_touched_floor = 0  # if floor is hit, touched_floor is now 0
                    self.y_vel = 0
                    change_y = False
    
    def tick(self, platforms: list[Platform], kill_areas: list[KillArea], dt):
        # controls all the collision and stuff
        
        if self.dashing:
            pass
            
        # only change velocity if the player isnt dashing
        # friction - needs to be updated to be physically accurate (friction = friction coefficient * normal force)
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
        self.time_since_touched_wall += dt
        self.time_since_dash += dt
        
        # move y vel down
        self.y_vel = min(self.y_vel + (self.gravity * dt), self.terminal_y_vel)
        
        if self.jumping:
            self.jump()
        
        self.platform_touching = None
        dead = self.update_position(platforms, kill_areas, dt)
        if dead == "dead":
            self.reset()
        
        if self.recording:
            self.recorded_coords.append((self.x, self.y))
        