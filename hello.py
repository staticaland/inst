import os

import instructor
from github import Auth, Github
from openai import OpenAI
from pydantic import BaseModel, field_validator

SYSTEM_PROMPT = "You create GitHub issues based on the user message."

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

    @field_validator('labels')
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
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": "Rewrite to Python",
        },
    ],
)

print(issue.title, issue.body, issue.labels, sep="\n")

response = input("Do you want to create the issue? (yes/no): ").strip().lower()

if response == 'yes':
    repo.create_issue(title=issue.title, body=issue.body, labels=issue.labels)
    print("Issue created successfully.")
else:
    print("Issue creation aborted.")
