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
        # Initialize particle's current position
        self.position_i = []
        # Initialize particle's velocity
        self.velocity_i = []
        # Initialize particle's best known position
        self.pos_best_i = []
        # Initialize particle's best known error
        self.err_best_i = -1
        # Initialize particle's current error
        self.err_i = -1
        
        # Initialize velocity and position
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
            pos_best_g (list): Global best position
        """
        w = 0.5  # Inertia weight
        c1 = 1   # Cognitive parameter
        c2 = 2   # Social parameter
        
        for i in range(len(self.position_i)):
            r1 = random.random()
            r2 = random.random()
            
            # Update velocity
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
```