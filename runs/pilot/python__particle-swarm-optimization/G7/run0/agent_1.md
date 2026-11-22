### FILE: pso/cost_functions.py
```python
"""
Cost functions for PSO optimization.
"""

def sphere(x):
    """
    Calculate the sphere function value for a given input vector x.
    
    The sphere function is a common test function for optimization algorithms.
    It is defined as: f(x) = sum(x_i^2) for all i in range(len(x))
    
    Args:
        x (list): Input vector
        
    Returns:
        float: Sphere function value
    """
    return sum(xi**2 for xi in x)
```

### FILE: pso/pso_simple.py
```python
"""
Simple Particle Swarm Optimization implementation.
"""

import random

class Particle:
    """
    Particle class representing an individual in the swarm.
    """
    
    def __init__(self, x0):
        """
        Initialize a particle with initial position.
        
        duty: Particle.__init__
        
        Args:
            x0 (list): Initial position of the particle
        """
        self.position_i = []      # particle position
        self.velocity_i = []      # particle velocity
        self.pos_best_i = []      # best position individual
        self.err_best_i = -1      # best error individual
        self.err_i = -1           # error individual

        # Initialize particle with given initial position
        for i in range(len(x0)):
            self.velocity_i.append(random.uniform(-1, 1))
            self.position_i.append(x0[i])

    def evaluate(self, costFunc):
        """
        Evaluate the particle's current position using the cost function.
        
        duty: Particle.evaluate
        
        Args:
            costFunc (function): Cost function to evaluate
            
        Returns:
            float: Error value at current position
        """
        self.err_i = costFunc(self.position_i)

        # Check if current position is better than personal best
        if self.err_i < self.err_best_i or self.err_best_i == -1:
            self.pos_best_i = self.position_i.copy()
            self.err_best_i = self.err_i
        return self.err_i

    def update_velocity(self, pos_best_g):
        """
        Update particle velocity based on personal best and global best positions.
        
        duty: Particle.update_velocity
        
        Args:
            pos_best_g (list): Global best position
        """
        w = 0.5       # inertia weight
        c1 = 1        # cognitive parameter
        c2 = 2        # social parameter

        for i in range(len(self.position_i)):
            r1 = random.random()
            r2 = random.random()

            # Update velocity components
            vel_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            vel_social = c2 * r2 * (pos_best_g[i] - self.position_i[i])
            self.velocity_i[i] = w * self.velocity_i[i] + vel_cognitive + vel_social

    def update_position(self, bounds):
        """
        Update particle position based on current velocity.
        
        duty: Particle.update_position
        
        Args:
            bounds (list): List of tuples containing (min_bound, max_bound) for each dimension
        """
        for i in range(len(self.position_i)):
            # Update position
            self.position_i[i] += self.velocity_i[i]
            
            # Adjust position if it goes out of bounds
            if self.position_i[i] > bounds[i][1]:
                self.position_i[i] = bounds[i][1]
            elif self.position_i[i] < bounds[i][0]:
                self.position_i[i] = bounds[i][0]
```

### FILE: examples/demo.py
```python
#!/usr/bin/env python3
"""
Demo script for PSO implementation.
"""

from pso.pso_simple import Particle
from pso.cost_functions import sphere

def minimize(costFunc, x0, bounds, num_particles=15, maxiter=30, verbose=True):
    """
    Minimize the given cost function using Particle Swarm Optimization (PSO) algorithm.
    
    Args:
        costFunc (function): Cost function to minimize
        x0 (list): Initial position
        bounds (list): List of tuples containing (min_bound, max_bound) for each dimension
        num_particles (int): Number of particles in the swarm
        maxiter (int): Maximum number of iterations
        verbose (bool): Whether to print progress information
        
    Returns:
        tuple: (best_position, best_value)
    """
    # Create particles
    swarm = []
    for _ in range(num_particles):
        # Generate random initial position within bounds
        x0_new = [random.uniform(bounds[i][0], bounds[i][1]) for i in range(len(bounds))]
        swarm.append(Particle(x0_new))

    # Initialize global best
    pos_best_g = []
    err_best_g = -1

    # Main PSO loop
    for i in range(maxiter):
        if verbose:
            print(f"Iteration {i+1}")

        # Evaluate each particle
        for j in range(num_particles):
            err = swarm[j].evaluate(costFunc)

            # Update global best if needed
            if err < err_best_g or err_best_g == -1:
                pos_best_g = swarm[j].position_i.copy()
                err_best_g = err

        # Update velocities and positions
        for j in range(num_particles):
            swarm[j].update_velocity(pos_best_g)
            swarm[j].update_position(bounds)

        if verbose:
            print(f"Best solution: {pos_best_g}, Best value: {err_best_g}")

    return pos_best_g, err_best_g

if __name__ == "__main__":
    import random
    
    # Define problem parameters
    dimensions = 2
    bounds = [(-5, 5)] * dimensions  # Bounds for each dimension
    x0 = [random.uniform(bounds[i][0], bounds[i][1]) for i in range(dimensions)]
    
    # Run PSO
    print("Running PSO on sphere function...")
    best_position, best_value = minimize(sphere, x0, bounds, num_particles=15, maxiter=30, verbose=True)
    
    print(f"\nFinal result:")
    print(f"Best position: {best_position}")
    print(f"Best value: {best_value}")
```