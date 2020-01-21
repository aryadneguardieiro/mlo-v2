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
    An encoder for JSON format

    Sample measurements:

    [{"measurement": "measurement_name", "values":[0], "time":1436372292, "tags": {"tag1": "value1"}}]

    [
       {
         "measurement": "measurement_name",
         "values":      [0],
         "time":        1436372292,
         "tags":        {
                           "tag1": "value1"
                        }
       }
    ]
    """

    def encode(self, msg):
        # type: (bytes) -> List[Text]
        measurements = []
        for line in msg.decode().split("\n"):
            try:
                entry = self.parse_line(line)
            except ValueError as e:
                logging.debug("Error in encoder: %s", e)
                continue
            try:
                measurement = Encoder.format_measurement_name(
                    entry, 'measurement')
                value = Encoder.format_value(entry)
                time = Encoder.format_time(entry)
                tags = Encoder.format_tags(
                    entry, 'tags')
                measurements.append(Encoder.compose_data(
                    measurement, tags, value, time))
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
        data = measurement
        if tags != '':
            data = data + ',' + tags
        data = data + " {0!s} {1!s}".format(value, time)
        return data

    @staticmethod
    def format_measurement_name(entry, arg):
        return entry[arg]

    @staticmethod
    def format_tags(entry, arg):
        tag = []
        if arg in entry:
            for key, value in entry[arg].items():
                tag.append("{0!s}={1!s}".format(key, value))
        return ','.join(tag)

    @staticmethod
    def format_time(entry):
        return int(float(entry['time']))

    @staticmethod
    def format_value(entry):
        values = entry['values']
        if len(values) == 1:
            return "value={0!s}".format(entry['values'][0])
        elif len(values) > 1:
            # influxdb supports writing a record with multiple field values.
            # e.g: 'cpu_load_short,host=server01,region=us-west mem=0.1,cpu=0.2 1422568543702900257'
            field_pairs = []
            for key, value in zip(entry['dsnames'], values):
                field_pairs.append("{0!s}={1!s}".format(key, value))
            return ','.join(field_pairs)
