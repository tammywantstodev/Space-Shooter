import pygame
import os
import time
import random
pygame.font.init()
import math
pygame.font.init()
pygame.mixer.init()  

# Load sound effects
laser_sound = pygame.mixer.Sound(os.path.join("assets", "laser.wav"))
explosion_sound = pygame.mixer.Sound(os.path.join("assets", "explosion.ogg"))

WIDTH, HEIGHT = 850, 700
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter 🚀☄️")

# Load images (Same as before)
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))

def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


class Laser:
    def __init__(self, x, y, img):
        self.x=x
        self.y=y 
        self.img=img
        self.mask=pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y+=vel

    def off_screen(self, height):
        return not(self.y <= height and self.y >=0)
    
    def collision(self, obj):
        return collide(self, obj)
    

class Ship:
    COOLDOWN=30
    def __init__(self,x,y,health=100):
        self.x=x
        self.y=y
        self.health=health
        self.ship_img=None
        self.laser_img=None
        self.lasers=[]
        self.cool_down_counter=0
    
    def draw(self,window):
         window.blit(self.ship_img, (self.x, self.y))
         for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health-=10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter>=self.COOLDOWN:
            self.cool_down_counter=0
        elif self.cool_down_counter>0:
            self.cool_down_counter+=1


    def shoot(self):
        if self.cool_down_counter==0:
            laser=Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter=1

    def get_width(self):
        return self.ship_img.get_width()
    
    def get_height(self):
        return self.ship_img.get_height()

    
class Enemy(Ship):
    COLOR_MAP={
        "red":{"ship": RED_SPACE_SHIP, "laser": RED_LASER, "health": 150, "speed": 1},
        "green": {"ship": GREEN_SPACE_SHIP, "laser": GREEN_LASER, "health": 100, "speed": 2},
        "blue": {"ship": BLUE_SPACE_SHIP, "laser": BLUE_LASER, "health": 50, "speed": 3}

    }
    def __init__(self, x, y, color):
        super().__init__(x,y,health=self.COLOR_MAP[color]["health"])
        self.ship_img = self.COLOR_MAP[color]["ship"]
        self.laser_img = self.COLOR_MAP[color]["laser"]
        self.speed = self.COLOR_MAP[color]["speed"] 
        self.mask = pygame.mask.from_surface(self.ship_img)


    def move(self):
        self.y+=self.speed

    def shoot(self):
        if self.cool_down_counter==0:
            laser=Laser(self.x-17, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter=1
        
class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs, score):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        explosion_sound.play()
                        objs.remove(obj)
                        score += 2  # Increment score by 2 when an enemy is destroyed
                        if laser in self.lasers:
                            self.lasers.remove(laser)
        return score
    
    def draw(self, window):
        """Draws the player and their health bar"""
        super().draw(window)
        self.healthbar(window)  # Make sure to call this here!

    def healthbar(self, window):
        """Draws the player's health bar"""
        pygame.draw.rect(window, (255, 0, 0), 
                         (self.x, self.y + self.ship_img.get_height() + 10, self.ship_img.get_width(), 10))  # Red bar (full width)
        pygame.draw.rect(window, (0, 255, 0), 
                         (self.x, self.y + self.ship_img.get_height() + 10, 
                          self.ship_img.get_width() * (self.health / self.max_health), 10))  # Green (scaled to health)

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1
            laser_sound.play()



def main():
    run = True
    FPS = 60
    level = 0
    lives = 6
    score = 0  # Initialize score
    main_font = pygame.font.SysFont('comicsans', 50)
    lost_font = pygame.font.SysFont('comicsans', 60)
    enemies = []
    wave_length = 5
    player = Player(300, 630)
    clock = pygame.time.Clock()
    lost = False
    lost_count = 0

    def redraw_window():
        WIN.blit(BG, (0, 0))
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 0, 0))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        score_label = main_font.render(f"Score: {score}", 1, (255, 255, 0))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        WIN.blit(score_label, (WIDTH // 2 - score_label.get_width() // 2, 10))

        for enemy in enemies:
            enemy.draw(WIN)
        player.draw(WIN)

        if lost:
            lost_label = lost_font.render(f"You Lose! Final Score: {score}", 1, (255, 255, 255))
            WIN.blit(lost_label, (WIDTH // 2 - lost_label.get_width() // 2, 350))

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
        if lost:
            if lost_count > FPS * 3:
                run = False
            else:
                continue

        if len(enemies) == 0:
            level += 1
            wave_length += 3
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x > 0:
            player.x -= 5
        if keys[pygame.K_RIGHT] and player.x + player.get_width() < WIDTH:
            player.x += 5
        if keys[pygame.K_UP] and player.y > 0:
            player.y -= 5
        if keys[pygame.K_DOWN] and player.y + player.get_height() + 15 < HEIGHT:
            player.y += 5
        if keys[pygame.K_SPACE]:
            player.shoot()

        for enemy in enemies[:]:
            enemy.move()
            enemy.move_lasers(5, player)
            if random.randrange(0, 50) == 1:
                enemy.shoot()
            if collide(enemy, player):
                player.health -= 5
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)

        score = player.move_lasers(-5, enemies, score)

def main_menu():
    title_font=pygame.font.SysFont('comicsans', 70)
    run=True
    clock = pygame.time.Clock()
    base_y = 350  
    time_elapsed = 0
    while run:
        WIN.blit(BG, (0,0))
        time_elapsed += 0.05  
        float_offset = math.sin(time_elapsed * 2) * 10  
        text_y = base_y + float_offset

        title_label=title_font.render("Click the mouse to begin.", 1, (255,255,255))
        WIN.blit(title_label,(WIDTH/2-title_label.get_width()/2, text_y))
        pygame.display.update()
        for event in pygame.event.get():
            if event==pygame.QUIT:
                run=False
            if event.type==pygame.MOUSEBUTTONDOWN:
                main()
        clock.tick(60)
    pygame.quit()
            
main_menu()
