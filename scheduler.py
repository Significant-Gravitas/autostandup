from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from team_member import TeamMember
from weekly_post_manager import WeeklyPostManager
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

    def add_job(self, func: callable, member: TeamMember, weekly_post_manager: WeeklyPostManager) -> None:
        """Add a new job to the scheduler for a specific team member.
        
        Args:
            func: The function to call when the job is run.
            member: The TeamMember object for whom the job is added.
        """
        time_zone = pytz.timezone(member.time_zone)
        
        weekday_trigger = CronTrigger(day_of_week='mon,tue,wed,thu,fri', hour=10, timezone=time_zone)
        self.scheduler.add_job(func, weekday_trigger, args=[member, weekly_post_manager])
        
        weekend_trigger = CronTrigger(day_of_week='sat,sun', hour=11, timezone=time_zone)
        self.scheduler.add_job(func, weekend_trigger, args=[member, weekly_post_manager])