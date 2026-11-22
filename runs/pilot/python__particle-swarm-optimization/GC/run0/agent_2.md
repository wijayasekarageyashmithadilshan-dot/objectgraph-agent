### FILE: pso/pso_simple.py
```python
import random

class Particle:
    def __init__(self, x0):
        """
        duty: Particle.__init__
        Initialize a particle with initial position and random velocity
        """
        self.position_i = []          # particle position
        self.velocity_i = []          # particle velocity
        self.pos_best_i = []          # best position individual
        self.err_best_i = -1          # best error individual
        self.err_i = -1               # error individual

        # Initialize position and velocity
        for i in range(len(x0)):
            self.velocity_i.append(random.uniform(-1, 1))
            self.position_i.append(x0[i])

    def evaluate(self, costFunc):
        """
        duty: Particle.evaluate
        Evaluate the particle's current position using the cost function
        """
        self.err_i = costFunc(self.position_i)

        # Check if the current position is better than the best position
        if self.err_i < self.err_best_i or self.err_best_i == -1:
            self.pos_best_i = self.position_i.copy()
            self.err_best_i = self.err_i

    def update_velocity(self, pos_best_g):
        """
        duty: Particle.update_velocity
        Update the particle's velocity based on global best position
        """
        w = 0.5       # inertia weight
        c1 = 1        # cognitive constant
        c2 = 2        # social constant

        for i in range(len(self.position_i)):
            r1 = random.random()
            r2 = random.random()

            # Update velocity
            vel_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            vel_social = c2 * r2 * (pos_best_g[i] - self.position_i[i])
            self.velocity_i[i] = w * self.velocity_i[i] + vel_cognitive + vel_social

    def update_position(self, bounds):
        """
        duty: Particle.update_position
        Update the particle's position based on its velocity
        """
        for i in range(len(self.position_i)):
            self.position_i[i] += self.velocity_i[i]

            # Adjust position if it goes out of bounds
            if self.position_i[i] > bounds[i][1]:
                self.position_i[i] = bounds[i][1]
            elif self.position_i[i] < bounds[i][0]:
                self.position_i[i] = bounds[i][0]
```

### FILE: pso/cost_functions.py
```python
def sphere(x):
    """
    Calculate the sphere function value for a given input vector x
    """
    return sum(xi**2 for xi in x)
```

### FILE: examples/demo.py
```python
from pso.pso_simple import Particle
from pso.cost_functions import sphere

def minimize(costFunc, x0, bounds, num_particles, maxiter, verbose=False):
    """
    Minimize the given cost function using Particle Swarm Optimization (PSO) algorithm
    """
    # Initialize particles
    swarm = []
    for _ in range(num_particles):
        particle = Particle(x0)
        swarm.append(particle)

    # Initialize global best
    pos_best_g = []
    err_best_g = -1

    # Main PSO loop
    for i in range(maxiter):
        if verbose:
            print(f"Iteration {i+1}")

        # Evaluate each particle
        for particle in swarm:
            particle.evaluate(costFunc)

            # Update global best if needed
            if particle.err_i < err_best_g or err_best_g == -1:
                pos_best_g = particle.position_i.copy()
                err_best_g = particle.err_i

        # Update velocity and position for each particle
        for particle in swarm:
            particle.update_velocity(pos_best_g)
            particle.update_position(bounds)

        if verbose:
            print(f"Best solution: {pos_best_g}, Best error: {err_best_g}")

    return pos_best_g, err_best_g

if __name__ == "__main__":
    # Example usage
    x0 = [5, 5]  # Initial position
    bounds = [[-10, 10], [-10, 10]]  # Bounds for each dimension
    num_particles = 10
    maxiter = 50
    verbose = True

    best_position, best_error = minimize(sphere, x0, bounds, num_particles, maxiter, verbose)
    
    print("Final result:")
    print(f"Best position: {best_position}")
    print(f"Best error: {best_error}")
```