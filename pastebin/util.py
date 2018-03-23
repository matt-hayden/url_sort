
from datetime import datetime, timezone
import email.parser
import sys

import tqdm

now = datetime.now(timezone.utc)


if sys.stderr.isatty():
    progress = tqdm.tqdm
else:
    def progress(arg, **kwargs):
        return arg


def parse_email_message(text, \
        parser=email.parser.BytesParser(), \
        date_format='%a, %d %b %Y %X %z'):
    """
    Returns message, dict_of_updates

    """
    m = parser.parsebytes(text)
    u = {}
    # Fields like message['date'] cannot be written in-place
    u['date'] = datetime.strptime(m['date'], date_format)
    return m, u

