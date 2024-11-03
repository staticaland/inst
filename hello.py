"""GitHub Issue Creator with AI-Generated Content

This module provides functionality to create GitHub issues using AI-generated content.
It uses OpenAI's GPT model to generate issue titles, descriptions, and labels based
on user input, then creates the issue in a specified GitHub repository after user
confirmation.

Dependencies:
    - instructor: For structured OpenAI API responses
    - PyGithub: For GitHub API integration
    - openai: For accessing OpenAI's API
    - pydantic: For data validation

Environment Variables Required:
    - GITHUB_TOKEN: GitHub personal access token with repo permissions

Usage:
    1. Set the GITHUB_TOKEN environment variable
    2. Run the script and provide an issue description when prompted
    3. Review the AI-generated issue content
    4. Confirm creation of the issue

The script validates that all suggested labels exist in the target repository
before creating the issue.
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

labels = repo.get_labels()

valid_labels = {label.name for label in labels}


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
