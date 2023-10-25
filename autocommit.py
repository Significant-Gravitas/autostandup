#!/bin/sh
''':'
for interpreter in python3 python; do
    if command -v $interpreter > /dev/null 2>&1; then
        exec "$interpreter" "$0" "$@"
        exit
    fi
done
echo "No python interpreter found."
exit 1
' '''

import os
import openai
import sys
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_staged_diff():
    """Get the git diff of the staged changes in the current repository."""
    return os.popen('git diff --cached').read()

def stage_all_changes():
    """Stage all changes in the current repository."""
    os.system('git add .')

def generate_commit_message(diff):
    """Generate a commit title and message using the OpenAI API."""
    
    system_message = {
        "role": "system",
        "content": (
            "You are an expert commit message generator. You should generate a single commit message from a git diff in the following format:"
            "\n\n<type>: <description>\n\n[bulleted body]\n\n"
            "Acceptable types for your commit message are:"
            "\n- build: Changes that affect the build system or external dependencies (example scopes: gulp, broccoli, npm)"
            "\n- ci: Changes to our CI configuration files and scripts (example scopes: Travis, Circle, BrowserStack, SauceLabs)"
            "\n- docs: Documentation only changes"
            "\n- feat: A new feature"
            "\n- fix: A bug fix"
            "\n- perf: A code change that improves performance"
            "\n- refactor: A code change that neither fixes a bug nor adds a feature"
            "\n- style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)"
            "\n- test: Adding missing tests or correcting existing tests"
        )
    }

    user_message = {
        "role": "user",
        "content": diff
    }

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k-0613",
        messages=[system_message, user_message]
    )

    return response.choices[0].message['content'].strip()

def is_valid_git_repo():
    """Check if the current directory is a valid Git repository."""
    exit_status = os.system('git rev-parse --is-inside-work-tree > /dev/null 2>&1')
    return exit_status == 0

def main():
    if "--stage-all" in sys.argv:
        stage_all_changes()
        
    if not is_valid_git_repo():
        print("Error: This is not a valid Git repository.")
        return

    diff = get_staged_diff()
    if not diff:
        print("No staged changes detected. Ensure you've staged your changes using 'git add <filename>' or use the '--stage-all' flag to stage all changes.")
        return

    while True:
        commit_msg = generate_commit_message(diff)
        print(f"Suggested Commit Message:\n\n{commit_msg}")
        choice = input("\nDo you want to [a]ccept, or [g]enerate a new one? ").lower()

        if choice == 'a':
            os.system('git stash push -k')  # Stash unstaged changes, keeping the index intact
            os.system(f'git commit -m "{commit_msg}"')
            os.system('git stash pop')  # Apply the stashed changes back
            print("Changes committed!")
            break
        elif choice == 'g':
            print("Generating a new commit message...\n")
        else:
            print("Invalid choice. Please choose [a]ccept or [g]enerate.")

if __name__ == '__main__':
    main()
