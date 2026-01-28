import os
import json
import logging
import multiprocessing
import time

import tornado.gen
import tornado.ioloop
import tornado.websocket
from tornado.options import options

import MQTTClient
import SerialProcess

logger = logging.getLogger('RFLinkGW')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def load_config():
    # load config.json and overrides with environment variables
    config = {}

    try:
        with open('config.json') as f:
            config = json.load(f)
        logger.info("Configuration loaded from config.json")
    except Exception as e:
        logger.error("Failed to load config.json: %s", e)
        exit(1)

    env = {k.lower(): v for k, v in os.environ.items()}
    for key in list(config.keys()):
        key_lower = key.lower()
        if key_lower in env:
            raw_value = env[key_lower]

            # Tentative de parsing JSON (list, dict, bool, int…)
            try:
                value = json.loads(raw_value)
            except Exception:
                value = raw_value

            logger.info(
                "Config override: %s = %s (env)",
                key,
                value
            )
            config[key] = value

    return config

def main():
    # load configuration
    config = load_config()

    # messages read from device
    messageQ = multiprocessing.Queue()
    # messages written to device
    commandQ = multiprocessing.Queue()

    sp = SerialProcess.SerialProcess(messageQ, commandQ, config)
    sp.daemon = True
    sp.start()

    mqtt = MQTTClient.MQTTClient(messageQ, commandQ, config)
    mqtt.daemon = True
    mqtt.start()

    # wait a second before sending first task
    time.sleep(1)
    options.parse_command_line()

    mainLoop = tornado.ioloop.IOLoop.instance()
    mainLoop.start()


if __name__ == "__main__":
    main()
