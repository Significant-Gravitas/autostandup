from datetime import datetime, timedelta
import json
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
        self.load_weekly_post_data()

    def load_weekly_post_data(self):
        """
        Load the weekly post data from a JSON file.

        This function reads the 'weekly_post_data.json' file to get the ID and timestamp of the last
        weekly post. If the file does not exist, it sets the ID and timestamp to None.
        """
        try:
            with open("weekly_post_data.json", "r") as f:
                data = json.load(f)
            self.editable_weekly_post_id = data.get('post_id', None)
            self.weekly_post_timestamp = datetime.fromisoformat(data.get('timestamp')) if data.get('timestamp') else None
        except FileNotFoundError:
            self.editable_weekly_post_id = None
            self.weekly_post_timestamp = None
            # Create an empty weekly_post_data.json
            with open("weekly_post_data.json", "w") as f:
                json.dump({}, f)

    def save_weekly_post_data(self):
        """
        Save the weekly post data to a JSON file.

        This function writes the ID and timestamp of the current weekly post to the
        'weekly_post_data.json' file.
        """
        data = {
            'post_id': self.editable_weekly_post.id,
            'timestamp': datetime.now().isoformat()
        }
        with open("weekly_post_data.json", "w") as f:
            json.dump(data, f)

    async def initialize_post(self):
        """
        Initializes or retrieves the weekly status post on Discord.

        This function checks if a valid weekly post already exists for the current week.
        If it does, it retrieves that post. Otherwise, it sends a new message in the Discord
        channel with the list of team members and their statuses.
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

        member_list = '\n'.join([f"# `{m.name.ljust(self.max_name_length)} {'❓' * 5}`" for m in self.team_members])

        await self.channel.send(f"# Weekly Status Updates")
        await self.channel.send(f"## {start_date} to {end_date}")
        self.editable_weekly_post = await self.channel.send(f"{member_list}")

        self.save_weekly_post_data()  # Save the ID and timestamp after creating the post

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
        existing_line = self.editable_weekly_post.content[start_index:start_index + 5]  # 5 for the '❓' or '✅'

        # Find the first question mark and replace it with a checkmark
        first_question_mark = existing_line.find("❓")
        if first_question_mark == -1:
            return  # No question marks left, do nothing

        # Generate the new line for this member
        new_line = existing_line[:first_question_mark] + "✅" + existing_line[first_question_mark + 1:]

        # Update the weekly post
        new_content = self.editable_weekly_post.content[:start_index] + new_line + self.editable_weekly_post.content[start_index + 5:]
        await self.editable_weekly_post.edit(content=new_content)

    def has_all_checkmarks(self, member: TeamMember) -> bool:
        """
        Checks if a team member has all checkmarks (✅) in their status.

        Args:
            member: The TeamMember object to check.

        Returns:
            True if all checkmarks are present, False otherwise.
        """
        name_index = self.editable_weekly_post.content.find(member.name)
        if name_index == -1:
            return False  # Name not found, do nothing

        start_index = name_index + self.max_name_length + 1
        existing_line = self.editable_weekly_post.content[start_index:start_index + 5]
        
        return all([char == "✅" for char in existing_line])


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
