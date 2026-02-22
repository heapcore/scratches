import re
from typing import List, Any

import bs4
import mailbox
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class EmailMessage:
    email_labels: str
    email_date: str
    email_from: str
    email_to: str
    email_subject: str
    email_text: List[Any]


class GmailMboxMessage:
    REGEX_EMAIL = r"[\w.+-]+@[\w-]+\.[\w.-]+"

    def __init__(self, email_data):
        if not isinstance(email_data, mailbox.mboxMessage):
            raise TypeError("Variable must be type mailbox.mboxMessage")
        self.email_data = email_data

    @staticmethod
    def get_html_text(html):
        try:
            return bs4.BeautifulSoup(html, "lxml").body.get_text(" ", strip=True)
        except AttributeError:  # message contents empty
            return None

    @staticmethod
    def parse_regex(pattern, data):
        match = re.search(pattern, data)
        return match.group(0)

    def parse_email(self):
        email_labels = self.email_data["X-Gmail-Labels"]
        email_date = self.email_data["Date"]
        email_from = self.parse_regex(self.REGEX_EMAIL, self.email_data["From"])
        email_to = self.parse_regex(self.REGEX_EMAIL, self.email_data["To"])
        email_subject = self.email_data["Subject"]
        email_text = self.read_email_payload()

        return EmailMessage(
            email_labels, email_date, email_from, email_to, email_subject, email_text
        )

    def read_email_payload(self):
        email_payload = self.email_data.get_payload()
        if self.email_data.is_multipart():
            email_messages = list(self._get_email_messages(email_payload))
        else:
            email_messages = [email_payload]
        return [self._read_email_text(msg) for msg in email_messages]

    def _get_email_messages(self, email_payload):
        for msg in email_payload:
            if isinstance(msg, (list, tuple)):
                for submsg in self._get_email_messages(msg):
                    yield submsg
            elif msg.is_multipart():
                for submsg in self._get_email_messages(msg.get_payload()):
                    yield submsg
            else:
                yield msg

    def _read_email_text(self, msg):
        content_type = "NA" if isinstance(msg, str) else msg.get_content_type()
        encoding = (
            "NA" if isinstance(msg, str) else msg.get("Content-Transfer-Encoding", "NA")
        )
        if "text/plain" in content_type and "base64" not in encoding:
            msg_text = msg.get_payload()
        elif "text/html" in content_type and "base64" not in encoding:
            msg_text = self.get_html_text(msg.get_payload())
        elif content_type == "NA":
            msg_text = self.get_html_text(msg)
        else:
            msg_text = None
        return content_type, encoding, msg_text


if __name__ == "__main__":
    mbox_obj = mailbox.mbox(r"D:\Dump from Gmail.mbox")

    num_entries = len(mbox_obj)
    parsed_emails = []
    parsed_emails_from = defaultdict(int)
    parsed_emails_to = defaultdict(int)
    errors = []
    steps_to_log = 10

    # Parse emails
    for idx, email_obj in enumerate(mbox_obj):
        email_data = GmailMboxMessage(email_obj)
        try:
            parsed_emails.append(email_data.parse_email())
        except Exception as e:
            errors.append((idx, str(e)))

        if idx % steps_to_log == 0:
            print("Parsing email {0} of {1}".format(idx, num_entries))

    # Process results
    for email in parsed_emails:
        parsed_emails_from[email.email_from] += 1
        parsed_emails_to[email.email_to] += 1

    print("Emails from:")
    for w in sorted(parsed_emails_from, key=parsed_emails_from.get, reverse=True):
        print(w, parsed_emails_from[w])
    print("Emails to:")
    for w in sorted(parsed_emails_to, key=parsed_emails_to.get, reverse=True):
        print(w, parsed_emails_to[w])
    print("Errors:")
    for idx, err in errors:
        print(idx, err)
