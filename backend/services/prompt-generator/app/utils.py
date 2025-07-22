"""
Utility functions for the prompt generator service
"""

def complexity_string_to_float(complexity: str) -> float:
    """Convert string complexity to float value for internal calculations"""
    mapping = {
        "simple": 0.2,
        "moderate": 0.5,
        "complex": 0.8
    }
    return mapping.get(complexity, 0.5)  # default to moderate


def complexity_float_to_string(complexity: float) -> str:
    """Convert float complexity to string value"""
    if complexity <= 0.33:
        return "simple"
    elif complexity <= 0.66:
        return "moderate"
    return "complex"