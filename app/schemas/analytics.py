from datetime import date, datetime

from pydantic import BaseModel


class CountByType(BaseModel):
    type: str
    count: int


class CountBySource(BaseModel):
    source: str
    count: int


class CountBySeverity(BaseModel):
    severity: int
    count: int


class AnalyticsTimeRange(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    oldest_event_time: datetime | None = None
    latest_event_time: datetime | None = None


class AnalyticsSummaryRead(BaseModel):
    total_events: int
    time_range: AnalyticsTimeRange
    by_type: list[CountByType]
    by_source: list[CountBySource]
    by_severity: list[CountBySeverity]


class DailySeriesPoint(BaseModel):
    date: str
    count: int


class AnalyticsDailySeriesRead(BaseModel):
    series: list[DailySeriesPoint]


class HotspotPoint(BaseModel):
    latitude: float
    longitude: float
    count: int


class AnalyticsHotspotsRead(BaseModel):
    hotspots: list[HotspotPoint]


class EventRiskRead(BaseModel):
    event_id: int
    title: str
    type: str
    source: str | None = None
    severity: int
    event_time: datetime
    risk_score: float
    risk_level: str
    factors: dict[str, float]


class EventRiskListRead(BaseModel):
    items: list[EventRiskRead]
