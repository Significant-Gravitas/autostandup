from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from team_member import TeamMember
import pytz

class Scheduler:
    def __init__(self) -> None:
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.scheduler.start()

    def add_job(self, func: callable, member: TeamMember) -> None:
        time_zone = pytz.timezone(member.time_zone)
        trigger = CronTrigger(day_of_week='mon,wed,fri', hour=10, timezone=time_zone)
        job = self.scheduler.add_job(func, trigger, args=[member])
