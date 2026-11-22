### FILE: pso/pso_simple.py
```python
import random

class Particle:
    def __init__(self, x0):
        """
        Initialize a particle with given initial position.
        
        Args:
            x0 (list): Initial position of the particle
        """
        # Current position of the particle
        self.position_i = []
        # Velocity of the particle
        self.velocity_i = []
        # Best position found by this particle
        self.pos_best_i = []
        # Best error found by this particle
        self.err_best_i = -1
        # Current error of this particle
        self.err_i = -1
        
        # Initialize particle with given initial position
        for i in range(len(x0)):
            self.velocity_i.append(random.uniform(-1, 1))
            self.position_i.append(x0[i])

    def evaluate(self, costFunc):
        """
        Evaluate the current particle's position using the given cost function.
        
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
        Update the particle's velocity using the given global best position.
        
        Args:
            pos_best_g (list): Global best position found so far
        """
        w = 0.5  # Inertia weight
        c1 = 1   # Cognitive parameter
        c2 = 2   # Social parameter
        
        for i in range(len(self.position_i)):
            r1 = random.random()
            r2 = random.random()
            
            # Update velocity using PSO formula
            self.velocity_i[i] = (w * self.velocity_i[i] + 
                                c1 * r1 * (self.pos_best_i[i] - self.position_i[i]) + 
                                c2 * r2 * (pos_best_g[i] - self.position_i[i]))

    def update_position(self, bounds):
        """
        Update the position of the particle based on its velocity.
        
        Args:
            bounds (list): List of tuples containing min and max bounds for each dimension
        """
        for i in range(len(self.position_i)):
            # Update position
            self.position_i[i] += self.velocity_i[i]
            
            # Adjust position if it goes out of bounds
            if self.position_i[i] > bounds[i][1]:
                self.position_i[i] = bounds[i][1]
            elif self.position_i[i] < bounds[i][0]:
                self.position_i[i] = bounds[i][0]

def minimize(costFunc, x0, bounds, num_particles, maxiter, verbose=False):
    """
    Minimize the given cost function using Particle Swarm Optimization (PSO) algorithm.
    
    Args:
        costFunc (function): Cost function to minimize
        x0 (list): Initial position
        bounds (list): List of tuples containing min and max bounds for each dimension
        num_particles (int): Number of particles in the swarm
        maxiter (int): Maximum number of iterations
        verbose (bool): Whether to print progress information
        
    Returns:
        tuple: (best_position, best_error) - Best solution found
    """
    # Initialize swarm
    swarm = []
    for _ in range(num_particles):
        swarm.append(Particle(x0))
    
    # Initialize global best
    pos_best_g = []
    err_best_g = -1
    
    # Main optimization loop
    for i in range(maxiter):
        if verbose:
            print(f"Iteration {i+1}")
        
        # Evaluate all particles
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
            print(f"Best error: {err_best_g}")
            print(f"Best position: {pos_best_g}")
            print()
    
    return pos_best_g, err_best_g
```