from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, literal_column, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Download, Newsletter, Visit
from app.schemas.dashboard import (
    DailyTraffic,
    DashboardStats,
    NewsletterDownloads,
    RecentDownload,
    Totals,
    TodayStats,
)


def _local_day(column):
    # The timezone is validated in Settings, so inlining it as a literal is safe. A literal
    # (instead of a bind parameter) keeps SELECT and GROUP BY expressions identical for Postgres.
    zone = literal_column(f"'{settings.app_timezone}'")
    return func.date(func.timezone(zone, column))


def get_dashboard_stats(db: Session, days: int = 30) -> DashboardStats:
    tz = ZoneInfo(settings.app_timezone)
    today = datetime.now(tz).date()
    start_of_today = datetime.combine(today, time.min, tzinfo=tz)
    since = datetime.combine(today - timedelta(days=days - 1), time.min, tzinfo=tz)

    def scalar(stmt) -> int:
        return db.scalar(stmt) or 0

    totals = Totals(
        newsletters=scalar(select(func.count(Newsletter.id))),
        visits=scalar(select(func.count(Visit.id))),
        unique_visitors=scalar(select(func.count(func.distinct(Visit.visitor_id)))),
        downloads=scalar(select(func.count(Download.id))),
    )
    today_stats = TodayStats(
        visits=scalar(select(func.count(Visit.id)).where(Visit.created_at >= start_of_today)),
        unique_visitors=scalar(
            select(func.count(func.distinct(Visit.visitor_id))).where(
                Visit.created_at >= start_of_today
            )
        ),
        downloads=scalar(
            select(func.count(Download.id)).where(Download.created_at >= start_of_today)
        ),
    )

    views_by_newsletter = dict(
        db.execute(
            select(Visit.newsletter_id, func.count(Visit.id))
            .where(Visit.newsletter_id.is_not(None))
            .group_by(Visit.newsletter_id)
        ).all()
    )
    download_count = func.count(Download.id)
    per_newsletter = [
        NewsletterDownloads(
            id=row.id,
            title=row.title,
            publication_date=row.publication_date,
            views=views_by_newsletter.get(row.id, 0),
            downloads=row.downloads,
        )
        for row in db.execute(
            select(
                Newsletter.id,
                Newsletter.title,
                Newsletter.publication_date,
                download_count.label("downloads"),
            )
            .outerjoin(Download, Download.newsletter_id == Newsletter.id)
            .group_by(Newsletter.id)
            .order_by(download_count.desc(), Newsletter.publication_date.desc())
        ).all()
    ]

    recent = [
        RecentDownload(
            newsletter_id=row.id,
            title=row.title,
            downloaded_at=row.created_at.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"),
        )
        for row in db.execute(
            select(Newsletter.id, Newsletter.title, Download.created_at)
            .join(Newsletter, Newsletter.id == Download.newsletter_id)
            .order_by(Download.created_at.desc())
            .limit(20)
        ).all()
    ]

    visit_day = _local_day(Visit.created_at).label("day")
    visit_rows = db.execute(
        select(visit_day, func.count(Visit.id), func.count(func.distinct(Visit.visitor_id)))
        .where(Visit.created_at >= since)
        .group_by(visit_day)
    ).all()
    download_day = _local_day(Download.created_at).label("day")
    download_rows = db.execute(
        select(download_day, func.count(Download.id))
        .where(Download.created_at >= since)
        .group_by(download_day)
    ).all()

    by_day: dict = {}
    for day, visits, unique in visit_rows:
        by_day[day] = {"visits": visits, "unique": unique, "downloads": 0}
    for day, downloads in download_rows:
        by_day.setdefault(day, {"visits": 0, "unique": 0, "downloads": 0})["downloads"] = downloads

    traffic = [
        DailyTraffic(
            date=day,
            visits=v["visits"],
            unique_visitors=v["unique"],
            downloads=v["downloads"],
        )
        for day, v in sorted(by_day.items(), reverse=True)
    ]

    return DashboardStats(
        timezone=settings.app_timezone,
        range_days=days,
        totals=totals,
        today=today_stats,
        downloads_by_newsletter=per_newsletter,
        recent_downloads=recent,
        daily_traffic=traffic,
    )
