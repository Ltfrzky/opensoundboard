from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Board:
    id: int
    name: str
    color: str | None = None
    icon: str | None = None
    sort_order: int = 0

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Board name cannot be blank")
        object.__setattr__(self, "name", name)
