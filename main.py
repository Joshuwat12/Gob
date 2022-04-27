import pygame, sys, os
from pygame.locals import *
import random

pygame.init()

WHITE = (255,255,255)

FPS = 30
framerate = pygame.time.Clock()

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("Gob")

animations = {}
spriteDir = "Assets/Sprites"
for c in os.listdir(spriteDir):
  animations[c] = {}
  for p in os.listdir(f"{spriteDir}/{c}"):
    animations[c][p] = [pygame.image.load(f"{spriteDir}/{c}/{p}/{f}") for f in os.listdir(f"{spriteDir}/{c}/{p}")]



class Animation(pygame.sprite.Sprite):
    def __init__(self, charDir, defaultAnim="idle", animSpeed=1, rectX=0, rectY=0):
        super().__init__()
        self.charDir = charDir
        self.curAnim = defaultAnim
        self.curFrame = 0
        self.animSpeed = animSpeed
        self.rectOffset = (rectX, rectY)
        self.SetSprite()

    def update(self, deltaTime):
        self.curFrame += self.animSpeed / deltaTime / FPS
        self.SetSprite()

    def SetSprite(self):
        self.image = animations[self.charDir][self.curAnim][round(self.curFrame) % len(animations[self.charDir][self.curAnim])]
        
    def ChangeAnim(self, newAnim, animSpeed=1, rectX=0, rectY=0):
        if (self.curAnim != newAnim):
            self.curAnim = newAnim
            self.curFrame = 0
        self.animSpeed = animSpeed
        self.rectOffset = (rectX, rectY)



class Player(Animation):
    def __init__(self, charDir, defaultAnim="idle", animSpeed=1):
        super().__init__(charDir, defaultAnim, animSpeed)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2, 0)
        self.rect.bottom = SCREEN_HEIGHT
        self.collision = pygame.rect.Rect((0,0),(96,112)) #I can't figure out how to offset the main rect relative to the image, so I made an individual rect here.
		
        self.size = 1
        self.max_health = 100
        self.health = self.max_health
        self.damage = 10
        self.attack_cooldown = 0.25
        self.move_speed = 5
        self.jump_force = 17.5
        self.gravity = 1

        self.is_idle = False
        self.facing_left = False
        self.airborne = False
        self.is_attacking = False
        self.velocity = 0
 
    def update(self, deltaTime):
        #self.grow(deltaTime / 20)
        super().update(deltaTime)
        #SetSize(self.size) #Sets the player's sprite size
        self.rect.midbottom = (self.collision.midbottom[0] - self.rectOffset[0] * self.size, self.collision.midbottom[1] - self.rectOffset[1] * self.size)
        self.is_idle = True

        pressed_keys = pygame.key.get_pressed()
        if (self.collision.left > 0 and pressed_keys[K_a]): #TODO: Add wall collision if applicable.
            self.move(-self.move_speed * self.size, 0)
            if (not self.is_attacking):
                super().ChangeAnim("walk", rectX=20, rectY=15)
            self.is_idle = False
            self.facing_left = True
        if (self.collision.right < SCREEN_WIDTH and pressed_keys[K_d]): #TODO: Add wall collision if applicable.
            self.move(self.move_speed * self.size, 0)
            if (not self.is_attacking):
                super().ChangeAnim("walk", rectX=20, rectY=15)
            self.is_idle = False
            self.facing_left = False

        if (self.airborne):
            self.move(0, -self.velocity)
            if (not self.is_attacking):
                super().ChangeAnim("jump", 0, 15, 0)
                self.curFrame = min((1 - self.velocity / self.jump_force / self.size), 1) * 30 - 1 #This formula sets the animation frame proportional to the player's velocity.
            self.velocity -= self.gravity * self.size
            self.is_idle = False
            if (self.collision.bottom >= SCREEN_HEIGHT):
                self.move(0, SCREEN_HEIGHT - self.collision.bottom)
                self.airborne = False
                self.velocity = 0
        else:
            self.move(0, SCREEN_HEIGHT - self.collision.bottom)

        if self.is_attacking:
            if self.curFrame < 15:
                self.is_idle = False
            else:
                self.is_attacking = False
        if self.is_idle:
            super().ChangeAnim("idle", 1, 0, -1) #is_idle is used to determine if the animation should switch back to idle.

    def move(self, x, y):
        self.rect.move_ip(x, y)
        self.collision.move_ip(x, y)

    def jump(self):
        if (self.collision.bottom >= SCREEN_HEIGHT):
            self.airborne = True
            self.velocity = self.jump_force * self.size

    def jump_stop(self):
        if (self.velocity > 0):
            self.velocity = 0

    def attack(self):
        self.jump_stop()
        if (random.random() <= 1/3):
            super().ChangeAnim("attack1", rectX=40, rectY=-1)
        elif (random.random() <= 0.5):
            super().ChangeAnim("attack2", rectX=20, rectY=40)
        else:
            super().ChangeAnim("attack3", rectX=40)
        self.curFrame = 0
        self.is_attacking = True

    def grow(self, amount):
        self.size += amount
        if (self.rect.width / 109 < self.size):
            self.rect.inflate_ip(1,1)
        if (self.collision.width / 96 < self.size):
            self.collision.inflate_ip(1,1)
 
    def draw(self, surface):
        #pygame.draw.rect(DISPLAYSURF, (0,0,0), self.rect)
        #pygame.draw.rect(DISPLAYSURF, (255,0,0), self.collision)
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * self.size, self.image.get_height() * self.size)) #pygame.transform.scale() scale the image according to the sprite's dimensions and self.size.
        surface.blit(pygame.transform.flip(self.image, self.facing_left, False), self.rect) #pygame.transform.flip() flips the image.



GOB = Player("gob")

while True:     
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                GOB.jump()
            if event.key == pygame.K_SPACE:
                GOB.attack()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w:
                GOB.jump_stop()
    GOB.update(1/framerate.get_time() if framerate.get_time() > 0 else 1/FPS) #framerate.get_time() returns the real framerate in FPS in between the previous two frames. The default value is 0 for the first two frames.
	
    DISPLAYSURF.fill(WHITE)
    GOB.draw(DISPLAYSURF)
         
    pygame.display.update()
    framerate.tick(FPS)
