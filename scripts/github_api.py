import re
import json
import argparse
from collections import defaultdict, namedtuple
from datetime import date, timedelta, datetime
from urllib.parse import urlparse, urlencode
from http.client import HTTPSConnection

# HTTPSConnection.debuglevel = 2

GITHUB_API_URL = "api.github.com"
GITHUB_OAUTH_TOKEN = "your_oauth_token"


class CmdArgParser:
    DATE_FORMAT = "%Y-%m-%d"

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="Simple GitHub repository analyzer"
        )
        parser.add_argument(
            "--url", type=str, required=True, help="URL of public repository on GitHub"
        )
        parser.add_argument(
            "--since_date",
            type=self.date_validator,
            help="only commits after this date will be analyzed",
        )
        parser.add_argument(
            "--until_date",
            type=self.date_validator,
            help="only commits before this date will be analyzed",
        )
        parser.add_argument(
            "--branch", type=str, help="repository branch", default="master"
        )

        self.argument_parser = parser
        self.args = parser.parse_args()

    def date_validator(self, value):
        try:
            return datetime.strptime(value, self.DATE_FORMAT)
        except ValueError:
            msg = "date '{0}' does not match format '{1}'".format(
                value, self.DATE_FORMAT
            )
            raise argparse.ArgumentTypeError(msg)


class APIHandler:
    def __init__(self, hostname, token):
        self.connection = HTTPSConnection(hostname)
        self.headers = {"User-Agent": "Python/3.8", "Authorization": "token " + token}

    def get(self, url, params=None):
        connection = self.connection
        if params:
            params = {k: v for k, v in params.items() if v}
            url += "?" + urlencode(params)

        connection.request(method="GET", url=url, headers=self.headers)
        response = connection.getresponse()
        headers = dict(response.getheaders())
        data = json.loads(response.read())

        return headers, data


class GitHubAPI:
    PAGINATION_PATTERN = re.compile(r"<([^>]+)>")
    GITHUB_API_URL = GITHUB_API_URL
    GITHUB_OAUTH_TOKEN = GITHUB_OAUTH_TOKEN

    def __init__(self, repository):
        self.handler = APIHandler(self.GITHUB_API_URL, self.GITHUB_OAUTH_TOKEN)
        self.repository = repository

    @staticmethod
    def build_query(url, params):
        if params:
            params = "+" + "+".join(
                ["{k}:{v}".format(k=key, v=value) for key, value in params.items()]
            )
            url += params
        return url

    def get_result(self, query, factory=None, params=None, skip_pages=False):
        result = []
        if params and "skip_pages" in params:
            skip_pages = params.pop("skip_pages")
        while True:
            headers, data = self.handler.get(query, params)

            if callable(factory):
                result = factory(result, data)
            else:
                if isinstance(data, list):
                    result.extend(data)
                else:
                    result.append(data)

            if skip_pages:
                break

            if "Link" in headers:
                link_next = headers["Link"].split('rel="next"')[0]
                url = self.PAGINATION_PATTERN.match(link_next).group(1)
                query = "{0.path}?{0.query}".format(urlparse(url))

                params = {}
            else:
                break

        return result

    def search_issues_or_pulls(self, factory=None, skip_pages=False, **kwargs):
        query = self.build_query(
            "/search/issues?q=repo:{repo}".format(repo=self.repository), params=kwargs
        )
        return self.get_result(query=query, factory=factory, skip_pages=skip_pages)

    def get_total_issues_or_pulls(self, factory=None, **kwargs):
        return self.search_issues_or_pulls(factory=factory, skip_pages=True, **kwargs)[
            0
        ].get("total_count")

    def get_commits(self, factory=None, skip_pages=False, **kwargs):
        query = "/repos/{repo}/commits".format(repo=self.repository)
        return self.get_result(
            query=query, factory=factory, params=kwargs, skip_pages=skip_pages
        )


class GitHubAnalyzer:
    OLD_PULL_DAYS = 30
    OLD_ISSUE_DAYS = 14
    GITHUB_DATETIME_FORMAT = "%Y-%m-%dT%H-%M-%SZ"
    GITHUB_DATE_FORMAT = "%Y-%m-%d"

    def __init__(self, args):
        path = urlparse(args.url).path
        api = GitHubAPI(path.strip("/"))

        self.args = args
        self.api = api
        self.branch = args.branch
        self.since_date = args.since_date
        self.until_date = args.until_date

    def show_contributors_report(self):
        Contributor = namedtuple("Contributor", ["login", "commits"])
        table_row_format = "{:<20}{:>8}"

        def factory(result, data):
            if not result:
                result = defaultdict(int)
            for commit in data:
                if commit.get("author"):
                    result[commit.get("author").get("login")] += 1
            return result

        api = self.api
        since_date = (
            self.since_date.strftime(self.GITHUB_DATETIME_FORMAT)
            if self.since_date
            else None
        )
        until_date = (
            self.until_date.strftime(self.GITHUB_DATETIME_FORMAT)
            if self.until_date
            else None
        )

        contributors = api.get_commits(
            factory=factory,
            sha=self.branch,
            since=since_date,
            until=until_date,
            per_page=100,
        )
        contributors = [Contributor(*item) for item in contributors.items()]
        contributors = sorted(contributors, key=lambda x: x[1], reverse=True)[:30]

        print("Contributors:")
        print(table_row_format.format("Login", "Commits"))
        for contributor in contributors:
            print(table_row_format.format(contributor.login, contributor.commits))

    def show_pulls_report(self):
        api = self.api

        opened_pulls = api.get_total_issues_or_pulls(type="pr", state="open")
        closed_pulls = api.get_total_issues_or_pulls(type="pr", state="closed")
        print("Opened pulls:", opened_pulls)
        print("Closed pulls:", closed_pulls)

        before_30_days = date.today() - timedelta(days=self.OLD_PULL_DAYS)
        before_30_days = "<" + before_30_days.strftime(self.GITHUB_DATE_FORMAT)
        old_pulls = api.get_total_issues_or_pulls(
            type="pr", state="open", created=before_30_days
        )
        print("Old pulls:", old_pulls)

    def show_issues_report(self):
        api = self.api

        opened_issues = api.get_total_issues_or_pulls(type="issue", state="open")
        closed_issues = api.get_total_issues_or_pulls(type="issue", state="closed")
        print("Opened issues:", opened_issues)
        print("Closed issues:", closed_issues)

        before_14_days = date.today() - timedelta(days=self.OLD_ISSUE_DAYS)
        before_14_days = "<" + before_14_days.strftime(self.GITHUB_DATE_FORMAT)
        old_issues = api.get_total_issues_or_pulls(
            type="issue", state="open", created=before_14_days
        )
        print("Old issues:", old_issues)

    def run(self):
        self.show_contributors_report()
        self.show_pulls_report()
        self.show_issues_report()


if __name__ == "__main__":
    parser = CmdArgParser()
    analyzer = GitHubAnalyzer(parser.args)
    analyzer.run()
