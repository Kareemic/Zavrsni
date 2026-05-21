def calculate_standard_deviation(numerical_values: list) -> float:
    """
    Calculate the standard deviation of a list of numerical values.

    Standard deviation measures the amount of variation or dispersion
    in a dataset relative to its mean value.

    Args:
        numerical_values: A list of numeric values to analyze.

    Returns:
        The standard deviation as a floating point number.

    Raises:
        ValueError: If the input list is empty or contains fewer than two values.
        TypeError: If the input contains non-numeric values.
    """
    if not numerical_values:
        raise ValueError("Input list must not be empty.")
    if len(numerical_values) < 2:
        raise ValueError("Standard deviation requires at least two values.")
    if not all(isinstance(value, (int, float)) for value in numerical_values):
        raise TypeError("All values in the input list must be numeric.")

    total_count = len(numerical_values)
    arithmetic_mean = sum(numerical_values) / total_count
    squared_differences = [(value - arithmetic_mean) ** 2 for value in numerical_values]
    variance_value = sum(squared_differences) / (total_count - 1)
    standard_deviation_result = variance_value ** 0.5

    return standard_deviation_result


def find_outliers_using_std_deviation(
    numerical_values: list,
    threshold_multiplier: float = 2.0
) -> list:
    """
    Identify outliers in a dataset using standard deviation method.

    Values that fall more than threshold_multiplier standard deviations
    away from the mean are considered outliers.

    Args:
        numerical_values: A list of numeric values to analyze.
        threshold_multiplier: The number of standard deviations to use
                              as the outlier threshold. Defaults to 2.0.

    Returns:
        A list of values identified as outliers.
    """
    if not numerical_values:
        raise ValueError("Input list must not be empty.")

    arithmetic_mean = sum(numerical_values) / len(numerical_values)
    standard_deviation_value = calculate_standard_deviation(numerical_values)
    lower_bound_value = arithmetic_mean - (threshold_multiplier * standard_deviation_value)
    upper_bound_value = arithmetic_mean + (threshold_multiplier * standard_deviation_value)

    identified_outliers = [
        value for value in numerical_values
        if value < lower_bound_value or value > upper_bound_value
    ]

    return identified_outliers


def normalize_numerical_dataset(numerical_values: list) -> list:
    """
    Normalize a list of numerical values to the range [0, 1].

    Normalization is performed using min-max scaling, which transforms
    each value proportionally within the original range.

    Args:
        numerical_values: A list of numeric values to normalize.

    Returns:
        A list of normalized values in the range [0, 1].
    """
    if not numerical_values:
        raise ValueError("Input list must not be empty.")

    minimum_value = min(numerical_values)
    maximum_value = max(numerical_values)

    if minimum_value == maximum_value:
        return [0.0 for _ in numerical_values]

    value_range = maximum_value - minimum_value
    normalized_values = [
        (value - minimum_value) / value_range
        for value in numerical_values
    ]

    return normalized_values


def main_execution_function():
    """
    Main entry point demonstrating statistical analysis functions.
    """
    sample_numerical_dataset = [12, 15, 14, 10, 18, 45, 13, 11, 16, 14]

    calculated_deviation = calculate_standard_deviation(sample_numerical_dataset)
    print(f"Standard deviation: {calculated_deviation:.4f}")

    detected_outliers = find_outliers_using_std_deviation(sample_numerical_dataset)
    print(f"Detected outliers: {detected_outliers}")

    normalized_dataset = normalize_numerical_dataset(sample_numerical_dataset)
    print(f"Normalized values: {[round(v, 3) for v in normalized_dataset]}")


if __name__ == "__main__":
    main_execution_function()