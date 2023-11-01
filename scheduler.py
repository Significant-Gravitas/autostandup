from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from streaks.streaks_manager import StreaksManager
from team_members.team_member import TeamMember
from updates.updates_manager import UpdatesManager
from weekly_posts.weekly_post_manager import WeeklyPostManager
import pytz
from typing import Dict, List
from datetime import datetime

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
        self.weekly_post_job_id = None  # To store the ID of the scheduled weekly post job
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

    def schedule_weekly_post(self, func: callable, weekly_post_manager: WeeklyPostManager, streaks_manager: StreaksManager, team_members: List[TeamMember]) -> None:
        """Schedules the weekly post based on the latest time zone among the team members."""
        
        # Determine the latest time zone
        latest_time_zone = max([member.time_zone for member in team_members], key=lambda tz: pytz.timezone(tz).utcoffset(datetime.utcnow()))

        # Set the trigger for 9:10 AM in the earliest time zone on Monday
        trigger = CronTrigger(day_of_week='mon', hour=9, minute=10, timezone=latest_time_zone)

        # Schedule the function with the trigger
        job = self.scheduler.add_job(func, trigger, args=[weekly_post_manager, streaks_manager, team_members])
        self.weekly_post_job_id = job.id

    def unschedule_weekly_post(self) -> None:
        """Removes the weekly post job from the scheduler."""
        if self.weekly_post_job_id:
            self.scheduler.remove_job(self.weekly_post_job_id)
            self.weekly_post_job_id = None

    def get_all_scheduled_jobs(self, team_member_manager) -> List[str]:
        """Retrieve all scheduled jobs as a list of strings."""
        job_descriptions = []

        for job in self.scheduler.get_jobs():
            # Determine the associated team member by looking up the job ID in the job_ids dictionary
            member_discord_id = next((discord_id for discord_id, job_ids in self.job_ids.items() if job.id in job_ids), None)
            member_name = team_member_manager.find_member(member_discord_id).name if member_discord_id else "Unknown"

            # Calculate the remaining time until the next run
            now = datetime.now(job.next_run_time.tzinfo)  # Get the current time with the same timezone as the job's next_run_time
            remaining_time = job.next_run_time - now
            remaining_time_str = str(remaining_time).split('.')[0]  # Remove the microseconds part

            # If this job is the weekly post job
            if job.id == self.weekly_post_job_id:
                job_descriptions.append(f"ID: {job.id}, Type: Weekly Post, Next Run: {job.next_run_time}, Remaining Time: {remaining_time_str}, Func: {job.func.__name__}")
            else:
                job_descriptions.append(f"ID: {job.id}, Member: {member_name}, Next Run: {job.next_run_time}, Remaining Time: {remaining_time_str}, Func: {job.func.__name__}")

        return job_descriptions
