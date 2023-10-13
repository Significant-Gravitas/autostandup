from datetime import datetime, timedelta
import pytz
from typing import List
from team_member import TeamMember

class WeeklyPostManager:
    """Manages the status post in a Discord channel."""
    
    def __init__(self, channel, team_members: List[TeamMember]):
        """
        Initializes a new WeeklyPostManager instance.

        Args:
            channel: The Discord channel where the weekly post will be sent.
            team_members: A list of TeamMember objects.
        """
        self.channel = channel
        self.team_members = team_members
        self.max_name_length = max([len(m.name) for m in team_members])
        self.editable_weekly_post = None

    async def initialize_post(self):
        """
        Initializes the weekly status post on Discord.

        This function sends a new message in the Discord channel with the list
        of team members and their statuses.
        """
        utc_now = pytz.utc.localize(datetime.utcnow())
        today_weekday = utc_now.weekday()
        last_monday = utc_now - timedelta(days=today_weekday)
        next_friday = last_monday + timedelta(days=4)

        start_date = self.format_date(last_monday)
        end_date = self.format_date(next_friday)

        member_list = '\n'.join([f"## `{m.name.ljust(self.max_name_length)} {'❌' * 5}`" for m in self.team_members])

        await self.channel.send(f"# Weekly Status Updates")
        await self.channel.send(f"### {start_date} to {end_date}")
        self.editable_weekly_post = await self.channel.send(f"{member_list}")

    async def update_post(self, member: TeamMember, weekday: int):
        """
        Updates a specific line in the weekly status post.

        Args:
            member: The TeamMember object whose status needs updating.
            weekday: The weekday index (0 for Monday, 1 for Tuesday, etc.)
        """
        # Fetch the current line for this member from the weekly post
        name_index = self.editable_weekly_post.content.find(member.name)
        if name_index == -1:
            return  # Name not found, do nothing

        start_index = name_index + self.max_name_length + 1  # Adding 1 for the space after the name
        existing_line = self.editable_weekly_post.content[start_index:start_index + 5]  # 5 for the '❌' or '✅'

        # Generate the new line for this member
        new_line = existing_line[:weekday] + "✅" + existing_line[weekday + 1:]

        # Update the weekly post
        new_content = self.editable_weekly_post.content[:start_index] + new_line + self.editable_weekly_post.content[start_index + 5:]
        await self.editable_weekly_post.edit(content=new_content)


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
