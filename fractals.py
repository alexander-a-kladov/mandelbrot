#!/usr/bin/python3
import sys
from array import array

import math as m
import pygame
import moderngl

pygame.init()

SCR_SIZE=800
DEG_RAD=(3.1415926535 / 180.0)

screen = pygame.display.set_mode((SCR_SIZE, SCR_SIZE), pygame.OPENGL | pygame.DOUBLEBUF)
display = pygame.Surface((SCR_SIZE, SCR_SIZE))
ctx = moderngl.create_context()

clock = pygame.time.Clock()

quad_buffer = ctx.buffer(data=array('f', [
    # position (x, y), uv coords (x, y)
    -1.0, 1.0,   # topleft
    1.0, 1.0,    # topright
    -1.0, -1.0,  # bottomleft
    1.0, -1.0,  # bottomright
]))

vert_shader = '''
#version 430 core

in vec2 vert;

void main() {
    gl_Position = vec4(vert, 0.0, 1.0);
}
'''

frag_shader = '''
#version 430 core

uniform float angle;
uniform float scale;
uniform float brightness_div;
uniform int cycles;
uniform vec2 resolution;
uniform vec2 offset;

in vec2 uvs;
out vec4 f_color;

vec2 rotate2D(vec2 uv, float a) {
 float s = sin(a);
 float c = cos(a);
 return mat2(c, -s, s, c) * uv;
}

vec2 scale2D(vec2 uv) {
 return scale*uv;
}

float Dist(dvec2 uv) {
 return float(sqrt(uv.x*uv.x+uv.y*uv.y));
}

float Module(dvec2 uv) {
 return float(uv.x*uv.x+uv.y*uv.y);
} 

dvec2 SquareZ(dvec2 z) {
 return vec2(z.x*z.x - z.y*z.y, 2*z.x*z.y);
}

void main() {
    vec2 uv = (gl_FragCoord.xy - 0.5 * resolution.xy) / resolution.y;
    
    float value = 0.0;
    uv = rotate2D(uv, angle);
    dvec2 z0 = scale2D(uv)+offset/resolution.y;
    dvec2 z = dvec2(0.0,0.0);
    int i = 0;
    for  (i = 0; i<cycles; i++) {
      z = SquareZ(z) + z0;
      if (Module(z) > 2.0) {
       break;
      }
    }
    vec3 col = vec3(0.0, 0.0, 0.5);
    if (i<cycles) {
     col = vec3(1.0, 0.8, 0.4)*(i/brightness_div);
    } 
    f_color = vec4(col, 1.0);
}
'''

program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '2f', 'vert')])

def rotate2D(dxdy, a):
    s = m.sin(a);
    c = m.cos(a);
    return (dxdy[0]*c-dxdy[1]*s, dxdy[0]*s+dxdy[1]*c);

class ScreenData():
    def __init__(self):
        self.speed = 0.0
        self.angle = 0.0
        self.zoom_speed = 0.0
        self.MAX_SPEED = 180.0
        self.MAX_ZOOM_SPEED = 2500
        self.MAX_ZOOM = 5.0
        self.MIN_ZOOM = 0.00001
        self.MAX_CYCLES = 2000
        self.zoom = self.MAX_ZOOM
        self.dx = 0.0
        self.dy = 0.0
        self.s_dx = 0.0
        self.s_dy = 0.0
        self.speed = 0.0
        self.BRIGHT_MAX = 500
        self.BRIGHT_MIN = 50
        self.brightness_div = self.BRIGHT_MAX
        self.cycles = self.MAX_CYCLES
        
    def readEvents(self):
        redraw = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if self.speed < self.MAX_SPEED:
                        self.speed += 0.5
                    redraw = True
                elif event.key == pygame.K_RIGHT:
                    if self.speed > -self.MAX_SPEED:
                        self.speed -= 0.5
                    redraw = True
                elif event.key == pygame.K_DOWN:
                    if self.zoom_speed < self.MAX_ZOOM_SPEED:
                        self.zoom_speed += 0.01
                    redraw = True
                elif event.key == pygame.K_UP:
                    if self.zoom_speed > -self.MAX_ZOOM_SPEED:
                        self.zoom_speed -= 0.01
                    redraw = True
                if event.key == pygame.K_a:
                    self.s_dx -= 5.0
                    redraw = True
                elif event.key == pygame.K_d:
                    self.s_dx += 5.0
                    redraw = True
                elif event.key == pygame.K_w:
                    self.s_dy += 5.0
                    redraw = True
                elif event.key == pygame.K_s:
                    self.s_dy -= 5.0
                    redraw = True
                elif event.key == pygame.K_z:
                    if self.brightness_div < self.BRIGHT_MAX:
                        self.brightness_div += 10
                    redraw = True
                elif event.key == pygame.K_x:
                    if self.brightness_div > self.BRIGHT_MIN:
                        self.brightness_div -= 10
                    redraw = True
                elif event.key == pygame.K_SPACE:
                    self.speed = 0.0
                    self.zoom_speed = 0.0
                    self.s_dx = 0.0
                    self.s_dy = 0.0
                    self.dx = 0.0
                    self.dy = 0.0
                    self.angle = 0.0
                    self.brightness_div = self.BRIGHT_MAX
                    self.zoom = self.MAX_ZOOM
                    redraw = True
            elif event.type == pygame.KEYUP:
                    self.speed = 0.0
                    self.zoom_speed = 0.0
                    self.s_dx = 0.0
                    self.s_dy = 0.0
                    redraw = True
        return redraw

    def updateScreen(self):
        self.angle += self.speed
        s_dx1, s_dy1 = rotate2D((self.s_dx,self.s_dy), -self.angle*DEG_RAD)
        self.dx += s_dx1*self.zoom
        self.dy += s_dy1*self.zoom
    
        if self.zoom > self.MIN_ZOOM and self.zoom < self.MAX_ZOOM:
            self.zoom += self.zoom_speed*self.zoom
        if self.zoom <= self.MIN_ZOOM:
            self.zoom_speed = 0.0
            self.zoom = self.MIN_ZOOM+self.MIN_ZOOM/10.0
        if self.zoom >= self.MAX_ZOOM:
            self.zoom_speed = 0.0
            self.zoom = self.MAX_ZOOM-self.MIN_ZOOM
            
        pygame.display.set_caption(f'Brightness {1.0/self.brightness_div:.3f} Zoom {round(1.0/self.zoom,3)} angle {self.angle} deg xy_center {self.dx/SCR_SIZE:.5f},{self.dy/SCR_SIZE:.5f} size {self.zoom:.5f}')
    
        program['resolution'] = (float(SCR_SIZE),float(SCR_SIZE))
        program['cycles'] = self.cycles
        program['brightness_div'] = self.brightness_div
        program['angle'] = self.angle*DEG_RAD
        program['offset'] = (self.dx,self.dy)
        program['scale'] = self.zoom
        render_object.render(mode=moderngl.TRIANGLE_STRIP)
    
        pygame.display.flip()


if __name__ == "__main__":
    t = 0
    screen = ScreenData()
    pygame.key.set_repeat(50)

    while True:

        if (t==0 or screen.readEvents()):
            display.fill((0, 0, 0))
            screen.updateScreen();
        t += 1
        clock.tick(25)
    
