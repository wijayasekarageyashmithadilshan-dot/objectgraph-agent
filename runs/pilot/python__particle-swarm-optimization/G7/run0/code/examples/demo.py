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
