from datetime import date

from pydantic import BaseModel


class Totals(BaseModel):
    newsletters: int
    visits: int
    unique_visitors: int
    downloads: int


class TodayStats(BaseModel):
    visits: int
    unique_visitors: int
    downloads: int


class NewsletterDownloads(BaseModel):
    id: int
    title: str
    publication_date: date
    views: int
    downloads: int


class RecentDownload(BaseModel):
    newsletter_id: int
    title: str
    downloaded_at: str  # "YYYY-MM-DD HH:MM:SS" in the app timezone


class DailyTraffic(BaseModel):
    date: date
    visits: int
    unique_visitors: int
    downloads: int


class DashboardStats(BaseModel):
    timezone: str
    range_days: int
    totals: Totals
    today: TodayStats
    downloads_by_newsletter: list[NewsletterDownloads]
    recent_downloads: list[RecentDownload]
    daily_traffic: list[DailyTraffic]
