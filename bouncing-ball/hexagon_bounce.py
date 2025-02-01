# Installation:
# Ensure you have PyOpenGL and PyOpenGL_accelerate installed:
# pip install PyOpenGL PyOpenGL_accelerate

import sys, math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

# Physics and container parameters
GRAVITY = np.array([0.0, -9.81, 0.0])
DT = 0.01
FRICTION = 0.1
RESTITUTION = 0.8

BALL_RADIUS = 0.3
# Container: hexagon (regular) parameters. R is circumradius.
HEX_R = 5
FLOOR_Y = -5
CEILING_Y = 5

# Hexagon spin speed (radians per second)
HEX_ANGULAR_SPEED = 0.35

# Ball state
ball_pos = np.array([0.0, 0.0, 0.0])
ball_vel = np.array([2.0, 5.0, 1.0])  # initial velocity

hex_rotation = 50.0  # initial rotation angle


def get_hexagon_vertices(rotation):
    vertices = []
    for i in range(6):
        angle = math.radians(60 * i) + rotation
        x = HEX_R * math.cos(angle)
        z = HEX_R * math.sin(angle)
        vertices.append(np.array([x, z]))
    return vertices


def check_hexagon_collision():
    global ball_pos, ball_vel
    # Use only x and z components for hexagon collision.
    ball_hpos = np.array([ball_pos[0], ball_pos[2]])
    vertices = get_hexagon_vertices(hex_rotation)
    collided = False
    min_penetration = None
    collision_normal = None
    for i in range(6):
        p = vertices[i]
        q = vertices[(i + 1) % 6]
        midpoint = (p + q) / 2.0
        # Inward normal: from midpoint to center (which is [0,0])
        n = -midpoint
        norm = np.linalg.norm(n)
        if norm == 0:
            continue
        n = n / norm
        # Compute distance from ball to edge
        # Distance from point to line defined by p and q:
        # Since the inward direction is n, project (ball_hpos - p) onto n.
        d = np.dot(ball_hpos - p, n)
        if d < BALL_RADIUS:
            penetration = BALL_RADIUS - d
            if (min_penetration is None) or (penetration > min_penetration):
                min_penetration = penetration
                collision_normal = n
            collided = True
    if collided and (collision_normal is not None):
        # Correct position in x,z plane.
        ball_hpos = ball_hpos + collision_normal * min_penetration
        ball_pos[0], ball_pos[2] = ball_hpos[0], ball_hpos[1]
        # Reflect horizontal velocity.
        vel_h = np.array([ball_vel[0], ball_vel[2]])
        vn = np.dot(vel_h, collision_normal) * collision_normal
        vt = vel_h - vn
        vt = vt * (1 - FRICTION)
        vel_h = vt - vn * RESTITUTION
        ball_vel[0], ball_vel[2] = vel_h[0], vel_h[1]


def check_floor_ceiling_collision():
    global ball_pos, ball_vel
    # Floor
    if ball_pos[1] - BALL_RADIUS < FLOOR_Y:
        ball_pos[1] = FLOOR_Y + BALL_RADIUS
        ball_vel[1] = -ball_vel[1] * RESTITUTION
        # Apply friction to horizontal components on floor bounce.
        ball_vel[0] *= 1 - FRICTION
        ball_vel[2] *= 1 - FRICTION
    # Ceiling
    if ball_pos[1] + BALL_RADIUS > CEILING_Y:
        ball_pos[1] = CEILING_Y - BALL_RADIUS
        ball_vel[1] = -ball_vel[1] * RESTITUTION


def draw_hexagon():
    # Draw the hexagon walls as vertical lines and top & bottom outlines.
    vertices = get_hexagon_vertices(hex_rotation)
    # Bottom outline (at FLOOR_Y)
    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)
    for v in vertices:
        glVertex3f(v[0], FLOOR_Y, v[1])
    glEnd()
    # Top outline (at CEILING_Y)
    glBegin(GL_LINE_LOOP)
    for v in vertices:
        glVertex3f(v[0], CEILING_Y, v[1])
    glEnd()
    # Vertical edges and wall lines
    glBegin(GL_LINES)
    for v in vertices:
        glVertex3f(v[0], FLOOR_Y, v[1])
        glVertex3f(v[0], CEILING_Y, v[1])
    glEnd()


def draw_ball():
    glPushMatrix()
    glTranslatef(ball_pos[0], ball_pos[1], ball_pos[2])
    glColor3f(1, 0, 0)
    quad = gluNewQuadric()
    gluSphere(quad, BALL_RADIUS, 16, 16)
    gluDeleteQuadric(quad)
    glPopMatrix()



def main():
    global ball_pos, ball_vel, hex_rotation
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)

    # Debug: Print when window is created
    print("Simulation window created.")

    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

    gluPerspective(45, (display[0] / display[1]), 0.1, 100.0)
    glTranslatef(0.0, 0.0, -20)

    clock = pygame.time.Clock()

    pygame.display.set_caption("Hexagon Bounce")

    running = True
    while running:
        # Debug: tick count or loop indicator
        # print("Running simulation loop")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update physics
        ball_vel += GRAVITY * DT
        ball_pos += ball_vel * DT

        # Check collisions with floor/ceiling and hexagon walls.
        check_floor_ceiling_collision()
        check_hexagon_collision()

        # Update hexagon rotation
        hex_rotation += HEX_ANGULAR_SPEED * DT

        # Clear screen and draw scene
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # Draw container
        draw_hexagon()
        # Draw ball
        draw_ball()

        pygame.display.flip()
        clock.tick(100)  # Run simulation at ~100 FPS
        # if user click ESC or close the window
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()


    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
