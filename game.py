import pygame
import os

from consts import *

from platforms import Platform, Circle, ImageStage
from kill_area import KillArea
from player import Player


class Game:
    def __init__(self):
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        
        self.clock = pygame.time.Clock()
        
        self.player: Player = Player(self.win)
        # self.platforms = [Platform((-1000, HEIGHT - 300), (100, 300), self.win),
        #                   Platform((WIDTH + 1900, HEIGHT - 300), (100, 300), self.win), 
        #                   Platform((0, 600), (WIDTH, 100), self.win), Platform((600, 200), (100, 500), self.win),
        #                   Platform((200, 450), (WIDTH - 200, 100), self.win), Platform((400, 300), (WIDTH - 400, 100), self.win),
        #                   Platform((-1000, HEIGHT - 60), (WIDTH + 3000, 100), self.win),
        #                   Platform((-800, HEIGHT - 60 - 173), (100, 173), self.win), Platform((-600, HEIGHT - 60 - 172), (100, 172), self.win),
        #                   Platform((-400, HEIGHT - 60 - 171), (100, 171), self.win), Platform((-900, HEIGHT - 60 - 133), (100, 133), self.win),
        #                   Platform((1200, 600), (1000, 100), self.win), Platform((1300, 598), (100, 100), self.win),
        #                   Platform((1400, 596), (100, 100), self.win), Platform((1500, 592), (100, 100), self.win),
        #                   Circle((200, 300), 30, self.win), Circle((0, 300), 100, self.win)]
        # self.kill_areas = [KillArea((540, 400), (60, 50), self.win)]
        
        self.load_level_from_images("levels/2")
        
        self.kill_areas = []
        
        self.running: bool = False
        
        self.screen_coords = [0.0, 0.0]     # coords of the top left corner of the screen
        
        self.mode = 0   # 0-platformer, 1-editing
        
        self.last_mouse_click: tuple[int, int] | None = None        # used for placing platforms in edit mode
    
    def load_level_from_images(self, folder_path):
        files = []
        for (dirpath, dirnames, filenames) in os.walk(folder_path):
            files.extend(filenames)
            break
        
        image_paths = [f"{folder_path}/{file}" for file in files if file.endswith(".png")]
        
        self.platforms: list[Platform | Circle | ImageStage] = []
        for image in image_paths:
            self.platforms.append(ImageStage(image, self.win))
    
    def run(self):
        self.running = True
        while self.running:
            self.loop()
        pygame.quit()
        
    def control_screen_scroll(self):
        # if the player x is in the left or right third of the screen, scroll the screen in that direction
        lower_third = WIDTH / 3 + self.screen_coords[0]
        upper_third = 2 * WIDTH / 3 + self.screen_coords[0]
        if self.player.x < lower_third:
            difference = lower_third - self.player.x
            self.screen_coords[0] -= difference / 10
        elif self.player.x + self.player.width > upper_third:
            difference = self.player.x + self.player.width - upper_third
            self.screen_coords[0] += difference / 10
        
        # if the player y is in the top or bottom third of the screen, scroll the screen in that direction
        lower_third = HEIGHT / 3 + self.screen_coords[1]
        upper_third = 2 * HEIGHT / 3 + self.screen_coords[1]
        if self.player.y < lower_third:
            difference = lower_third - self.player.y
            self.screen_coords[1] -= difference / 10
        elif self.player.y + self.player.height > upper_third:
            difference = self.player.y + self.player.height - upper_third
            self.screen_coords[1] += difference / 10

    def draw(self):
        self.win.fill(pygame.Color("white"))
        
        self.player.draw(self.screen_coords)
        
        for platform in self.platforms:
            platform.draw(self.screen_coords)
            
        for kill_area in self.kill_areas:
            kill_area.draw(self.screen_coords)
        
        if self.last_mouse_click:
            # draw the rect that will currently be placed if there is another click
            x, y = pygame.mouse.get_pos()

            topleft_x = min(x, self.last_mouse_click[0] - int(self.screen_coords[0]))
            topleft_y = min(y, self.last_mouse_click[1] - int(self.screen_coords[1]))

            pygame.draw.rect(self.win, pygame.Color("black"),
                (topleft_x, topleft_y, abs(self.last_mouse_click[0] - int(self.screen_coords[0]) - x), abs(self.last_mouse_click[1] - int(self.screen_coords[1]) - y)))
        
        pygame.display.update()
        
        pygame.display.set_caption(str(round(self.clock.get_fps(), 2)))
    
    def handle_mouse_down(self, event):
        mouse_coords = pygame.mouse.get_pos()
        mouse_x = mouse_coords[0] + int(self.screen_coords[0])
        mouse_y = mouse_coords[1] + int(self.screen_coords[1])
        if event.button == 3:
            print(mouse_x, mouse_y)
        if self.mode == 1:
            # edit mode
            if self.last_mouse_click is None:
                # record coordinates of first corner of platform
                self.last_mouse_click = (mouse_x, mouse_y)
            else:
                # get lowest and highest x and y values for corners of platform
                min_x = min(mouse_x, self.last_mouse_click[0])
                min_y = min(mouse_y, self.last_mouse_click[1])
                max_x = max(mouse_x, self.last_mouse_click[0])
                max_y = max(mouse_y, self.last_mouse_click[1])
                platform = Platform((min_x, min_y), (max_x - min_x, max_y - min_y), self.win)
                self.platforms.append(platform)
                self.last_mouse_click = None
    
    def handle_key_down(self, event: pygame.event.Event):
        if event.key == pygame.K_h:
            print(HELP_MESSAGE)
        
        elif event.key in [pygame.K_SPACE, pygame.K_UP, pygame.K_w]:
            self.player.jump(wall_jump=True)
        elif event.key == pygame.K_f:
            self.player.dash()
        elif event.key == pygame.K_r:
            self.player.reset()
        elif event.key == pygame.K_m:
            self.mode += 1
            self.mode %= 2      # change to be the amount of modes
            
            self.last_mouse_click = None
        
        elif event.key == pygame.K_F1:
            self.player.recording = not self.player.recording
            if self.player.recording:
                self.player.recorded_coords = []
            
        elif event.key == pygame.K_F2:
            x = [coords[0] for coords in self.player.recorded_coords]
            y = [coords[1] for coords in self.player.recorded_coords]
            print(min(y), max(y), max(y) - min(y))
    
    def loop_platformer(self):
        # tell player what keys are being pressed
        keys_pressed = pygame.key.get_pressed()
        self.player.right = keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]
        self.player.left = keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]
        self.player.jumping = keys_pressed[pygame.K_SPACE] or keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]
    
        # update platforms (in case they are moving)
        for platform in self.platforms:
            platform.tick(self.player)
        
        # update player
        self.player.tick(self.platforms, self.kill_areas, self.clock.get_time() / 1000)     # / 1000 turns dt into seconds
    
        # scroll screen after player has moved
        self.control_screen_scroll()
        
    def loop_editor(self):
        # scroll the screen if arrows or wasd are pressed, scroll faster if shift is also pressed
        keys_pressed = pygame.key.get_pressed()
        if keys_pressed[pygame.K_LSHIFT]:
            multiply = 5
        else:
            multiply = 1
        
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.screen_coords[0] += 5 * multiply
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.screen_coords[0] -= 5 * multiply
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            self.screen_coords[1] -= 5 * multiply
        if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
            self.screen_coords[1] += 5 * multiply
    
    def loop(self):
        # main loop
        
        self.clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            elif event.type == pygame.KEYDOWN:
                self.handle_key_down(event)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event)
            
        if self.mode == 0:
            self.loop_platformer()
        elif self.mode == 1:
            self.loop_editor()
        
        self.draw()
