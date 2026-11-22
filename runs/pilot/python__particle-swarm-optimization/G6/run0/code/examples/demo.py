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
