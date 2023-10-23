from datetime import datetime, timedelta
import pytz
from typing import List
from weekly_posts.weekly_posts_db import WeeklyPostsDB
from team_members.team_member import TeamMember

class WeeklyPostManager:
    """Manages the status post in a Discord channel."""
    
    def __init__(self, channel, weekly_posts_db: WeeklyPostsDB):
        """
        Initializes a new WeeklyPostManager instance.
        """
        self.channel = channel
        self.weekly_posts_db = weekly_posts_db
        self.editable_weekly_post = None
        self.load_weekly_post_data()

    def load_weekly_post_data(self):
        """
        Load the weekly post data from the database.
        
        This method queries the 'weekly_posts' table to get the ID and timestamp of 
        the last weekly post. If no data exists, it sets the ID and timestamp to None.
        """
        data = self.weekly_posts_db.get_weekly_post_data()
        self.editable_weekly_post_id = data.get('post_id', None)
        self.weekly_post_timestamp = data.get('timestamp', None)

    def save_weekly_post_data(self):
        """
        Save the weekly post data to the database.
        
        This method inserts or updates the ID and timestamp of the current weekly post 
        in the 'weekly_posts' table.
        """
        self.weekly_posts_db.save_weekly_post_data(self.editable_weekly_post.id, datetime.now())

    async def initialize_post(self, team_members: List[TeamMember]):
        """
        Initializes or retrieves the weekly status post on Discord.

        This function checks if a valid weekly post already exists for the current week.
        If it does, it retrieves that post. Otherwise, it sends a new message in the Discord
        channel with the list of team members and their statuses.

        Args:
            team_members: A list of TeamMember objects to be displayed in the post.
        """
        current_week_number = datetime.now().isocalendar()[1]
        saved_week_number = self.weekly_post_timestamp.isocalendar()[1] if self.weekly_post_timestamp else None

        # Skip initialization if the post already exists and is for the current week
        if self.editable_weekly_post_id and current_week_number == saved_week_number:
            self.editable_weekly_post = await self.channel.fetch_message(self.editable_weekly_post_id)
            return

        utc_now = pytz.utc.localize(datetime.utcnow())
        today_weekday = utc_now.weekday()
        last_monday = utc_now - timedelta(days=today_weekday)
        next_sunday = last_monday + timedelta(days=6)

        start_date = self.format_date(last_monday)
        end_date = self.format_date(next_sunday)

        # Calculate the max name length for alignment purposes
        max_name_length = max([len(m.name) for m in team_members])

        member_list = []
        for m in team_members:
            # Include the streak with the fire emoji if the streak is greater than 0
            streak_str = f" {m.current_streak}🔥" if m.current_streak > 0 else ""

            # Construct the new line for the member with the updated information
            new_line = f"# `{m.name.ljust(max_name_length)} {'❓' * 5} {streak_str}`"
            member_list.append(new_line)

        member_list_str = '\n'.join(member_list)

        await self.channel.send(f"# Weekly Status Updates")
        await self.channel.send(f"## {start_date} to {end_date}")
        if member_list_str:
            self.editable_weekly_post = await self.channel.send(f"{member_list_str}")
            self.save_weekly_post_data()  # Save the ID and timestamp after creating the post

    async def rebuild_post(self, team_members: List[TeamMember]):
        """
        Rebuilds the entire weekly status post from the team members' data.

        Args:
            team_members: A list of TeamMember objects with updated statuses and streaks.
        """
        # If there are no team members, delete the post and return
        if not team_members:
            if self.editable_weekly_post:
                await self.editable_weekly_post.delete()
            self.editable_weekly_post = None
            return

        # Calculate the max name length for alignment purposes
        max_name_length = max([len(m.name) for m in team_members])

        member_list = []
        for m in team_members:
            # Get the streak and number of weekly check-ins for the member
            streak = m.current_streak
            check_ins = m.weekly_checkins

            # Generate the marks based on the number of check-ins
            marks = "✅" * check_ins + "❓" * (5 - check_ins)

            # Include the streak with the fire emoji if the streak is greater than 0
            streak_str = f" {streak}🔥" if streak > 0 else ""

            # Construct the new line for the member with the updated information
            new_line = f"# `{m.name.ljust(max_name_length)} {marks} {streak_str}`"
            member_list.append(new_line)

        new_content = '\n'.join(member_list)

        # Update the existing post or create a new one if it doesn't exist
        if self.editable_weekly_post:
            self.editable_weekly_post = await self.editable_weekly_post.edit(content=new_content)
        else:
            self.editable_weekly_post = await self.channel.send(new_content)

        # Save the ID and timestamp of the post
        self.save_weekly_post_data()

    def format_date(self, dt: datetime) -> str:
        """
        Formats a datetime object into a human-readable string.

        Args:
            dt: The datetime object to format.

        Returns:
            A human-readable date string.
        """
        suffix = ['th', 'st', 'nd', 'rd']
        day = int(dt.strftime('%d'))
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix_index = 0  # use 'th'
        else:
            suffix_index = day % 10  # use 'st', 'nd', 'rd' as appropriate

        return dt.strftime(f"%B {day}{suffix[suffix_index]}")
