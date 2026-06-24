from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectName:
    value: str

    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("Project name cannot be empty")
        if len(self.value) > 100:
            raise ValueError("Project name is too long")
