import random


class Particle:
    def __init__(self, x0):
        """
        Initialize a particle with given initial position.

        # duty: Particle.__init__

        Args:
            x0 (list): Initial position of the particle
        """
        self.position_i = []          # particle position
        self.velocity_i = []          # particle velocity
        self.pos_best_i = []          # best position individual
        self.err_best_i = -1          # best error individual
        self.err_i = -1               # error individual

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

        # duty: Particle.update_velocity

        Args:
            pos_best_g (list): Global best position
        """
        w = 0.5       # inertia weight
        c1 = 1        # cognitive parameter
        c2 = 2        # social parameter

        for i in range(len(self.position_i)):
            r1 = random.random()
            r2 = random.random()

            # Update velocity
            vel_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            vel_social = c2 * r2 * (pos_best_g[i] - self.position_i[i])
            self.velocity_i[i] = w * self.velocity_i[i] + vel_cognitive + vel_social

    def update_position(self, bounds):
        """
        Update the position of the particle based on its velocity.

        # duty: Particle.update_position

        Args:
            bounds (list): List of tuples containing min and max bounds for each dimension
        """
        for i in range(len(self.position_i)):
            # Update position
            self.position_i[i] += self.velocity_i[i]

            # Adjust for bounds
            if self.position_i[i] > bounds[i][1]:
                self.position_i[i] = bounds[i][1]
            elif self.position_i[i] < bounds[i][0]:
                self.position_i[i] = bounds[i][0]
