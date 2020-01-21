from datetime import datetime
try:
    import ujson as json
except ImportError:
    import json

import logging
import pdb

try:
    # Test for mypy support (requires Python 3)
    from typing import List, Text
except:
    pass


class Encoder(object):
    """
    An encoder for the Collectd JSON format
    See https://collectd.org/wiki/index.php/JSON

    Sample measurements:
    """

    def encode(self, msg):
        # type: (bytes) -> List[Text]
        measurements = []

        for line in msg.decode().split("\n"):
            try:
                # Set flag for float precision to get the same
                # results for Python 2 and 3.
                json_object = self.parse_line(line)

            except ValueError as e:
                logging.debug("Error in encoder: %s", e)
                continue

            measurement = None
            tags = None
            value = None
            time = None

            try:
                time = time or Encoder.format_time(json_object)
                measurement = measurement or Encoder.format_measurement_name(json_object, ['name'])
                tags = tags or Encoder.format_tags(json_object, ['labels'])
                value = value or Encoder.format_value(json_object)

                if measurement and tags and value and time:
                   measurements.append(Encoder.compose_data(measurement, tags, value, time))

            except Exception as e:
                logging.debug("Error in input data: %s. Skipping.", e)
                continue

        return measurements

    @staticmethod
    def parse_line(line):
        # return json.loads(line, {'precise_float': True})
        # for influxdb version > 0.9, timestamp is an integer
        return json.loads(line)

    # following methods are added to support customizing measurement name, tags much more flexible
    @staticmethod
    def compose_data(measurement, tags, value, time):
        data = "{0!s},{1!s} {2!s} {3!s}".format(measurement, tags, value, time)
        return data

    @staticmethod
    def format_measurement_name(entry, args):
        name = []
        for arg in args:
            if arg in entry:
                # avoid to add extra _ if some entry value is None
                if entry[arg] != '':
                    name.append(entry[arg])
        return '_'.join(name)

    @staticmethod
    def format_tags(entry, args):
        tag = []
        for arg in args:
            if arg in entry:
                # to avoid add None as tag value
                prom_tags = entry[arg]
                if len(prom_tags) > 0:
                    for prom_tag, prom_tag_value in prom_tags.items():
                        tag.append("{0!s}={1!s}".format(prom_tag, prom_tag_value))
        return ','.join(tag)

    @staticmethod
    def format_time(entry):
        date = datetime.strptime(entry['timestamp'],'%Y-%m-%dT%H:%M:%SZ')
        return int(float(date.timestamp()))

    @staticmethod
    def format_value(entry):
        value = entry['value']
        #if len(values) == 1:
        return "value={0!s}".format(value)
        #else:
        #    # influxdb supports writing a record with multiple field values.
        #    # e.g: 'cpu_load_short,host=server01,region=us-west mem=0.1,cpu=0.2 1422568543702900257'
        #    field_pairs = []
        #    for key, value in zip(entry['dsnames'], values):
        #        field_pairs.append("{0!s}={1!s}".format(key, value))
        #    return ','.join(field_pairs)
