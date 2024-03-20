# ---------------- INITIALISATION ---------------- #






#Imports
import pygame
from pygame.locals import *
import sys
import math
import time
import csv
import os

pygame.init()

# Read settings
with open("settings.csv") as settings_file:
    settings_reader = csv.reader(settings_file)
    i = -1
    for row in settings_reader:
        i += 1
        if i == 0:
            width = int(row[1])
        if i == 1:
            height = int(row[1])
        if i == 2:
            fps = int(row[1])

# Read current level
with open("current_level.csv") as level_file:
    level_reader = csv.reader(level_file)
    for row in level_reader:
        current_level = int(row[0])

num_levels = 3


game_state = "menu"
# ALWAYS SET THIS BACK TO TRUE WHEN SWITCHING GAME STATE VERY IMPORTANT
objects_initialised = True

two_vec = pygame.math.Vector2
three_vec = pygame.math.Vector3
# Third dimension (not on screen)
length = 200
l_h_ratio = length / height
width_ratio = width / 1280
height_ratio = height / 720

FramePerSec = pygame.time.Clock()
last_time = time.time()

debugger_font = pygame.font.SysFont("Arial", 18 * int(height_ratio))
menu_font = pygame.font.SysFont("bahnschrift", int(50 * height_ratio))

pressed_keys = pygame.key.get_pressed()

slidersurface = pygame.display.set_mode((width, height))
displaysurface = pygame.display.set_mode((width, height))
playersurface = pygame.display.set_mode((width, height))
pygame.display.set_caption("Voxel")


pygame.mixer.music.load('main_menu.wav')






# ---------------- CLASSES ---------------- #






class MenuBox(pygame.sprite.Sprite):

    def __init__(self, res_width, res_height, box_fps, box_x, box_y, box_y_distance, text):
        super().__init__()
        self.box_width = 300 * width_ratio
        self.box_height = 80 * height_ratio

        # Used to set resolution and fps values when boxes clicked to change settings
        self.res_height = res_height
        self.res_width = res_width
        self.box_fps = box_fps

        self.image = pygame.Surface((self.box_width, self.box_height))
        self.image.fill((128, 0, 128))
        self.rect = self.image.get_rect()
        
        self.pos = two_vec((box_x, box_y + box_y_distance))
        self.rect.center = self.pos

        self.text = text

    def menu_display(self):
        menu_text = menu_font.render(self.text, True, pygame.Color("white"))
        text_rect = menu_text.get_rect(center=(self.pos.x, self.pos.y))
        slidersurface.blit(menu_text, text_rect)

    def click_check(self):
        # Check if box is being hovered over
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(displaysurface, (0, 0, 0), self.rect, width = int(5 * width_ratio))
            self.image.fill((153, 50, 204))
        else:
            self.image.fill((128, 0, 128))
        # Check if box has been pressed
        mouse_state = pygame.mouse.get_pressed()
        if mouse_state[0] == 1:
            if self.rect.collidepoint(event.pos):
                time.sleep(0.1)
                return True




class Player(pygame.sprite.Sprite):

    def __init__(self, object_pos_x, object_pos_y):
        super().__init__()

        self.width = 30 * width_ratio
        self.height = 60 * height_ratio

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        
        self.pos = two_vec((object_pos_x, object_pos_y))
        self.speed = 4 * width_ratio
        self.acceleration = 0.5 * height_ratio
        self.friction = -0.12 * width_ratio
        self.jump_height = -15 * height_ratio

        self.grounded = False
        self.previous_collided = []

        self.velocity = two_vec((0, height_ratio))
        self.acc = two_vec((0, 0))
        
        self.rect.center = self.pos

    def move(self, spheres_list):

        # Horizontal and vertical acceleration
        self.acc = two_vec((0, 0.5 * height_ratio))
        
        if pressed_keys[K_a]:
            self.acc.x = -self.acceleration * width_ratio
        if pressed_keys[K_d]:
            self.acc.x = self.acceleration * width_ratio

        self.acc.x += self.velocity.x * self.friction

        if not self.grounded:
            self.velocity.y += self.acc.y * dt
        else:
            if pressed_keys[K_SPACE]:
                # Prevent double jumping, can only jump when on a platform
                self.velocity.y = self.jump_height
                self.grounded = False
        
        self.velocity.x += self.acc.x * dt

        self.collide_check(self.velocity, spheres_list)

        self.pos += self.velocity * dt
            
        self.rect.center = self.pos
    
    def collide_check(self, direction, spheres_list):
        # Stop the player from going off the left, right and bottom of the screen
        if self.pos.x <= self.width / 2:
            self.pos.x = self.width / 2
        if self.pos.x >= width - self.width / 2:
            self.pos.x = width - self.width / 2
        if self.pos.y >= height - self.height / 2:
            self.pos.y = height - self.height / 2

        self.rect.x += direction.x
        collided = sprite_collision(self, spheres_list)
        if collided:
            if direction.x > 0:
                self.rect.x = collided.left - self.rect.width
            if direction.x < 0:
                self.rect.x = collided.right + self.rect.width
            self.velocity.x = 0

        self.rect.y += direction.y
        collided = sprite_collision(self, spheres_list)
        if collided:
            self.previous_collided = collided
            if direction.y > 0:
                self.pos.y = collided.top - self.height / 2 - height_ratio
                self.grounded = True
            if direction.y < 0:
                self.pos.y = collided.bottom + self.height / 2 + height_ratio
            self.velocity.y = 0
        
        if self.previous_collided:
            # Gravity acts if the player is off the object
            if self.rect.left > self.previous_collided.right or self.rect.right < self.previous_collided.left:
                self.grounded = False
            # Gravity acts if the player is being pushed by an object
            if self.pos.y - self.previous_collided.top + self.height /2 != - height_ratio:
                self.grounded = False
            # Gravity acts if object is no longer there
            count = 0
            platform_flag = False
            sphere_count = 0

            for i in object_sprites:
                if i.rect == self.previous_collided:
                    count += 1
            for i in platform_sprites:
                if i.rect == self.previous_collided:
                    platform_flag = True
            for i in spheres_list:
                for j in i:
                    if j == self.previous_collided:
                        sphere_count += 1

            if count == 0 and sphere_count == 0 and platform_flag == False:
                self.grounded = False




class SliderLine(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        # Line witdh and height
        # 50 * height_ratio is the same value as used in Slider class, if changing the value of self.c in Slider, needs to be changed in SliderLine as well
        self.image = pygame.Surface((8 * width_ratio, height - (2 * 50 * height_ratio)))
        # Line colour
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        
        # Line starting position
        self.pos = two_vec((51 * width_ratio, height /2))
        self.rect.center = self.pos




class Slider(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        # Slider witdh and height
        self.image = pygame.Surface((60 * width_ratio, 60 * height_ratio))
        # Slider colour
        self.image.fill((200, 200, 200))
        self.rect = self.image.get_rect()
        
        # Box starting position and speed
        self.pos = two_vec((51 * width_ratio, 360 * height_ratio))
        self.speed = 4 * width_ratio
        
        self.drag = False

        # y = m(x-c) where y is a value from 0 to length, x is the slider y position, m is the length / slider length and c is the distance of the slider from the bottom
        # Or rearranged for x = y/m + c

        self.c = 50 * height_ratio
        self.slider_length = height - (2 * self.c)
        self.m = length / self.slider_length

        self.rect.center = self.pos
        
    def move(self):
        # Check if mouse is outside of window
        if not mouse_check():
            # Get key and mouse values
            mouse_state = pygame.mouse.get_pressed()
            
            # Move up and down to just under the end of the screen
            if mouse_state[0] != 1:
                if pressed_keys[K_UP]:
                    if self.pos.y > self.c:
                        self.pos.y += -self.speed * dt
                        if self.pos.y < self.c:
                            self.pos.y = self.c
                if pressed_keys[K_DOWN]:
                    if self.pos.y < self.slider_length + self.c:
                        self.pos.y += self.speed * dt
                        if self.pos.y > self.slider_length + self.c:
                            self.pos.y = self.slider_length + self.c

            # Move up and down if slider is being clicked on
            if not pressed_keys:
                offset_y = 0    
                if mouse_state[0] == 1:         
                    if self.rect.collidepoint(event.pos):
                        self.drag = True
                        mouse_x, mouse_y = event.pos
                        offset_y = self.pos.y - mouse_y
                
                if mouse_state[0] == 0:      
                        self.drag = False
                
                if event.type == pygame.MOUSEMOTION:
                    if self.drag:
                        mouse_x, mouse_y = event.pos
                        self.pos.y = mouse_y + offset_y
            
            self.rect.center = self.pos
    
    def display(self):
        # Display y position value

        pos_text = debugger_font.render(str(self.m * (self.pos.y - self.c)), True, pygame.Color("coral"))
        displaysurface.blit(pos_text, (width - (width // 11), height // 18))
        return self.m * (self.pos.y - self.c)
    	
    


class Object(pygame.sprite.Sprite):
    
    def __init__(self, object_shape, object_pos_x, object_pos_y, object_pos_z, object_width, object_height, object_length, object_radius):
        super().__init__()
        self.image = pygame.Surface((object_width * width_ratio, object_height * height_ratio))
        self.image.fill((0, 0, 0))
        self.image.set_colorkey((0, 0, 0))
        
        # Object values
        self.shape = object_shape
        self.pos = three_vec((object_pos_x, object_pos_y, object_pos_z))
        # x is width, y is height and z is length
        self.values = three_vec((object_width, object_height, object_length))
        self.radius = object_radius
         
        self.rect = self.image.get_rect()

    def display(self, z_position):

    
        # -------- Sphere -------- #

        
        if self.shape == "sphere":

            # Calculate radius at a given point
            sphere_position = self.pos
            sphere_radius = self.radius
            # (x - a)^2 + (y - b)^2 + (z - c)^2 = r^2
            try:
                circle_radius = math.sqrt(sphere_radius**2 - ((z_position - sphere_position.z)**2)) * width_ratio
                circle_colour = find_colour(self.shape, circle_radius, sphere_radius * width_ratio, 310)

                num_rects = 10
                num_rects = num_rects // 2
                rect_width = circle_radius / num_rects

                values = create_circle(circle_radius, rect_width)
                # if values:
                #     print(values)

                rect_list = []

                for i in range(len(values)):
                    # x, y, width, height
                    rect_list.append(pygame.Rect((sphere_position.x + values[i][0], sphere_position.y - values[i][1]), (rect_width, values[i][1] * 2)))
                    rect_list.append(pygame.Rect((sphere_position.x - values[i][0] - rect_width, sphere_position.y - values[i][1]), (rect_width, values[i][1] * 2)))

                
                # Draw circle
                pygame.draw.circle(displaysurface, circle_colour, (sphere_position.x, sphere_position.y), circle_radius, 0)
                
                # Draw approximated circle
                # for i in rect_list:
                #     pygame.draw.rect(displaysurface, circle_colour, i)

                return True, rect_list, circle_colour

            except ValueError:
                return False, 0, 0
            

        # -------- Cuboid -------- #

            
        elif self.shape == "cuboid":

            cuboid_position = self.pos
            cuboid_values = self.values
            dist_from_centre = abs(z_position - cuboid_position.z)
            
            # Check that object is on the 2D plane
            if cuboid_values.z / 2 > dist_from_centre:
                    
                # Draw rectangle
                self.image = pygame.Surface((cuboid_values.x, cuboid_values.y))
                self.image.fill(find_colour(self.shape, dist_from_centre, (cuboid_values.z / 2), 310))
                self.rect = self.image.get_rect()
                self.rect.center = (cuboid_position.x, cuboid_position.y)
                # pygame.draw.rect(displaysurface, (0, 255, 0, 0), (object_pos_x - object_width, object_pos_y - object_height / 4, object_height, object_width))
                return True, 0, 0
            else:
                self.kill()
                return False, 0, 0




class Checkpoint(pygame.sprite.Sprite):

    def __init__(self, object_pos_x, object_pos_y):
        super().__init__()

        self.width = 15 * width_ratio
        self.height = 90 * height_ratio

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        
        self.pos = two_vec((object_pos_x, object_pos_y))
        self.rect.center = self.pos




class Platform(pygame.sprite.Sprite):

    def __init__(self, object_pos_x, object_pos_y, object_width, object_height):
        super().__init__()

        self.width = object_width
        self.height = object_height

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((128, 128, 128))
        self.rect = self.image.get_rect()
        
        self.pos = two_vec((object_pos_x, object_pos_y))
        self.rect.center = self.pos 


                

    

		
# ---------------- FUNCTIONS ---------------- #






def display_fps():
    fps = str(int(FramePerSec.get_fps()))
    fps_text = debugger_font.render(fps, True, pygame.Color("coral"))
    return fps_text


def find_colour(shape, distance, radius, max_hsla):
    # Rainbow - red is 0, 100, 50 and violet is 310, 100, 50
    # Find colour of a sphere at a given point
    ratio = max_hsla / radius
    colour = pygame.Color(0)
    if shape == "sphere":
        colour.hsla = (ratio * distance, 100, 50)
    # Find colour of a cuboid at a given point
    elif shape == "cuboid":
        colour.hsla = (-1 * ratio * distance + 310, 100, 50)

    return colour


def create_circle(radius, rect_width):
    # y = sqrt(r**2 - (x - a)**2) + b
    # y = sqrt(r**2 - x**2)
    total_values = []

    # for i in range(0, int(radius), int(rect_width)):
    i = 0
    while i < radius:
        values = []
        # Add x value of the centrepoint (y value will always be 0)
        values.append(i - rect_width / 2)
        # Add the y value at a given x point
        values.append(math.sqrt(radius**2 - i**2))
        total_values.append(values)
        i += rect_width
    
    return total_values



def exit_menu(state):
    # Return objects initialised as True, state for the menu to return to and flag to decide if it should return to settings
    if pressed_keys[K_ESCAPE]:
        time.sleep(0.1)
        # Return in main menu
        if state == "settings":
            return True, "main", False
        elif state == "resolution" or state == "fps":
            return True, "settings", True
        # Return to main menu from level
        elif state == "level":
            return True, "menu", False


def mouse_check():
    # Check if mouse is outside of the pygame window
    mouse_focus = pygame.mouse.get_focused()
    if mouse_focus == 0:
        return True


def sprites_display(sprite_group):
    # Draw boxes and text
    sprite_group.draw(displaysurface)
    for i in sprite_group:
        i.menu_display()


def file_change(file, option, width, height, fps, current_level):
    # Rewrite data in settings.csv or current_level.csv
    file_read = csv.reader(open(file))
    lines = list(file_read)
    if option == "settings":
        lines[0][1] = str(width)
        lines[1][1] = str(height)
        lines[2][1] = str(fps)
    elif option == "level":
        lines[0][0] = str(current_level + 1)
    file_write = csv.writer(open(file, "w+", newline = ""))
    file_write.writerows(lines)

    if option == "settings":
        pygame.quit()
        sys.exit()
    

def gradient_display(display, left_colour, right_colour, surface_rect):
    try:
        colour_rect = pygame.Surface(( 2, 2 ))
        pygame.draw.line(colour_rect, left_colour,  ( 0,0 ), ( 0,1 ))
        pygame.draw.line(colour_rect, right_colour, ( 1,0 ), ( 1,1 ))
        # Stretch lines as required
        colour_rect = pygame.transform.smoothscale(colour_rect, (surface_rect.width, surface_rect.height))
        display.blit(colour_rect, surface_rect)
    except ValueError:
        pass


def sprite_collision(player, spheres_list):
    # Check for a collision with cuboid cross sections, platforms or the checkpoint
    rect_collided = pygame.sprite.spritecollideany(player, object_sprites)
    platform_collided = pygame.sprite.spritecollideany(player, platform_sprites)
    if rect_collided:
        rect_collided = rect_collided.rect
    elif platform_collided:
        rect_collided = platform_collided.rect

    sphere_collide_flag = False
    sphere_collided = []

    for sphere_rects in spheres_list:
        if spheres_list[spheres_index]:
            collision_check = pygame.Rect.collidelist(player.rect, sphere_rects)
            if collision_check != -1 and not sphere_collide_flag:
                sphere_collided = sphere_rects[collision_check]
                sphere_collide_flag = True
    
    
    if rect_collided != None:
        # print(rect_collided)
        object_collided = rect_collided
    else:
        # print(sphere_collided)
        object_collided = sphere_collided
    
    return object_collided





	

# ---------------- MAIN PROGRAM ---------------- #






# ---------------- CONSTANT LOOP ---------------- #


while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Set delta time for framerate
    dt = time.time() - last_time
    dt *= 60
    last_time = time.time()

    # Get the current pressed keys
    pressed_keys = pygame.key.get_pressed()


    # ---------------- MENU LOOP ---------------- #


    if game_state == "menu":
        # Run things to initialise only once
        if objects_initialised == True:
            #Play music
            pygame.mixer.music.play(-1)

            # Set menu state to either main menu or settings menu
            menu_state = "main"
            if 'settings_check' in globals():
                if settings_check:
                    menu_state = "settings"

            # Set gradient background information
            grad_colour1 = 255
            grad_colour2 = 0
            grad_flag = "down"

            # Set logo information
            logo_width = 1302 * 0.4 * width_ratio
            logo_height = 628 * 0.4 * height_ratio

            logo_image = pygame.image.load("logo_transparent_3.png")
            logo_image = pygame.transform.rotozoom(logo_image, 0, 0.4 * width_ratio)

            # Box positions and distance between boxes
            box_x = 640 * width_ratio
            box_y = 240 * height_ratio
            box_y_distance = 100 * height_ratio

            # Main menu boxes
            play_box = MenuBox(0, 0, 0, box_x, box_y, box_y_distance, "Play")
            create_box = MenuBox(0, 0, 0, box_x, box_y, box_y_distance * 2, "Create")
            settings_box = MenuBox(0, 0, 0, box_x, box_y, box_y_distance * 3, "Settings")
            exit_box = MenuBox(0, 0, 0, box_x, box_y, box_y_distance * 4, "Exit")

            # Settings boxes
            resolution_box = MenuBox(0, 0, 0, box_x, box_y, box_y_distance, "Resolution")
            fps_box = MenuBox(0, 0, 0, box_x, box_y, box_y_distance * 2, "FPS")

            # Resolution boxes
            box_y = 0
            nhd_box = MenuBox(640, 360, 0, box_x, box_y, box_y_distance * 2, "640 x 360")
            hd_box = MenuBox(1280, 720, 0, box_x, box_y, box_y_distance * 3, "1280 x 720")
            fhd_box = MenuBox(1920, 1080, 0, box_x, box_y, box_y_distance * 4, "1920 x 1080")
            qhd_box = MenuBox(2560, 1440, 0, box_x, box_y, box_y_distance * 5, "2560 x 1440")
            uhd_box = MenuBox(3840, 2160, 0, box_x, box_y, box_y_distance * 6, "3840 x 2160")

            # FPS boxes
            box_y = 0
            thirty = MenuBox(0, 0, 30, box_x, box_y, box_y_distance * 2, "30")
            fourty_five = MenuBox(0, 0, 45, box_x, box_y, box_y_distance * 3, "45")
            sixty = MenuBox(0, 0, 60, box_x, box_y, box_y_distance * 4, "60")
            hundred_fourty_four = MenuBox(0, 0, 144, box_x, box_y, box_y_distance * 5, "144")
            two_hundred_fourty = MenuBox(0, 0, 240, box_x, box_y, box_y_distance * 6, "240")

            menu_sprites = pygame.sprite.Group()
            settings_sprites = pygame.sprite.Group()
            resolution_sprites = pygame.sprite.Group()
            fps_sprites = pygame.sprite.Group()

            menu_sprites.add(play_box)
            menu_sprites.add(create_box)
            menu_sprites.add(settings_box)
            menu_sprites.add(exit_box)
            
            settings_sprites.add(resolution_box)
            settings_sprites.add(fps_box)

            resolution_sprites.add(nhd_box)
            resolution_sprites.add(hd_box)
            resolution_sprites.add(fhd_box)
            resolution_sprites.add(qhd_box)
            resolution_sprites.add(uhd_box)
            
            fps_sprites.add(thirty)
            fps_sprites.add(fourty_five)
            fps_sprites.add(sixty)
            fps_sprites.add(hundred_fourty_four)
            fps_sprites.add(two_hundred_fourty)

            objects_initialised = False

        # Display changing gradient background
        if grad_flag == "down":
            if grad_colour1 > 0:
                grad_colour1 -= 0.5 * dt
                grad_colour2 += 0.5 * dt
                # print("colour1: " + str(grad_colour1) + "\n" + "colour2: " + str(grad_colour2))
            else:
                grad_flag = "up"
        elif grad_flag == "up":
            if grad_colour1 < 255:
                grad_colour1 += 0.5 * dt
                grad_colour2 -= 0.5 * dt
                # print("colour1: " + str(grad_colour1) + "\n" + "colour2: " + str(grad_colour2))
            else:
                grad_flag = "down"

        displaysurface.fill(( 0,0,0 ))
        gradient_display(displaysurface, (255, 0, grad_colour1), (255, 0, grad_colour2), pygame.Rect( 0, 0, width, height))

        # Display logo
        displaysurface.blit(logo_image, (width / 2 - logo_width / 2, height / 5 - logo_height / 2))


        if menu_state == "main":
            sprites_display(menu_sprites)

            # Check if boxes clicked
            if play_box.click_check():
                objects_initialised = True
                game_state = "level"
            elif create_box.click_check():
                pass
            elif settings_box.click_check():
                menu_state = "settings"
            elif exit_box.click_check():
                pygame.quit()
                sys.exit()

        elif menu_state == "settings":
            sprites_display(settings_sprites)

            # Check if boxes clicked
            if resolution_box.click_check():
                menu_state = "resolution"
            elif fps_box.click_check():
                menu_state = "fps"

        elif menu_state == "resolution":
            # Flag used to set menu_state when initialising
            settings_check = True
            sprites_display(resolution_sprites)
            
            # Check if boxes clicked
            for box in resolution_sprites:
                if box.click_check():
                    width = box.res_width
                    height = box.res_height
                    file_change("settings.csv", "settings", width, height, fps, 0)

        elif menu_state == "fps":
            # Flag used to set menu_state when initialising
            settings_check = True
            sprites_display(fps_sprites)

            # Check if boxes clicked
            for box in fps_sprites:
                if box.click_check():
                    fps = box.box_fps
                    file_change("settings.csv", "settings", width, height, fps, 0)
        
        # Exit to previous menu if escape pressed
        exit_check = exit_menu(menu_state)
        if exit_check != None:
            # INITIALISING AGAIN IS NOT NEEDED WITHIN THE MENU
            # objects_initialised = exit_check[0]
            menu_state = exit_check[1]
            settings_check = exit_check[2]


    # ---------------- LEVEL LOOP ---------------- #

            
    elif game_state == "level":
        # Run things to initialise only once
        if objects_initialised == True:
            #Stop music
            pygame.mixer.music.stop()
            
            checkpoint_collided = False

            if "new_level" in globals() and new_level:
                checkpoint = None
                platform_list = None
                object_sprites.empty()
                platform_sprites.empty()
                slider.pos.y = 360 * height_ratio
            
            num_spheres = 0

            # -------- Go into the "levels" folder -------- #
            
            if current_level == num_levels:
                current_level = 0
                objects_initialised = True
                game_state = "menu"
                pygame.mixer.music.play(-1)

            script_dir = os.path.dirname(__file__)
            rel_path = "levels/level_" + str(current_level) + ".csv"
            abs_file_path = os.path.join(script_dir, rel_path)

            # -------- Read csv files -------- #


            object_list = []
            platform_list = []
            with open(abs_file_path) as objects_file:
                objects_reader = csv.reader(objects_file)
                for row in objects_reader:
                    # Pass in x, y, z, width, height, length, radius
                    if row[0] == "sphere" or row[0] == "cuboid":
                        object_shape = row[0]
                        object_pos_x = int(row[1]) * width_ratio
                        object_pos_y = int(row[2]) * height_ratio
                        object_pos_z = int(row[3])
                        object_width = int(row[4]) * width_ratio
                        object_height = int(row[5]) * height_ratio
                        object_length = int(row[6])
                        object_radius = int(row[7])
                        
                        object_passed = Object(object_shape, object_pos_x, object_pos_y, object_pos_z, object_width, object_height, object_length, object_radius)
                        object_list.append(object_passed)
                    elif row[0] == "flag":
                        checkpoint = Checkpoint(int(row[1]) * width_ratio, int(row[2]) * height_ratio)
                    elif row[0] == "player":
                        player = Player(int(row[1]) * width_ratio, int(row[2]) * height_ratio)
                    elif row[0] == "platform":
                        platform = Platform(int(row[1]) * width_ratio, int(row[2]) * height_ratio, int(row[4]) * width_ratio, int(row[5]) * height_ratio)
                        platform_list.append(platform)

            for i in object_list:
                if i.shape == "sphere":
                    num_spheres += 1
                    
                    
            # -------- Sprites -------- #
            if "new_level" in globals() and new_level:
                checkpoint_sprites.empty()
                
                if checkpoint:
                    checkpoint_sprites.add(checkpoint)
                player_sprites.empty()
                player_sprites.add(player)
                
            else:
                slider = Slider()
                slider_line = SliderLine()
                
                slider_sprites = pygame.sprite.Group()
                player_sprites = pygame.sprite.Group()
                object_sprites = pygame.sprite.Group()
                checkpoint_sprites = pygame.sprite.Group()
                platform_sprites = pygame.sprite.Group()

                slider_sprites.add(slider_line)
                slider_sprites.add(slider)
                player_sprites.add(player)
                checkpoint_sprites.add(checkpoint)

            for i in platform_list:
                platform_sprites.add(i)


            objects_initialised = False


        # -------- Background and slider -------- #
        
                
        # White background
        displaysurface.fill((255, 255, 255))
        # Display FPS in top right
        displaysurface.blit(display_fps(), (width - (width // 21), 0))
        
        # Move slider
        slider.move()
        # Display slider y-position
        z_position = slider.display()


        # -------- Exit back to menu -------- #


        exit_check = exit_menu(game_state)
        if exit_check != None:
            objects_initialised = exit_check[0]
            game_state = exit_check[1]
        

        # -------- Display objects -------- #
        
        spheres_index = 0
        spheres_list = [[]] * num_spheres

        for body in object_list:
            returned = body.display(z_position)
            if returned[0]:
                if body.shape == "cuboid":
                    if body not in object_sprites:
                        object_sprites.add(body)
                elif body.shape == "sphere":
                    spheres_list[spheres_index] = returned[1]
                    if body not in object_sprites:
                        object_sprites.add(body)
                        
                    spheres_index += 1


        spheres_index = 0


        checkpoint_collided = pygame.sprite.spritecollideany(player, checkpoint_sprites)
        if checkpoint_collided:
            file_change("current_level.csv", "level", 0, 0, 0, current_level)
            current_level += 1
            objects_initialised = True
            new_level = True

        player.move(spheres_list)
        
        
        # -------- Display sprites and update -------- #
        

        object_sprites.draw(displaysurface)
        platform_sprites.draw(displaysurface)
        checkpoint_sprites.draw(playersurface)
        player_sprites.draw(playersurface)
        slider_sprites.draw(displaysurface)
    

    pygame.display.update()
    FramePerSec.tick(fps)
