from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from streaks.streaks_manager import StreaksManager
from team_members.team_member import TeamMember
from updates.updates_manager import UpdatesManager
from weekly_posts.weekly_post_manager import WeeklyPostManager
import pytz
from typing import Dict, List

class Scheduler:
    """Scheduler class to manage timed jobs for sending status requests.

    Attributes:
        scheduler: The APScheduler object.
        job_ids: A dictionary to store lists of job IDs for each member.
    """
    
    def __init__(self) -> None:
        """Initialize the Scheduler object and start the APScheduler."""
        self.scheduler: AsyncIOScheduler = AsyncIOScheduler()
        self.job_ids: Dict[int, List[str]] = {}  # Store job IDs indexed by member's Discord ID
        self.scheduler.start()

    def add_job(self, func: callable, member: TeamMember, weekly_post_manager: WeeklyPostManager, streaks_manager: StreaksManager, updates_manager: UpdatesManager) -> None:
        """Add a new job to the scheduler for a specific team member.
        
        Args:
            func: The function to call when the job is run.
            member: The TeamMember object for whom the job is added.
        """
        time_zone = pytz.timezone(member.time_zone)
        
        weekday_trigger = CronTrigger(day_of_week='mon,tue,wed,thu,fri', hour=10, timezone=time_zone)
        weekend_trigger = CronTrigger(day_of_week='sat,sun', hour=11, timezone=time_zone)

        weekday_job = self.scheduler.add_job(func, weekday_trigger, args=[member, weekly_post_manager, streaks_manager, updates_manager])
        weekend_job = self.scheduler.add_job(func, weekend_trigger, args=[member, weekly_post_manager, streaks_manager, updates_manager])

        self.job_ids.setdefault(member.discord_id, []).extend([weekday_job.id, weekend_job.id])

    def remove_job(self, discord_id: int) -> None:
        """Remove jobs for a specific team member.
        
        Args:
            discord_id: The Discord ID of the member for whom the job should be removed.
        """
        job_ids = self.job_ids.get(discord_id, [])
        for job_id in job_ids:
            self.scheduler.remove_job(job_id)

        if discord_id in self.job_ids:
            del self.job_ids[discord_id]  # Remove the job IDs from the dictionary
