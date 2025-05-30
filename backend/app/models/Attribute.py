class Attribute:
    def __init__(self, name: str, base_score: int, habit_points: int = 0):
        # Add validation
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Attribute name must be a non-empty string")
        if not isinstance(base_score, int) or base_score < 1:
            raise ValueError("Base score must be a positive integer")

        self.name = name
        self.base_score = base_score
        self.habit_points = int(habit_points)

    def calculate_base_bonus(self) -> int:
        """Calculate the bonus from the base score using DnD rules (usually (score - 10) // 2)."""
        return (self.base_score - 10) // 2

    def calculate_habit_bonus(self) -> int:
        """Calculate additional bonus from habit points. You can adjust the formula as needed."""
        # For example, every 5 habit points add +1 bonus
        return self.habit_points // 5

    def total_bonus(self) -> int:
        """Total bonus is the sum of base bonus and habit bonus."""
        return self.calculate_base_bonus() + self.calculate_habit_bonus()

    def __str__(self):
        return (f"{self.name}: Score={self.base_score}, "
                f"Habit Points={self.habit_points}, "
                f"Total Bonus={self.total_bonus()}")