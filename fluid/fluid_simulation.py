import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, Rectangle
import matplotlib.transforms as transforms

class FluidSimulation:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.density = np.zeros((height, width))
        self.velocity_x = np.zeros((height, width))
        self.velocity_y = np.zeros((height, width))
        self.vorticity = np.zeros((height, width))
        
        # Stronger initial conditions
        self.velocity_x[:, :] = 2.0  # Uniform wind from left to right
        self.density[:, 0:5] = 0.2  # Start with lower density
        self.smoke_buildup = 0.0    # Track smoke buildup
        
        # Add smoke particles for better visualization
        self.particles_x = np.random.uniform(0, width//4, 1000)
        self.particles_y = np.random.uniform(0, height, 1000)
        
        # Create more interesting initial conditions
        self.velocity_x[:, 0:width//4] = 3.0
        self.add_circular_vortex(width//4, height//2, 10)
        
        self.blade_angle = 0  # Add blade angle tracking
        self.wake_strength = 0.0  # Track wake development
        
    def add_circular_vortex(self, cx, cy, radius):
        """Add a circular vortex centered at (cx, cy) with given radius"""
        y, x = np.mgrid[0:self.height, 0:self.width]
        r = np.sqrt((x - cx)**2 + (y - cy)**2)
        mask = r <= radius
        
        # Calculate rotational vectors
        dx = -(y - cy) / (radius + 1e-6)  # avoid division by zero
        dy = (x - cx) / (radius + 1e-6)
        
        # Apply mask and add velocities
        self.velocity_x[mask] += dx[mask] * 2
        self.velocity_y[mask] += dy[mask] * 2
        
    def calculate_vorticity(self):
        # Compute rotation of the fluid
        dx = np.roll(self.velocity_y, -1, axis=1) - np.roll(self.velocity_y, 1, axis=1)
        dy = np.roll(self.velocity_x, -1, axis=0) - np.roll(self.velocity_x, 1, axis=0)
        self.vorticity = dx - dy
        
    def step(self, dt):
        # Gradual smoke source with buildup
        self.smoke_buildup = min(1.0, self.smoke_buildup + 0.001)  # Very slow buildup
        self.density[:, 0:5] = self.smoke_buildup * (0.8 + 0.2 * np.sin(plt.gcf().number * dt))
        
        # Add smoke diffusion
        self.density = np.clip(
            self.density + np.random.uniform(-0.01, 0.01, self.density.shape), 
            0, 1
        )
        
        # Slow down density advection
        dt_density = dt * 0.5  # Slower density movement
        
        # Update density using semi-Lagrangian advection with damping
        next_density = np.zeros_like(self.density)
        y, x = np.mgrid[0:self.height, 0:self.width]
        coords_x = x - self.velocity_x * dt_density
        coords_y = y - self.velocity_y * dt_density
        coords_x = np.clip(coords_x, 0, self.width-1)
        coords_y = np.clip(coords_y, 0, self.height-1)
        next_density = self.density[coords_y.astype(int), coords_x.astype(int)] * 0.995  # Slight dissipation
        
        self.density = next_density
        
        # Update particles
        self.particles_x += self.velocity_x[
            np.clip(self.particles_y.astype(int), 0, self.height-1),
            np.clip(self.particles_x.astype(int), 0, self.width-1)
        ] * dt
        
        self.particles_y += self.velocity_y[
            np.clip(self.particles_y.astype(int), 0, self.height-1),
            np.clip(self.particles_x.astype(int), 0, self.width-1)
        ] * dt
        
        # Reset particles that exit the domain
        reset_mask = (self.particles_x > self.width) | (self.particles_x < 0) | \
                    (self.particles_y > self.height) | (self.particles_y < 0)
        self.particles_x[reset_mask] = 0
        self.particles_y[reset_mask] = np.random.uniform(0, self.height, np.sum(reset_mask))
        
        # Add continuous source with oscillation
        t = plt.gcf().number * dt
        self.density[:, 0:2] = 1.0 + 0.3 * np.sin(t)
        
        # Update velocity field
        next_vel_x = self.velocity_x.copy()
        next_vel_y = self.velocity_y.copy()
        
        # Add turbine effect with improved wake
        center_x, center_y = self.width // 2, self.height // 2
        y, x = np.mgrid[0:self.height, 0:self.width]
        y_rel = y - center_y
        x_rel = x - center_x
        r = np.sqrt(x_rel**2 + y_rel**2)
        
        # Turbine influence zone
        blade_mask = r <= 15
        
        # Create realistic wake effect
        wake_length = 50
        wake_width = 25
        
        # Define wake region (cone shape)
        wake_mask = (x_rel > 0) & (np.abs(y_rel) < wake_width * (x_rel/wake_length + 1)) & (x_rel < wake_length)
        
        # Rotating turbine effect
        angle = self.blade_angle * np.pi / 180
        blade_effect_x = -np.sin(angle) * 4
        blade_effect_y = np.cos(angle) * 4
        
        # Apply blade effects
        next_vel_x[blade_mask] = blade_effect_x
        next_vel_y[blade_mask] = blade_effect_y
        
        # Apply wake effects with proper array dimensions
        wake_factor = np.exp(-x_rel/wake_length)
        self.wake_strength = min(1.0, self.wake_strength + 0.001)
        
        where_wake = wake_mask & (r > 15)
        
        # Update velocities safely
        next_vel_x[where_wake] *= (1 - 0.5 * wake_factor[where_wake] * self.wake_strength)
        
        # Add swirl in wake
        swirl_strength = 0.5 * wake_factor * self.wake_strength
        y_normalized = y_rel / (wake_width * (x_rel/wake_length + 1) + 1e-6)
        swirl = np.exp(-y_normalized**2) * np.sin(x_rel/10)
        
        next_vel_y[where_wake] += swirl[where_wake] * swirl_strength[where_wake]
        
        # Add small scale turbulence in wake
        if np.random.random() < 0.1:
            turb_shape = self.velocity_x.shape
            turbulence = np.random.normal(0, 0.2, size=turb_shape)
            next_vel_x[where_wake] += turbulence[where_wake] * wake_factor[where_wake] * self.wake_strength
            next_vel_y[where_wake] += turbulence[where_wake] * wake_factor[where_wake] * self.wake_strength
        
        # Update velocities
        self.velocity_x = next_vel_x
        self.velocity_y = next_vel_y
        
        # Calculate vorticity
        self.calculate_vorticity()

def main():
    width, height = 200, 100
    sim = FluidSimulation(width, height)
    
    # Modify colormap for better wake visualization
    colors = ['black', 'darkblue', 'royalblue', 'lightblue', 'white']
    n_bins = 256  # More color levels for smoother transition
    cmap = LinearSegmentedColormap.from_list('custom', colors, N=n_bins)
    
    # Setup figure
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 8))
    gs = plt.GridSpec(1, 20)
    ax = fig.add_subplot(gs[0, :19])
    cax = fig.add_subplot(gs[0, 19])
    
    # Initialize plots with adjusted parameters
    density_plot = ax.imshow(sim.density, cmap=cmap, vmin=0, vmax=1, interpolation='gaussian')
    plt.colorbar(density_plot, cax=cax, label='Smoke Density (%)')
    
    # Particle plot
    particles_plot = ax.plot([], [], 'w.', alpha=0.1, markersize=1)[0]
    
    # Streamplot setup
    skip = 8  # Increased skip for better performance
    x, y = np.meshgrid(np.arange(0, sim.width, skip), np.arange(0, sim.height, skip))
    streamplot = None

    def safe_remove_streamplot():
        nonlocal streamplot
        if streamplot is not None:
            try:
                for collection in streamplot.collections:
                    collection.remove()
                streamplot.lines.remove()
            except:
                pass
            streamplot = None

    # Add frame counter
    frame_count = 0
    
    # Add turbine visualization
    def create_turbine():
        # Create hub
        hub = Circle((width//2, height//2), radius=3, color='gray', zorder=3)
        ax.add_patch(hub)
        
        # Create blades
        blade_length = 15
        blade_width = 2
        blades = []
        for i in range(3):  # 3 blades
            blade = Rectangle(
                (width//2 - blade_width//2, height//2),
                blade_width, blade_length,
                color='white',
                zorder=2
            )
            ax.add_patch(blade)
            blades.append(blade)
        return hub, blades
    
    hub, blades = create_turbine()
    
    def update(frame):
        nonlocal frame_count
        frame_count += 1
        
        sim.step(0.1)
        sim.blade_angle += 5  # Rotate 5 degrees per frame
        
        # Update density and particles
        density_plot.set_array(sim.density)
        particles_plot.set_data(sim.particles_x, sim.particles_y)
        
        # Update turbine blades
        for i, blade in enumerate(blades):
            angle = sim.blade_angle + i * 120  # 120 degrees between blades
            trans = transforms.Affine2D() \
                .translate(-width//2, -height//2) \
                .rotate_deg(angle) \
                .translate(width//2, height//2)
            blade.set_transform(trans + ax.transData)
        
        # Update streamlines
        if frame_count % 5 == 0:
            # ...existing streamplot code...
            pass
        
        ax.set_title(f'Wind Turbine Simulation - Time: {frame_count*0.1:.1f}s')
        return [density_plot, particles_plot, hub] + blades
    
    # Update animation
    anim = FuncAnimation(
        fig,
        update,
        frames=None,
        interval=30,
        blit=True  # Enable blit for better performance
    )
    
    try:
        plt.show(block=True)
    except Exception as e:
        print(f"Animation error: {e}")
    finally:
        plt.close(fig)

if __name__ == "__main__":
    main()
