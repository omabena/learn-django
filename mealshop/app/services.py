import re
import os
import logging
import concurrent.futures
import datetime
from slack import WebClient
from slack.errors import SlackApiError
from django.utils.timezone import now, timedelta
from markdown_strings import header, code_block
from .models import Profile


logger = logging.getLogger(__name__)
client = WebClient(token=os.environ['SLACK_TOKEN'])


def create_reminder_async(menu):
    """
    Creates a ThreadPool to call a call _send_reminder in a different thread
    which makes this funciong non blocking

    Paramters:
    menu (Menu): Menu send to _send_reminder function
    """
    THREAD_POOL = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    future = THREAD_POOL.submit(_send_reminder, menu)


def _send_reminder(menu):
    logger.info('Sending reminder to {}'.format(menu))
    message = _format_menu_message(menu)
    profiles = Profile.objects.exclude(slack_user__exact='')

    for profile in profiles:
        time = _get_time_in_epoch()
        logger.info('Timestamp reminder'.format(time))
        _send_reminder_all_employees_with_slack({
            'time': time, 'text': message, 'user': profile.slack_user
        })


def _send_reminder_all_employees_with_slack(json_data):
    try:
        response = client.api_call(
            api_method='reminders.add',
            json=json_data
        )
        logger.debug(response)
    except SlackApiError as e:
        assert e.response["error"]
        logger.error(f"Got an error: {e.response['error']}")


def _get_time_in_epoch():
    dt = now() + timedelta(seconds=10)
    timestamp = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    m = re.search('([0-9]*)([.])', str(timestamp))
    return int(m[1])


def _format_menu_message(menu):
    message = '{}/menu/{}'.format(os.environ['HOSTNAME'], menu.uuid)
    return message
