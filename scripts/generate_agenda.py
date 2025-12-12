#!/usr/bin/env python3
"""
KubeStellar Community Meeting Agenda Generator

Run this script 2-3 days before each bi-weekly meeting to generate
a dynamic agenda based on GitHub repository activity.

Usage:
    python generate_agenda.py --meeting-date "2026-01-08"
    
Requirements:
    pip install PyGithub python-dateutil requests

Environment:
    GITHUB_TOKEN - GitHub personal access token (optional, but recommended for rate limits)
"""

import os
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional
import argparse

try:
    from github import Github, Auth
    from dateutil import parser as date_parser
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.run(["pip", "install", "PyGithub", "python-dateutil", "--break-system-packages"])
    from github import Github, Auth
    from dateutil import parser as date_parser


# Configuration
CONFIG = {
    "repos": [
        "kubestellar/kubestellar",
        "kubestellar/kubeflex",
        "kubestellar/ocm-status-addon",
        "kubestellar/docs",
        "kubestellar/ui",
    ],
    "lookback_days": 14,
    "max_prs_to_show": 8,
    "max_issues_to_show": 5,
    "max_discussions_to_show": 5,
    "meeting_time": "10AM ET",
    "meeting_link": "https://teams.microsoft.com/l/meetup-join/...",
    "youtube_link": "https://kubestellar.io/tv",
    "slack_channel": "https://cloud-native.slack.com/archives/C097094RZ3M",
}


@dataclass
class PRInfo:
    number: int
    title: str
    author: str
    url: str
    merged_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    labels: List[str] = field(default_factory=list)
    days_open: int = 0


@dataclass
class IssueInfo:
    number: int
    title: str
    author: str
    url: str
    labels: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None


@dataclass
class DiscussionInfo:
    title: str
    url: str
    author: str
    comments: int
    created_at: Optional[datetime] = None


class AgendaGenerator:
    def __init__(self, github_token: Optional[str] = None):
        if github_token:
            self.gh = Github(auth=Auth.Token(github_token))
        else:
            self.gh = Github()
        self.lookback_date = datetime.now() - timedelta(days=CONFIG["lookback_days"])
        
    def get_merged_prs(self, repo_name: str) -> List[PRInfo]:
        """Get PRs merged in the lookback period."""
        prs = []
        try:
            repo = self.gh.get_repo(repo_name)
            # Limit to first 50 PRs to avoid long API calls
            for pr in list(repo.get_pulls(state="closed", sort="updated", direction="desc")[:50]):
                if pr.merged_at and pr.merged_at.replace(tzinfo=None) > self.lookback_date:
                    prs.append(PRInfo(
                        number=pr.number,
                        title=pr.title[:60] + "..." if len(pr.title) > 60 else pr.title,
                        author=pr.user.login,
                        url=pr.html_url,
                        merged_at=pr.merged_at,
                        labels=[l.name for l in pr.labels],
                    ))
                elif pr.updated_at.replace(tzinfo=None) < self.lookback_date:
                    break  # Stop if we've gone past our lookback window
        except Exception as e:
            print(f"Warning: Could not fetch PRs from {repo_name}: {e}")
        return prs
    
    def get_open_prs_needing_review(self, repo_name: str) -> List[PRInfo]:
        """Get open PRs that need review."""
        prs = []
        try:
            repo = self.gh.get_repo(repo_name)
            # Limit to first 30 open PRs
            for pr in list(repo.get_pulls(state="open", sort="created", direction="desc")[:30]):
                days_open = (datetime.now() - pr.created_at.replace(tzinfo=None)).days
                if days_open >= 3:  # Only show PRs open for 3+ days
                    prs.append(PRInfo(
                        number=pr.number,
                        title=pr.title[:50] + "..." if len(pr.title) > 50 else pr.title,
                        author=pr.user.login,
                        url=pr.html_url,
                        created_at=pr.created_at,
                        days_open=days_open,
                        labels=[l.name for l in pr.labels],
                    ))
        except Exception as e:
            print(f"Warning: Could not fetch open PRs from {repo_name}: {e}")
        return sorted(prs, key=lambda x: x.days_open, reverse=True)
    
    def get_help_wanted_issues(self, repo_name: str) -> List[IssueInfo]:
        """Get issues with help-wanted or good-first-issue labels."""
        issues = []
        try:
            repo = self.gh.get_repo(repo_name)
            for label_name in ["help wanted", "good first issue", "help-wanted", "good-first-issue"]:
                try:
                    for issue in repo.get_issues(state="open", labels=[label_name]):
                        if not issue.pull_request:  # Exclude PRs
                            issues.append(IssueInfo(
                                number=issue.number,
                                title=issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                                author=issue.user.login,
                                url=issue.html_url,
                                labels=[l.name for l in issue.labels],
                                created_at=issue.created_at,
                            ))
                except:
                    pass  # Label might not exist
        except Exception as e:
            print(f"Warning: Could not fetch issues from {repo_name}: {e}")
        return issues
    
    def get_recent_contributors(self, repo_name: str) -> List[str]:
        """Get unique contributors from recent merged PRs."""
        contributors = set()
        try:
            repo = self.gh.get_repo(repo_name)
            for pr in repo.get_pulls(state="closed", sort="updated", direction="desc")[:30]:
                if pr.merged_at and pr.merged_at.replace(tzinfo=None) > self.lookback_date:
                    contributors.add(pr.user.login)
        except Exception as e:
            print(f"Warning: Could not fetch contributors from {repo_name}: {e}")
        return list(contributors)
    
    def get_repo_activity_score(self, repo_name: str) -> int:
        """Calculate activity score for a repo based on recent updates."""
        score = 0
        try:
            repo = self.gh.get_repo(repo_name)
            # Count recent PRs (open + merged) - limit to 30
            for pr in list(repo.get_pulls(state="all", sort="updated", direction="desc")[:30]):
                if pr.updated_at.replace(tzinfo=None) > self.lookback_date:
                    score += 1
                else:
                    break
            # Count recent issues - limit to 30
            for issue in list(repo.get_issues(state="all", sort="updated", direction="desc")[:30]):
                if not issue.pull_request and issue.updated_at.replace(tzinfo=None) > self.lookback_date:
                    score += 1
                elif issue.updated_at.replace(tzinfo=None) < self.lookback_date:
                    break
        except Exception as e:
            print(f"Warning: Could not calculate activity for {repo_name}: {e}")
        return score
    
    def get_top_issues_for_discussion(self, repo_name: str, limit: int = 2) -> List[IssueInfo]:
        """Get top issues worth discussing - prioritizes by comments and recent activity."""
        issues = []
        try:
            repo = self.gh.get_repo(repo_name)
            # Get open issues sorted by comments (most discussed) - limit to 20
            for issue in list(repo.get_issues(state="open", sort="comments", direction="desc")[:20]):
                if issue.pull_request:
                    continue  # Skip PRs
                # Prioritize issues with recent activity
                days_since_update = (datetime.now() - issue.updated_at.replace(tzinfo=None)).days
                if days_since_update <= 30:  # Active in last month
                    issues.append(IssueInfo(
                        number=issue.number,
                        title=issue.title[:45] + "..." if len(issue.title) > 45 else issue.title,
                        author=issue.user.login,
                        url=issue.html_url,
                        labels=[l.name for l in issue.labels][:3],
                        created_at=issue.created_at,
                    ))
                if len(issues) >= limit:
                    break
        except Exception as e:
            print(f"Warning: Could not fetch discussion issues from {repo_name}: {e}")
        return issues[:limit]
    
    def get_release_info(self, repo_name: str) -> dict:
        """Get latest release information."""
        try:
            repo = self.gh.get_repo(repo_name)
            releases = list(repo.get_releases())
            if releases:
                latest = releases[0]
                return {
                    "version": latest.tag_name,
                    "url": latest.html_url,
                    "date": latest.published_at.strftime("%Y-%m-%d") if latest.published_at else "N/A",
                }
        except Exception as e:
            print(f"Warning: Could not fetch release info from {repo_name}: {e}")
        return {"version": "Unknown", "url": "#", "date": "N/A"}
    
    def generate_agenda(self, meeting_date: str) -> str:
        """Generate the complete agenda."""
        
        # Collect data from all repos
        all_merged_prs = []
        all_open_prs = []
        all_help_wanted = []
        all_contributors = set()
        repo_activity = {}  # Track activity per repo
        
        print("Fetching data from GitHub repos...")
        for repo in CONFIG["repos"]:
            print(f"  - {repo}")
            all_merged_prs.extend(self.get_merged_prs(repo))
            all_open_prs.extend(self.get_open_prs_needing_review(repo))
            all_help_wanted.extend(self.get_help_wanted_issues(repo))
            all_contributors.update(self.get_recent_contributors(repo))
            repo_activity[repo] = self.get_repo_activity_score(repo)
        
        # Sort and limit
        all_merged_prs.sort(key=lambda x: x.merged_at or datetime.min, reverse=True)
        all_merged_prs = all_merged_prs[:CONFIG["max_prs_to_show"]]
        all_open_prs = all_open_prs[:CONFIG["max_prs_to_show"]]
        all_help_wanted = all_help_wanted[:CONFIG["max_issues_to_show"]]
        
        # Get top 3 most active repos
        sorted_repos = sorted(repo_activity.items(), key=lambda x: x[1], reverse=True)
        top_repos = [repo for repo, score in sorted_repos[:3] if score > 0]
        
        # Get top 2 discussion-worthy issues from each top repo
        print("Fetching top issues from most active repos...")
        top_issues_by_repo = {}
        for repo in top_repos:
            print(f"  - {repo}")
            top_issues_by_repo[repo] = self.get_top_issues_for_discussion(repo, limit=2)
        
        # Get release info from main repo
        release_info = self.get_release_info("kubestellar/kubestellar")
        
        # Calculate next meeting date (2 weeks from meeting_date)
        meeting_dt = date_parser.parse(meeting_date)
        next_meeting_dt = meeting_dt + timedelta(days=14)
        next_meeting = next_meeting_dt.strftime("%m/%d/%Y")
        
        # Generate the agenda
        agenda = self._render_template(
            meeting_date=meeting_date,
            merged_prs=all_merged_prs,
            open_prs=all_open_prs,
            help_wanted=all_help_wanted,
            contributors=list(all_contributors),
            release_info=release_info,
            next_meeting=next_meeting,
            top_issues_by_repo=top_issues_by_repo,
        )
        
        return agenda
    
    def _render_template(self, meeting_date: str, merged_prs: List[PRInfo], 
                         open_prs: List[PRInfo], help_wanted: List[IssueInfo],
                         contributors: List[str], release_info: dict,
                         next_meeting: str, top_issues_by_repo: dict = None) -> str:
        """Render the compact 30-min agenda template."""
        
        # Counts
        merged_count = len(merged_prs)
        review_count = len(open_prs)
        help_count = len(help_wanted)
        
        # Build attention table - only most urgent items (max 5)
        attention_items = []
        
        # Add stale PRs (>7 days)
        for pr in open_prs[:3]:
            if pr.days_open >= 7:
                urgency = "🟠" if pr.days_open < 14 else "🔴"
                attention_items.append(
                    f"| [PR #{pr.number}]({pr.url}) | {urgency} Open {pr.days_open}d | @{pr.author} |"
                )
        
        # Add breaking changes from merged
        for pr in merged_prs[:2]:
            if any(l in ["breaking-change", "major"] for l in pr.labels):
                attention_items.append(
                    f"| [PR #{pr.number}]({pr.url}) | 🚨 Breaking change merged | @{pr.author} |"
                )
        
        # Add help wanted
        for issue in help_wanted[:2]:
            attention_items.append(
                f"| [#{issue.number}]({issue.url}) | 🆘 Help wanted | - |"
            )
        
        attention_table = "\n".join(attention_items[:5]) if attention_items else "| ✅ | All clear this sprint! | - |"
        
        # Build discussion topics from top repos
        discussion_section = ""
        if top_issues_by_repo:
            for repo, issues in top_issues_by_repo.items():
                if issues:
                    repo_short = repo.split("/")[-1]  # Just the repo name
                    discussion_section += f"\n**{repo_short}:**\n"
                    for issue in issues:
                        labels_str = " ".join([f"`{l}`" for l in issue.labels[:2]]) if issue.labels else ""
                        discussion_section += f"- [#{issue.number}]({issue.url}): {issue.title} {labels_str}\n"
        
        if not discussion_section:
            discussion_section = "\n_No active issues to highlight_\n"
        
        template = f"""# KubeStellar Community Meeting
## 📅 {meeting_date} | {CONFIG["meeting_time"]} | ⏱️ 30 min

[Join]({CONFIG["meeting_link"]}) | [YouTube]({CONFIG["youtube_link"]}) | [Slack]({CONFIG["slack_channel"]})

---

## 🎯 Decision Needed (5 min)
> **_[Add focus topic before meeting]_**

Vote: 👍 / 👎 / 💬

---

## 🔥 Repo Pulse (8 min)
*Auto-generated {datetime.now().strftime("%Y-%m-%d")} | [Full PR list](https://github.com/kubestellar/kubestellar/pulls)*

**Merged:** {merged_count} PRs | **Needs Review:** {review_count} PRs | **Help Wanted:** {help_count} issues

### 🚨 Attention Needed
| Item | Why | Owner |
|------|-----|-------|
{attention_table}

### 💬 Top Issues to Discuss
*From most active repos*
{discussion_section}
---

## 🚀 Release (3 min)
**Current:** [{release_info["version"]}]({release_info["url"]}) ({release_info["date"]}) | **Next:** _[version]_ - _[status]_

---

## 📢 Quick Updates (4 min)
*30 sec each max - post details in Slack*

- **LFX/IFOS:** _[one line or "no update"]_
- **Events:** _[one line or "no update"]_  
- **Integrations:** _[one line or "no update"]_

---

## 💬 Open Mic (8 min)
*Sign up in PR or Slack*

| Slot | Who | Topic |
|------|-----|-------|
| 1 | _[name]_ | _[topic]_ |
| 2 | _[name]_ | _[topic]_ |

---

## ✅ Actions
| What | Who | Due |
|------|-----|-----|
| _[from last meeting]_ | | |

---

**Next:** {next_meeting} | 👥 _Add name in chat_

<sub>Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC</sub>
"""
        return template


def main():
    parser = argparse.ArgumentParser(description="Generate KubeStellar community meeting agenda")
    parser.add_argument("--meeting-date", required=True, help="Meeting date (YYYY-MM-DD)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    args = parser.parse_args()
    
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("⚠️  No GitHub token provided. Rate limits may apply.")
        print("   Set GITHUB_TOKEN env var or use --token flag\n")
    
    generator = AgendaGenerator(token)
    agenda = generator.generate_agenda(args.meeting_date)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(agenda)
        print(f"✅ Agenda written to {args.output}")
    else:
        print(agenda)


if __name__ == "__main__":
    main()
