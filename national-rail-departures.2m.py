#!/usr/bin/env python
# encoding: utf8

# <bitbar.title>National Rail departure times</bitbar.title>
# <bitbar.version>v0.1</bitbar.version>
# <bitbar.author>Nathan Reynolds</bitbar.author>
# <bitbar.author.github>nathforge</bitbar.author.github>
# <bitbar.desc>Show train departures and delays</bitbar.desc>
# <bitbar.image>https://raw.githubusercontent.com/nathforge/bitbar-nationalrail-departures/master/docs/national-rail-logo.png</bitbar.image>
# <bitbar.dependencies>python</bitbar.dependencies>
# <bitbar.abouturl>https://github.com/nathforge/bitbar-nationalrail-departures</bitbar.abouturl>

# Station codes for your route.
# See <http://www.nationalrail.co.uk/stations_destinations/48541.aspx>
FROM_LOC = 'xxx'
TO_LOC   = 'xxx'

# Number of upcoming services to show.
# CAUTION: OS X may hide this plugin if SERVICE_COUNT is too high.
SERVICE_COUNT = 2

# Output formatting.
ON_TIME_FORMAT     = '{departure_time} on time'
KNOWN_DELAY_FORMAT = ':rage: {departure_time}: {delay_minutes}m late'
OTHER_FORMAT       = ':rage: {departure_time} {status}'
ALERT_COLOR = 'red'
SERVICE_SEPARATOR = '    '

# API server.
HUXLEY_SERVER = 'https://huxley.apphb.com'
ACCESS_TOKEN = 'DA1C7740-9DA0-11E4-80E6-A920340000B1'

# Debugging.
DEBUG = False

####

import datetime
import json
import re
import sys
import textwrap
import urllib2
import urlparse

def main():
    if FROM_LOC == 'xxx' or TO_LOC == 'xxx':
        print(textwrap.dedent('''\
            Misconfigured - click for info | color=red
            ---
            FROM_LOC and TO_LOC must be set for your route.
            Fix this by editing {filename}
        '''.format(
            filename=sys.argv[0]
        )))
        return

    # Fetch data from API.
    url = urlparse.urljoin(
        HUXLEY_SERVER,
        'departures/{from_loc}/to/{to_loc}?accessToken={access_token}'.format(
            from_loc=FROM_LOC,
            to_loc=TO_LOC,
            access_token=ACCESS_TOKEN
        )
    )
    response = urllib2.urlopen(url, timeout=10)
    data = json.load(response)

    if DEBUG:
        with open('/tmp/train-times.log', 'a') as fp:
            json.dump(data, fp, indent=4)

    # Filter out services that don't stop at this station.
    #
    # "std: The scheduled time of departure of this service at this location.
    #  If no std is present then this is the destination of this service or it
    #  does not pick up passengers at this location."
    # <https://lite.realtime.nationalrail.co.uk/OpenLDBWS/>, ServiceDetails
    services = [
        service
        for service in data['trainServices']
        if service.get('std')
    ]

    service_strs = []
    has_alerts = False
    for service in services[:SERVICE_COUNT]:
        scheduled_str = service['std']
        estimated_str = service['etd']

        if estimated_str == 'On time':
            service_strs.append(ON_TIME_FORMAT.format(
                departure_time=scheduled_str
            ))
            continue

        has_alerts = True
        scheduled_dt = parse_time_from_str(scheduled_str)
        estimated_dt = parse_time_from_str(estimated_str)

        if estimated_dt:
            delay = estimated_dt - scheduled_dt
            delay_minutes = delay.total_seconds() / 60.0
            service_strs.append(KNOWN_DELAY_FORMAT.format(
                departure_time=scheduled_str,
                delay_minutes=int(delay_minutes)
            ))
            continue

        service_strs.append(OTHER_FORMAT.format(
            departure_time=scheduled_str,
            status=estimated_str.lower()
        ))

    output = SERVICE_SEPARATOR.join(service_strs)
    if has_alerts:
        output += ' | color=red'

    print(output)

def parse_time_from_str(string):
    match = re.search(r'^(\d+):(\d+)$', string)
    if not match:
        return None
    hour_str, minute_str = match.groups()
    return datetime.datetime.now().replace(
        hour=int(hour_str),
        minute=int(minute_str)
    )

if __name__ == '__main__':
    main()
