import turtle, math

screen = turtle.Screen()
screen.bgcolor("black")
screen.title("Solar System Model")

# Add text to the screen
text = turtle.Turtle()
text.hideturtle()
text.color("white")
text.penup()
text.goto(-100, 200)
text.write("Solar System Model", font=("Arial", 24, "bold"))



# Create Sun (stationary)
sun = turtle.Turtle()
sun.shape("circle")
sun.color("yellow")
sun.shapesize(2)
sun.penup()
sun.goto(0, 0)

# Create Earth
earth = turtle.Turtle()
earth.shape("circle")
earth.color("blue")
earth.shapesize(0.5)
earth.penup()

# Create Mars
mars = turtle.Turtle()
mars.shape("circle")
mars.color("red")
mars.shapesize(0.7)
mars.penup()

# Orbit setup
earth_orbit_radius = 100
mars_orbit_radius = 150
earth_angle = 0
mars_angle = 0
earth_speed = 1    # degrees per update
mars_speed = 0.8   # degrees per update



def update():
    global earth_angle, mars_angle
    # Update Earth's orbit position
    earth_x = earth_orbit_radius * math.cos(math.radians(earth_angle))
    earth_y = earth_orbit_radius * math.sin(math.radians(earth_angle))
    earth.goto(earth_x, earth_y)
    earth_angle = (earth_angle + earth_speed) % 360

    # Update Mars's orbit position
    mars_x = mars_orbit_radius * math.cos(math.radians(mars_angle))
    mars_y = mars_orbit_radius * math.sin(math.radians(mars_angle))
    mars.goto(mars_x, mars_y)
    mars_angle = (mars_angle + mars_speed) % 360

    screen.ontimer(update, 50)

if __name__ == '__main__':
    update()
    turtle.done()
