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
    for  (i = 0; i<300; i++) {
      z = SquareZ(z) + z0;
      if (Module(z) > 2.0) {
       break;
      }
    }
    vec3 col = vec3(0.0, 0.0, 0.0);
    if (i<300) {
     col = vec3(1.0, 0.8, 0.4)*(i/30.0);
    }
    f_color = vec4(col, 1.0);
}
'''

program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
render_object = ctx.vertex_array(program, [(quad_buffer, '2f', 'vert')])

def surf_to_texture(surf):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex

def rotate2D(dxdy, a):
    s = m.sin(a);
    c = m.cos(a);
    return (dxdy[0]*c-dxdy[1]*s, dxdy[0]*s+dxdy[1]*c);

if __name__ == "__main__":
    t = 0
    speed = 0.0
    angle = 0.0
    zoom_speed = 0.0
    MAX_SPEED = 180.0
    MAX_ZOOM_SPEED = 2500
    MAX_ZOOM = 5.0
    MIN_ZOOM = 0.00001
    zoom = MAX_ZOOM
    dx = 0.0
    dy = 0.0
    s_dx = 0.0
    s_dy = 0.0
    speed = 0.0
    
    if speed < -180.0 or speed > 180.0:
        speed = 0.0
    
    pygame.display.set_caption(f'Zoom {round(1.0/zoom,3)} angle {-angle} deg xy_center {dx:.3f},{dy:.3f}')
    
    pygame.key.set_repeat(150)

    while True:
        display.fill((0, 0, 0))
    
        t += 1
    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if speed < MAX_SPEED:
                        speed += 0.5
                elif event.key == pygame.K_RIGHT:
                    if speed > -MAX_SPEED:
                        speed -= 0.5
                elif event.key == pygame.K_DOWN:
                    if zoom_speed < MAX_ZOOM_SPEED:
                        zoom_speed += 0.01
                elif event.key == pygame.K_UP:
                    if zoom_speed > -MAX_ZOOM_SPEED:
                        zoom_speed -= 0.01
                if event.key == pygame.K_a:
                    s_dx -= 5.0
                elif event.key == pygame.K_d:
                    s_dx += 5.0
                elif event.key == pygame.K_w:
                    s_dy += 5.0
                elif event.key == pygame.K_s:
                    s_dy -= 5.0
                elif event.key == pygame.K_SPACE:
                    speed = 0.0
                    zoom_speed = 0.0
                    s_dx = 0.0
                    s_dy = 0.0
                    dx = 0.0
                    dy = 0.0
                    angle = 0.0
                    zoom = MAX_ZOOM
            elif event.type == pygame.KEYUP:
                    speed = 0.0
                    zoom_speed = 0.0
                    s_dx = 0.0
                    s_dy = 0.0
       
        angle += speed
        s_dx1, s_dy1 = rotate2D((s_dx,s_dy), -angle*DEG_RAD)
        dx += s_dx1*zoom
        dy += s_dy1*zoom
    
        if zoom > MIN_ZOOM and zoom < MAX_ZOOM:
            zoom += zoom_speed*zoom
        if zoom <= MIN_ZOOM:
            zoom_speed = 0.0
            zoom = MIN_ZOOM+MIN_ZOOM/10.0
        if zoom >= MAX_ZOOM:
            zoom_speed = 0.0
            zoom = MAX_ZOOM-MIN_ZOOM
            
        pygame.display.set_caption(f'Zoom {round(1.0/zoom,3)} angle {angle} deg xy_center {dx/SCR_SIZE:.5f},{dy/SCR_SIZE:.5f} size {zoom:.5f}')
    
        program['resolution'] = (800.0,800.0)
        program['angle'] = angle*DEG_RAD
        program['offset'] = (dx,dy)
        program['scale'] = zoom
        render_object.render(mode=moderngl.TRIANGLE_STRIP)
    
        pygame.display.flip()
    
        clock.tick(25)
    
