import os
from sys import argv

import pygame
from math import atan,sin,cos,pi,hypot
from random import random, randint
from scipy.constants import G
from os.path import join as pjoin
from os import getcwd
from time import sleep,time
import cv2 as cv

class Star():
    def __init__(self,radius,mass,color,centre_x,centre_y,speed_x,speed_y,winsize,scale_factor=1,trail_on=True,trail_len=20):  # scale_factor=1933333
        self.radius = radius
        self.mass = mass
        self.volume = 4/3*pi*self.radius**3
        self.density = self.mass/self.volume
        self.color = color
        self.x = centre_x
        self.y = centre_y
        self.x_dot = speed_x
        self.y_dot = speed_y
        self.scale_factor = scale_factor
        self.winsize = winsize
        self.x_new = centre_x  # the new value
        self.y_new = centre_y
        self.x_dot_new = speed_x
        self.y_dot_new = speed_y
        if trail_on:
            self.trail_x = [self.x for i in range(trail_len)]
            self.trail_y = [self.y for i in range(trail_len)]
        self.trail_on = trail_on
        self.trail_len = trail_len
        self.trail_spacing = 49   # record a trail every for 50 draw() called; this is a counter
    def draw(self,Surface,focused=False):
        changed = Surface     # passing by value is inefficient here, but I am lazy enough to wait for it
        # print([self.color,self.x,self.y,self.radius])
        if self.trail_on:
            for i in range(self.trail_len):
                pygame.draw.circle(changed,self.color,(int(self.trail_x[i]/self.scale_factor+self.winsize[0]/2),
                                               int(self.trail_y[i]/self.scale_factor+self.winsize[1]/2)),3)
        pygame.draw.circle(changed,self.color,(int(self.x/self.scale_factor+self.winsize[0]/2),
                                               int(self.y/self.scale_factor+self.winsize[1]/2)),self.radius)
        if focused:
            pygame.draw.circle(changed, '#e6e6e6',(self.winsize[0]/2+self.x,self.winsize[1]/2+self.y),radius=8,width=2)
        return changed
    def move(self,timelapse,otherStars):
        '''
        rather clumsily, one star read the position of the others in this way
        :param timelapse: delta t
        :param otherStars: some function out there gives this information
        :return: None
        '''
        t = timelapse
        acc_x = 0
        acc_y = 0
        for star in otherStars:
            dist = hypot(star.x-self.x,star.y-self.y)
            # acc = dist ** -2 * G * star.mass
            acc = dist ** -2 * star.mass
            acc_x += acc * (star.x-self.x) / dist
            acc_y += acc * (star.y-self.y) / dist
        self.x_dot_new += acc_x * t          # cannot change the old values just yet
        self.y_dot_new += acc_y * t
        self.x_new += (self.x_dot+self.x_dot_new)*t/2
        self.y_new += (self.y_dot+self.y_dot_new)*t/2
        # print(['a',self.x,self.y,self.x_dot,self.y_dot])
    def update(self):
        '''
        Apply when all the stars have their new values changed
        :return: None
        '''
        self.x_dot = self.x_dot_new
        self.y_dot = self.y_dot_new
        self.x = self.x_new
        self.y = self.y_new
        if self.trail_on and self.trail_spacing==0:
            self.trail_x.pop(0)
            self.trail_x.append(self.x)
            self.trail_y.pop(0)
            self.trail_y.append(self.y)
            self.trail_spacing = 49
        self.trail_spacing -= 1

class Space():
    def __init__(self,winsize,*stars,color=(0,100,0,255),grid=False,grid_color='#ffffff',grid_spacing=50,system='any'):
        self.stars = stars
        self.sur = pygame.Surface(winsize,pygame.SRCALPHA,32).convert_alpha()
        self.timepassed = 0
        self.winsize = winsize
        self.savestatus_index = 0  # if this is c++, I would use "static" in savestatus() to store this, which is breathtaking
        self.color = color
        self.grid = grid
        self.grid_color = grid_color
        self.grid_spacing = grid_spacing
        self.system = system
    def otherstars(self,thestar):
        ostar = []
        for i in self.stars:
            if i==thestar:
                continue
            ostar.append(i)
        return ostar
    def moveall(self,timelapse):
        self.sur.fill(self.color,rect=((0,0),self.winsize))
        if self.grid:
            n = int(self.winsize[0]//self.grid_spacing)+1
            for i in range(0,n):
                pygame.draw.line(self.sur,self.grid_color,(i*self.grid_spacing,0),(i*self.grid_spacing,self.winsize[1]),1)
            n = int(self.winsize[1]//self.grid_spacing)+1
            for i in range(0,n):
                pygame.draw.line(self.sur,self.grid_color,(0,i*self.grid_spacing),(self.winsize[0],i*self.grid_spacing),1)
        for star in self.stars:
            star.move(timelapse,self.otherstars(star)) # all calculated with old position values
        for star in self.stars:
            star.update()
            if self.system == 'binary':   #may I declare two variants of this function at the constructor of the class? So that I don't have to judge the boolean value every time
                self.sur = star.draw(self.sur,focused=True)
                dx = self.stars[1].x-self.stars[0].x
                dy = self.stars[1].y-self.stars[0].y
                try:
                    a = atan(dy/dx)
                    qudrant = 1 if (dy>=0 and dx>=0)else 2 if (dy<0 and dx>=0) else 3 if (dy>=0 and dx<0) else 4
                except ZeroDivisionError:
                    if dy > 0: a=pi/2
                    else: a=-pi/2
            else:self.sur = star.draw(self.sur)
            self.timepassed += timelapse
        if self.system == 'binary':
            if qudrant in (1,2):
                pygame.draw.line(self.sur, '#e6e6e6',
                                 (int(self.winsize[0]/2+self.stars[0].x + 8 * cos(a)), int(self.winsize[1]/2+self.stars[0].y + 8 * sin(a))), # TODO as you can see, play with trignometrical function more to make it better.Line aren't drawn within circles
                                 (int(self.winsize[0]/2+self.stars[1].x - 8 * cos(a)), int(self.winsize[1]/2+self.stars[1].y - 8 * sin(a))), width=2)
            elif qudrant in (3,4):
                pygame.draw.line(self.sur, '#e6e6e6',
                                 (int(self.winsize[0] / 2 + self.stars[0].x - 8 * cos(a)),
                                  int(self.winsize[1] / 2 + self.stars[0].y - 8 * sin(a))),
                                 (int(self.winsize[0] / 2 + self.stars[1].x + 8 * cos(a)),
                                  int(self.winsize[1] / 2 + self.stars[1].y + 8 * sin(a))), width=2)
            pygame.draw.circle(self.sur, '#e6e6e6', (  ## the centre of mass
            int(self.winsize[0]/2+self.stars[0].x + dx * self.stars[1].mass / (self.stars[0].mass + self.stars[1].mass)),
            int(self.winsize[1]/2+self.stars[0].y + dy * self.stars[1].mass / (self.stars[0].mass + self.stars[1].mass))), 3.)
        return self.sur
    def savestatus(self,path=getcwd(),name='image',index=None):
        if index:
            pygame.image.save(self.sur, pjoin(path, name + '-%d.png' % index))
        else:
            pygame.image.save(self.sur, pjoin(path, name + '-%d.png' % self.savestatus_index))

def rndGen(lowerlimit,upperlimit):
    return lowerlimit+random()*(upperlimit-lowerlimit)

def chaosSpaceGenerator(winsize,*starYouLike,starnum=7,max_x_velocity=0.01,min_x_velocity=-0.01,max_y_velocity=0.01,min_y_velocity=-0.01,max_x_pos=500,min_x_pos=-500,max_y_pos=275, min_y_pos=-275, max_mass=60,min_mass=5,max_radius=30,min_radius=5,color='#1a1a1a',grid=True,grid_color='#003399'):
    stars=[*starYouLike]
    for i in range(starnum):
        stars.append(Star(rndGen(min_radius,max_radius),rndGen(min_mass,max_mass),tuple([randint(0,255)for i in range(4)]),rndGen(min_x_pos,max_x_pos),rndGen(min_y_pos,max_y_pos),rndGen(min_x_velocity,max_x_velocity),rndGen(min_y_velocity,max_y_velocity),winsize))
    return Space(winsize, *stars,color=color,grid=grid,grid_color=grid_color)

def binarySystemGenerator(winsize,max_x_velocity=1,min_x_velocity=-1,max_y_velocity=1,min_y_velocity=-1,max_x_pos=500,min_x_pos=-500,max_y_pos=275, min_y_pos=-275, max_mass=160,min_mass=50,max_radius=5,min_radius=40,color='#1a1a1a',grid=True,grid_color='#003399'):
    return Space(winsize,Star(rndGen(min_radius,max_radius),rndGen(min_mass,max_mass),tuple([randint(0,255)for i in range(4)]),rndGen(min_x_pos,max_x_pos),rndGen(min_y_pos,max_y_pos),rndGen(min_x_velocity,max_x_velocity),rndGen(min_y_velocity,max_y_velocity),winsize)
    ,Star(rndGen(min_radius, max_radius), rndGen(min_mass, max_mass), tuple([randint(0, 255) for i in range(4)]),
         rndGen(min_x_pos, max_x_pos), rndGen(min_y_pos, max_y_pos), rndGen(min_x_velocity, max_x_velocity),
         rndGen(min_y_velocity, max_y_velocity), winsize),color=color,grid=grid,grid_color=grid_color,system='binary'
    )


def timeEstimate(timespent,percentagefinished):
    if percentagefinished==0 or percentagefinished==100:
        return '--'
    t = timespent / percentagefinished * (100-percentagefinished)
    h = int(t//3600)
    m = int(t%3600//60)
    s = t%60
    a=''
    if h:
        a+=str(h)+'hr'
    if m:
        a+= str(m)+'min'
    if s:
        a+= '%.2fsec'%s
    return a

def main(I,mode,total_frame):
    # ---------video-output-controls----------------
    IMG_PATH = pjoin(getcwd(),"img")
    if "img" not in os.listdir():
        os.mkdir("img")
    TOTAL_FRAME = total_frame
    CALCs_PER_FRAME = 10
    GALAXY_MODE = mode
    # -----------norms-------------
    pygame.init()
    timelapse = 1
    wordtype = pygame.font.SysFont('SimHei',14)
    winsize = (1920,1080)
    win = pygame.display.set_mode(winsize,pygame.NOFRAME, 32)
    '''In my coordinate of the universe, the centre of the screen is (0,0), top-left corner is (-winsize[0]/2,-winsize[1]/2'''
    TRAIL_LEN=40
    #-----------------fake-solar-system----------------- this is very fake
    sun = Star(20, 60, '#ff9900', 0, 0, 0, 0,winsize,trail_len=100)
    # mercury = Star(5,1,'#e92f41',-50,0,0,1,winsize,trail_len=10)
    # venus = Star(12,3.5,'#ff9900',0,-125,0.8,0,winsize,trail_len=TRAIL_LEN)
    earth = Star(10, 3, '#3399ff', 0, -250, 0.4, 0, winsize, trail_len=TRAIL_LEN)
    # mars = Star(8,5,'#ff0000',0,-375,0.25,0,winsize,trail_len=TRAIL_LEN)
    # jupiter = Star(30,10,'#996633',-400,0,0,-0.5,winsize,trail_len=TRAIL_LEN)
    # saturn = Star(40,15,'#993300',450,0,0,0.7,winsize,trail_len=TRAIL_LEN)
    # uranus = Star(7,5,'#9900cc',650,0,0,0.6,winsize,trail_len=TRAIL_LEN)
    # neptune = Star(5,5,'#0059b3',-670,0,0,0.1,winsize,trail_len=TRAIL_LEN)
    #----------------real-solar-system------------------
    # radius = [696000,2440,6052,6378,3397,71492,60268,25559,24764] # km
    # masses = [1.989e30, 3.302e23, 4.869e24, 5.965e24,6.4219e23, 1.9e27, 5.6846e26, 8.6810e25, 1.0247e26]
    # distToSun = [0,58_000_000,]
    #
    if GALAXY_MODE == 'solar-system-default':
        space = Space(winsize,sun,mercury,earth,venus,mars,jupiter,saturn,uranus,neptune,color='#1a1a1a',grid=True,grid_color='#003399')
        # space = Space(winsize,sun,mercury,venus,earth,color='#1a1a1a',grid=True,grid_color='#003399')
    elif GALAXY_MODE == 'binary-maniac':
        # space = Space(winsize,sun,earth,color='#1a1a1a',grid=True,grid_color='#003399',system='binary')
        space = binarySystemGenerator(winsize)
    elif GALAXY_MODE == 'non-repeating':
        space = chaosSpaceGenerator(winsize,sun,color='#1a1a1a',grid=True,grid_color='#003399')
    else:
        raise RuntimeError
    start_time = time()
    for i in range(TOTAL_FRAME*CALCs_PER_FRAME+1):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()
        win.blit(space.moveall(timelapse),(0,0))
        # win.blit(wordtype.render('\n'.join(['vx:',str(earth.x_dot),'vy:',str(earth.y_dot)]),False,(255,255,255)),(0,0))
        # win.blit(wordtype.render('\n'.join(['vx:',str(sun.x_dot),'vy:',str(sun.y_dot)]),False,(255,255,255)),(0,25))
        win.blit(wordtype.render("Age of the universe: %d unit"%(space.timepassed),False,'#ffffff00'),(0,0))
        if i%CALCs_PER_FRAME == 0:
            space.savestatus(IMG_PATH,'star',i//CALCs_PER_FRAME)
            prog = 100*i//((TOTAL_FRAME+1)*CALCs_PER_FRAME)
            print("\r Generating image [{} {}%](Estimate time:{})".format('#'*(prog*20//100)+'='*(20-prog*20//100),prog,timeEstimate(time()-start_time,prog)),end='')
        pygame.display.update()
        # sleep(0.05)
    print("\r Generating image [" + "#" * 20 + " 100%](Time used: {:.2f})".format(time()-start_time))
    # 可以用(*'DVIX')或(*'X264'),如果都不行先装ffmepg: sudo apt-get install ffmepg
    # fourcc = cv.VideoWriter_fourcc(*'XVID')
    fourcc = cv.VideoWriter_fourcc(*'XVID')
    fps = 25
    videoWriter = cv.VideoWriter(f'Star{I}.avi',fourcc,25,winsize, isColor=False)
    start_time = time()
    for i in range(TOTAL_FRAME+1):
        frame = cv.imread(pjoin(IMG_PATH,'star-%d.png'%i))
        videoWriter.write(frame)
        prog = 100 * i // (TOTAL_FRAME+1)
        print("\r Converting to video [{} {}%](Estimate time: {})".format('#' * (prog*20//100) + '=' * (20 - prog*20//100), prog,timeEstimate(time()-start_time,prog)),end='')
    videoWriter.release()
    print("\r Converting to video [" + "#" * 20 + " 100%](Time used: {:.2f})".format(time()-start_time))

if __name__=='__main__':
    try:
        I = int(argv[1])
        if argv[2]=='-b':
            mode = 'binary-maniac'
        elif argv[2]=='-r':
            mode = 'non-repeating'
        else:
            raise Exception('invalid mode argument (%s)'%argv[2])
        total_frame=int(argv[3])
        # mode = 'solar-system-default'
    except:
        raise Exception('a number given (%s or %s) incorrect.'%(argv[1], argv[3]))
    main(I,mode,total_frame)