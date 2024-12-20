import pygame

from consts import *
from platforms import Platform, Rectangle, Circle, ImageStage
from kill_area import KillArea
from portal import Portal


class Player:
    def __init__(self, win: pygame.surface.Surface):
        self.win = win
        
        self.width = 40
        self.height = 40
        
        # constants, idk why they arent capital, i might change them at some point
        # speeds are in pixels per second
        self.mass = 10
        self.friction = 0.2
        self.x_accel = 2000
        self.x_accel_air_mod = 1.2
        self.terminal_x_vel = 480
        self.terminal_y_vel = 900
        self.wall_slide_vel = 200
        self.gravity = 1800
        self.jump_strength = 800
        self.coyote_time = 0.1
        self.dash_strength = 2400
        self.dash_length = 0.06
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
        self.time_since_jump = 0           # used to limit jumps when holding down jump button
        
        self.time_since_touched_floor = self.coyote_time         # time since the floor was last touched (any less than self.coyote_time allows the player to jump)
        self.time_since_touched_wall = self.coyote_time          # time since the wall was last touched (any less than self.coyote_time allows the player to wall jump)
        
        self.wall_jump_dir = 0
        self.wall_jumping = False
        
        self.platform_touching = None
        self.in_portal = False

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
        
    def jump(self, wall_jump=False, auto=False, override=False):
        # jump if touched floor in the last 10 frames (coyote time) or manual override (might be useful)
        # jump height is roughly 172 pixels
        jumped = True
        if (self.can_jump and not auto) or override:
            # normal jump
            self.y_vel = -self.jump_strength
            self.time_since_touched_floor += self.coyote_time    # any less than 0.1 allows player to jump immediately again
        
        elif self.can_jump and auto and self.time_since_jump > 0.2:
            # jump from holding down jump button (limits how fast this can happen)
            self.y_vel = -self.jump_strength
            self.time_since_touched_floor += self.coyote_time    # any less than 0.1 allows player to jump immediately again
        
        elif wall_jump and self.can_wall_jump:
            # wall jump
            self.y_vel = -self.jump_strength * 0.7
            self.time_since_touched_floor += self.coyote_time    # any less than 0.1 allows player to jump immediately again
            self.x_vel = self.wall_jump_dir * 500
            self.wall_jumping = True
        
        else: jumped = False
        if jumped:
            self.time_since_jump = 0
    
    def stop_jump(self):
        if self.y_vel < 0 and not self.wall_jumping:
            self.y_vel = 0
    
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
    
    def check_in_portal(self, portals: list[Portal]):
        collide_portal = False
        for portal in portals:
            if self.rect.colliderect(portal.rect_1):
                collide_portal = True
                if not self.in_portal:
                    # wasn't in a portal before but now is
                    if portal.vertical:
                        self.y = portal.y_2 + self.y - portal.y_1
                        if self.x > portal.x_1:
                            self.x = portal.x_2 - self.width
                        else:
                            self.x = portal.x_2 + portal.width
                    else:
                        self.x = portal.x_2 + self.x - portal.x_1
                        if self.y > portal.y_1:
                            self.y = portal.y_2 - self.height
                        else:
                            self.y = portal.y_2 + portal.height
                    self.in_portal = True
                
            elif self.rect.colliderect(portal.rect_2):
                collide_portal = True
                #print("in orange")
                if not self.in_portal:
                    # wasn't in a portal before but now is
                    if portal.vertical:
                        self.y = portal.y_1 + self.y - portal.y_2
                        if self.x > portal.x_2:
                            self.x = portal.x_1 - self.width
                        else:
                            self.x = portal.x_1 + portal.width
                    else:
                        self.x = portal.x_1 + self.x - portal.x_2
                        if self.y > portal.y_2:
                            self.y = portal.y_1 - self.height
                        else:
                            self.y = portal.y_1 + portal.height
                    self.in_portal = True
        
        if not collide_portal:
            self.in_portal = False
    
    def touching(self, platforms: list[Platform], kill_areas: list[KillArea], portals: list[Portal]):
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
    
    def update_position(self, platforms: list[Platform], kill_areas: list[KillArea], portals: list[Portal], dt):
        # splits movement into "divide" parts
        # keep moving the player in steps
        # if they overlap something, move them back 1 step and stop moving
        divide = 16
        change_x = True
        change_y = True
        for _ in range(divide):
            self.check_in_portal(portals)
            if change_x:
                slope = False
                self.x += (self.x_vel * dt) / divide
                touching = self.touching(platforms, kill_areas, portals)
                if touching == "dead":
                    return "dead"
                if touching != -1:
                    for i in range(6):
                        # moving up slopes
                        self.y -= i
                        if not slope and (abs(self.y_vel) <= 1 or self.x_vel >= self.terminal_x_vel) and self.touching(platforms, kill_areas, portals) == -1:
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
                touching = self.touching(platforms, kill_areas, portals)
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
    
    def tick(self, platforms: list[Platform], kill_areas: list[KillArea], portals: list[Portal], dt):
        # controls all the collision and stuff
        
        # try to get the player out of an object, otherwise kill them
        safe = True
        for _ in range(6):
            safe = self.touching(platforms, kill_areas, portals) == -1
            if not safe:
                self.y -= 1
            else:
                break
        
        if not safe:
            self.y += 6
            for _ in range(6):
                safe = self.touching(platforms, kill_areas, portals) == -1
                if not safe:
                    self.y += 1
                else:
                    break
        
        if not safe:
            self.reset()
        
        
        x_accel = self.x_accel * self.x_accel_air_mod if not self.can_jump else self.x_accel
        if self.time_since_dash < self.dash_length:
            max_speed = self.dash_strength
        elif self.time_since_dash < self.dash_length + 0.1 and self.time_since_touched_floor > 0.1:
            max_speed = self.dash_strength / 3
        elif self.time_since_touched_floor > 0.1:
            max_speed = max(self.terminal_x_vel, abs(self.x_vel))
        else:
            max_speed = max(self.terminal_x_vel, abs(self.x_vel) * 0.9)
        
        
        if self.dashing:
            pass
            
        # only change velocity if the player isnt dashing
        # friction - needs to be updated to be physically accurate (friction = friction coefficient * normal force)
        elif self.right and self.left or not self.right and not self.left:  
            # if nothing (or both left + right) is pressed, slow the player to a halt
            if self.x_vel < 0:
                self.x_vel = min(self.x_vel + (x_accel * dt), 0)
            elif self.x_vel > 0:
                self.x_vel = max(self.x_vel - (x_accel * dt), 0)
        
        elif self.right:
            # if slowing down, twice the acceleration is used
            if self.x_vel < 0:
                self.x_vel = min(self.x_vel + (x_accel * 2 * dt), max_speed)
            else:
                self.x_vel = min(self.x_vel + (x_accel * dt), max_speed)
        
        elif self.left:
            # if slowing down, twice the acceleration is used
            if self.x_vel > 0:
                self.x_vel = max(self.x_vel - (x_accel * 2 * dt), -max_speed)
            else:
                self.x_vel = max(self.x_vel - (x_accel * dt), -max_speed)
        
        # terminal x vel
        if not self.dashing and self.x_vel < 0:
            self.x_vel = max(self.x_vel, -max_speed)
        elif not self.dashing and self.x_vel > 0:
            self.x_vel = min(self.x_vel, max_speed)
        
        self.time_since_touched_floor += dt
        self.time_since_touched_wall += dt
        self.time_since_dash += dt
        self.time_since_jump += dt
        
        # move y vel down
        if self.y_vel >= 0:
            gravity = self.gravity * 2
            self.wall_jumping = False
        else:
            gravity = self.gravity
        self.y_vel = min(self.y_vel + (gravity * dt), self.terminal_y_vel)
        
        if self.jumping:
            self.jump(auto=True)
            
        if self.dashing:
            self.y_vel = min(0, self.y_vel)
        
        self.platform_touching = None
        dead = self.update_position(platforms, kill_areas, portals, dt)
        if dead == "dead":
            self.reset()
        
        if self.recording:
            self.recorded_coords.append((self.x, self.y))
        