"""GitHub Issue Creator with AI-Generated Content and Supabase Storage
This module provides functionality to create GitHub issues using AI-generated content
and stores them in a Supabase database for tracking purposes.

Dependencies:
    - instructor: For structured OpenAI API responses
    - PyGithub: For GitHub API integration
    - openai: For accessing OpenAI's API
    - pydantic: For data validation
    - supabase: For database integration
    
Environment Variables Required:
    - GITHUB_TOKEN: GitHub personal access token with repo permissions
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_KEY: Your Supabase service role key

The script validates labels and stores issue data in both GitHub and Supabase.
"""

import os

import instructor
from github import Auth, Github
from openai import OpenAI
from pydantic import BaseModel, field_validator
from supabase import Client, create_client

SYSTEM_PROMPT = "You create GitHub issues based on the user message."

ISSUE_DESCRIPTION = "Please make it possible to use the GitHub CLI to create issues."

issue_description = (
    input(f"Describe your issue or feature request [{ISSUE_DESCRIPTION}]: ").strip()
    or ISSUE_DESCRIPTION
)

github_token = os.getenv("GITHUB_TOKEN")

auth = Auth.Token(github_token)

g = Github(auth=auth)

repo = g.get_repo("staticaland/daggers")

valid_labels = {label.name for label in repo.get_labels()}


class GitHubIssue(BaseModel):
    title: str
    body: str
    labels: list[str]

    @field_validator("labels")
    def validate_labels(cls, v):
        invalid_labels = [label for label in v if label not in valid_labels]
        if invalid_labels:
            raise ValueError(f'Invalid labels: {", ".join(invalid_labels)}')
        return v


client = instructor.from_openai(OpenAI())

issue = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=GitHubIssue,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": issue_description},
    ],
)

print(issue.title, issue.body, issue.labels, sep="\n")

response = input("Do you want to create the issue? (yes/no): ").strip().lower()

if response == "yes":
    created_issue = repo.create_issue(
        title=issue.title, body=issue.body, labels=issue.labels
    )
    print("Issue created successfully.")
else:
    print("Issue creation aborted.")

supabase_response = input("Do you want to log the issue in Supabase? (yes/no): ").strip().lower()

if supabase_response == "yes":
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)

    supabase.table("issues").insert(
        {"title": issue.title, "body": issue.body, "labels": issue.labels}
    ).execute()
    print("Issue logged successfully in Supabase.")
else:
    print("Issue logging in Supabase aborted.")
