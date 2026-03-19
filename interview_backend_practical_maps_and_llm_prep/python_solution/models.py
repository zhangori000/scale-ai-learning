from __future__ import annotations

from dataclasses import dataclass, field


Bounds = tuple[tuple[float, float], tuple[float, float]]


class RetryableProviderError(RuntimeError):
    pass


class NonRetryableProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class RestaurantRecord:
    place_id: str
    name: str
    lat: float
    lng: float
    rating: float | None = None
    user_rating_count: int = 0
    price_level: int | None = None
    primary_type: str | None = None
    types: tuple[str, ...] = ()


@dataclass(frozen=True)
class RestaurantSearchPage:
    restaurants: list[RestaurantRecord]
    next_page_token: str | None = None


@dataclass(frozen=True)
class CuisineSummary:
    count: int
    avg_price_level: float | None


@dataclass(frozen=True)
class RestaurantScanResult:
    restaurants: list[RestaurantRecord]
    saturated: bool
    pages_fetched: int


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    customer: str
    project_id: str
    category: str
    prompt: str
    response: str


@dataclass
class ReviewResult:
    task_id: str
    overall_score: float | None
    grammar_score: int | None
    style_score: int | None
    answer_score: int | None
    passes_threshold: bool | None
    issues: list[str] = field(default_factory=list)
    review_status: str = "completed"
    attempt_count: int = 1
    error_message: str | None = None


@dataclass(frozen=True)
class ReviewJobResult:
    job_id: str
    status: str
    total_count: int
    processed_count: int
    failed_count: int
    csv_url: str
    results: list[ReviewResult]


@dataclass(frozen=True)
class ResolvedPlace:
    query: str
    place_id: str
    display_name: str


@dataclass(frozen=True)
class TripPlan:
    ordered_stops: list[ResolvedPlace]
    total_drive_seconds: int
    algorithm: str

    def display_route(self) -> list[str]:
        return [stop.display_name for stop in self.ordered_stops]
