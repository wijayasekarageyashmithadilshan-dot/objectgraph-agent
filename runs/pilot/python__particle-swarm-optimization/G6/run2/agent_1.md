### FILE: pso/cost_functions.py
```python
import math

class Global_functions:
    """Class containing global cost functions for optimization."""
    
    def sphere(self, x):
        """
        Calculate the sphere function value for a given input vector x.
        
        The sphere function is a common test function for optimization algorithms.
        It is defined as: f(x) = sum(x_i^2) for i = 1 to n
        
        duty: Global_functions.sphere
        """
        return sum(xi**2 for xi in x)
```