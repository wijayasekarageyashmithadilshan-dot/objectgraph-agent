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
