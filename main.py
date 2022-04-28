import pygame, sys, os, random, math
from pygame.locals import *

pygame.init()

WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)

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

ENEMIES = pygame.sprite.Group()
ENEMY_TIMER = 0
MAX_ENEMIES = 1



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
        self.collision = pygame.rect.Rect((0,0),(96,112)) #I can't figure out how to offset the main rect relative to the image, so I made an individual rect here.
        self.collision.midbottom = (SCREEN_WIDTH / 4, SCREEN_HEIGHT)
        self.blade = pygame.rect.Rect((0,0),(0,0))

        self.size = 1
        self.max_health = 100
        self.health = self.max_health
        self.damage = 10
        self.attack_cooldown = 0.25
        self.move_speed = 12.5
        self.jump_force = 20
        self.gravity = 1

        self.is_idle = False
        self.facing_left = False
        self.airborne = False
        self.is_attacking = False
        self.velocity = 0
        self.knockback = 0
 
    def update(self, deltaTime):
        super().update(deltaTime)
        self.is_idle = True
        self.rect.midbottom = (self.collision.midbottom[0] - self.rectOffset[0] * self.size, self.collision.midbottom[1] - self.rectOffset[1] * self.size)

        if self.can_fight():
            pressed_keys = pygame.key.get_pressed()
            if (self.collision.left > 0 and pressed_keys[K_a]):
                self.move(-self.move_speed * self.size, 0)
                if (not self.is_attacking):
                    super().ChangeAnim("walk", rectX=20, rectY=15)
                self.is_idle = False
                self.facing_left = True
            if (self.collision.right < SCREEN_WIDTH and pressed_keys[K_d]):
                self.move(self.move_speed * self.size, 0)
                if (not self.is_attacking):
                    super().ChangeAnim("walk", rectX=20, rectY=15)
                self.is_idle = False
                self.facing_left = False
        else:
            self.curFrame = min(self.curFrame, len(animations[self.charDir][self.curAnim]) - 2)

        if (self.airborne):
            self.move(0, -self.velocity)
            if (self.can_fight() and not self.is_attacking):
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

        self.move(self.knockback * (1 if self.facing_left else -1), 0)
        self.knockback = max(self.knockback - 1, 0)
        self.collision.left = max(self.collision.left, 0)
        self.collision.right = min(self.collision.right, SCREEN_WIDTH)

        if self.is_attacking:
            if self.curFrame < 15:
                self.is_idle = False
            else:
                self.is_attacking = False
        if (self.can_fight() and self.is_idle):
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

        self.blade.update((self.collision.left - self.collision.width, self.collision.top) if self.facing_left else self.collision.topright, self.collision.size)
        for e in ENEMIES:
            if e.collision.colliderect(self.blade):
                e.hurt(self.damage * self.size)

    def hurt(self, damage, turn_around=False):
        self.health -= damage / self.size
        if (self.health <= 0):
            super().ChangeAnim("death", rectY=16)
        else:
            super().ChangeAnim("hurt")
        if turn_around:
            self.facing_left = not self.facing_left
        self.jump_stop()
        self.knockback = 15

    def grow(self, amount):
        self.size += amount
        self.rect.update(self.rect.topleft, (round(109 * self.sprite_size()), round(124 * self.sprite_size())))
        self.collision.update(self.collision.topleft, (round(96 * self.sprite_size()), round(112 * self.sprite_size())))

    def can_fight(self):
        return (self.health > 0 and self.knockback <= 0)

    def sprite_size(self):
        return 1 + (self.size - 1) / 2
 
    def draw(self, surface):
        #pygame.draw.rect(DISPLAYSURF, BLACK, self.rect)
        #pygame.draw.rect(DISPLAYSURF, BLACK, self.blade)
        #pygame.draw.rect(DISPLAYSURF, RED, self.collision)
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * self.sprite_size(), self.image.get_height() * self.sprite_size())) #pygame.transform.scale() scale the image according to the sprite's dimensions and self.size.
        surface.blit(pygame.transform.flip(self.image, self.facing_left, False), self.rect) #pygame.transform.flip() flips the image.



class Enemy(Animation):
    def __init__(self, charDir, target, size=1, dummy=False, defaultAnim="idle", animSpeed=1):
        super().__init__(charDir, defaultAnim, animSpeed)
        self.target = target
        self.size = size
        self.rect = pygame.rect.Rect((0,0), (round(100 * size), round(140 * size)))
        self.collision = pygame.rect.Rect((0,0), (72 * round(size), 96 * round(size))) #I can't figure out how to offset the main rect relative to the image, so I made an individual rect here.
        self.collision.midbottom = (SCREEN_WIDTH / 2, SCREEN_HEIGHT) if dummy else (random.random() * SCREEN_WIDTH, 0)

        self.health = 100
        self.damage = 20 * size
        self.dummy = dummy

        self.facing_left = dummy or random.choice([True, False]) #If the enemy is the starting dummy, then it will face left. Otherwise, its initial orientation is random.
        self.airborne = not dummy
        self.velocity = [0,0]
        self.attack_timer = random.random() + 2
        self.knockback = 0
 
    def update(self, deltaTime):
        super().update(deltaTime)
        self.rect.midbottom = (self.collision.midbottom[0] - self.rectOffset[0] * self.size, self.collision.midbottom[1] - self.rectOffset[1] * self.size)

        self.attack_timer -= deltaTime
        if (self.attack_timer <= 0 and not self.dummy):
            self.attack()

        if (self.airborne):
            self.move(self.velocity[0] * (-1 if self.facing_left else 1), -self.velocity[1])
            self.velocity[1] -= self.size
            if (self.collision.colliderect(self.target.collision) and self.curAnim == "jump"):
                self.orient()
                self.target.hurt(self.damage, self.facing_left == self.target.facing_left)
                self.velocity = [0,0]
                self.knockback = 15
                super().ChangeAnim("idle", 1, 0, -1)
            if (self.collision.bottom >= SCREEN_HEIGHT):
                self.move(0, SCREEN_HEIGHT - self.collision.bottom)
                self.airborne = False
                self.velocity = [0,0]
                super().ChangeAnim("idle", 1, 0, -1)
        else:
            self.move(0, SCREEN_HEIGHT - self.collision.bottom)
            self.orient()

        self.move(self.knockback * (1 if self.facing_left else -1), 0)
        self.knockback = max(self.knockback - 1, 0)
        self.collision.left = max(self.collision.left, 0)
        self.collision.right = min(self.collision.right, SCREEN_WIDTH)

    def move(self, x, y):
        self.rect.move_ip(x, y)
        self.collision.move_ip(x, y)

    def jump_stop(self):
        if (self.velocity[1] > 0):
            self.velocity[1] = 0

    def attack(self):
        self.airborne = True
        super().ChangeAnim("jump", 4, 0, 0)
        if (random.random() <= 0.5):
            self.velocity = [min(abs(self.target.collision.centerx - self.collision.centerx) * (random.random() * 0.4 + 1.8), SCREEN_WIDTH / 2) / 30, (random.random() * 10 + 10) * self.size]
            self.attack_timer += random.random() + 2
        else:
            self.velocity = [abs(self.target.collision.centerx - self.collision.centerx) * (random.random() * 0.2 + 0.9) / 60, (random.random() * 10 + 25) * self.size]
            self.attack_timer += random.random() + 3

    def hurt(self, damage):
        self.health -= damage / self.size
        if (self.health <= 0):
            self.kill()
            self.target.grow(0.1)
        self.jump_stop()
        self.knockback = 10

    def orient(self):
        self.facing_left = (self.collision.centerx >= self.target.collision.centerx)
 
    def draw(self, surface):
        #pygame.draw.rect(DISPLAYSURF, BLACK, self.rect)
        #pygame.draw.rect(DISPLAYSURF, RED, self.collision)
        self.image = pygame.transform.scale(self.image, (self.image.get_width() * self.size * 0.75, self.image.get_height() * self.size * 0.75)) #pygame.transform.scale() scale the image according to the sprite's dimensions and self.size.
        surface.blit(pygame.transform.flip(self.image, self.facing_left, False), self.rect) #pygame.transform.flip() flips the image.



GOB = Player("gob")
ENEMIES.add(Enemy("slime_purple", GOB, dummy=True))

while True:     
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if GOB.can_fight():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w:
                    GOB.jump()
                if event.key == pygame.K_SPACE:
                    GOB.attack()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    GOB.jump_stop()

    MAX_ENEMIES = math.ceil(GOB.size)
    deltaTime = 1/framerate.get_time() if framerate.get_time() > 0 else 1/FPS #framerate.get_time() returns the real framerate in FPS in between the previous two frames. The default value is 0 for the first two frames.
    ENEMY_TIMER -= deltaTime
    if ENEMY_TIMER <= 0:
        ENEMY_TIMER += 1.5
        if (len(ENEMIES.sprites()) < MAX_ENEMIES):
            ENEMIES.add(Enemy("slime_" + random.choice(["red","orange","yellow","green","blue","purple"]), GOB, 1 + (GOB.size - 1) * (random.random() / 10 + 0.45), defaultAnim="jump", animSpeed=4))
    
    
    GOB.update(deltaTime)
    [e.update(deltaTime) for e in ENEMIES.sprites()]
	
    DISPLAYSURF.fill(WHITE)
    GOB.draw(DISPLAYSURF)
    [e.draw(DISPLAYSURF) for e in ENEMIES.sprites()]
         
    pygame.display.update()
    framerate.tick(FPS)
