import math


def sphere(x):
    """
    Calculate the sphere function value for a given input vector x
    """
    return sum(xi**2 for xi in x)


class Global_functions:
    """Class containing global cost functions for optimization."""
    
    def sphere(x):
        """
        Calculate the sphere function value for a given input vector x.
        
        The sphere function is a common test function for optimization algorithms.
        It is defined as: f(x) = sum(xi^2) for i = 1 to n
        
        Args:
            x (list): Input vector
            
        Returns:
            float: Sphere function value
        """
        return sum([xi**2 for xi in x])
