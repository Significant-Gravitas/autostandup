from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from team_member import TeamMember
import pytz

class Scheduler:
    """Scheduler class to manage timed jobs for sending status requests.
    
    Attributes:
        scheduler: The APScheduler object.
    """
    
    def __init__(self) -> None:
        """Initialize the Scheduler object and start the APScheduler."""
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.scheduler.start()

    def add_job(self, func: callable, member: TeamMember) -> None:
        """Add a new job to the scheduler for a specific team member.
        
        Args:
            func: The function to call when the job is run.
            member: The TeamMember object for whom the job is added.
        """
        time_zone = pytz.timezone(member.time_zone)
        trigger = CronTrigger(day_of_week='mon,tue,wed,thu,fri', hour=10, timezone=time_zone)
        job = self.scheduler.add_job(func, trigger, args=[member])