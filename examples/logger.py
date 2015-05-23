import discogs_client
import logging

def main():
    """Any module can get the logger for discogs_client,
    and configure it manually as in the example below,
    or use logging.dictConfig for advanced configuration"""

    # Get the library's logger and set its level
    logger = logging.getLogger('discogs_client.client')
    logger.setLevel(logging.DEBUG)

    # Add a handler to log to console.
    h = logging.StreamHandler()
    h.setLevel(logging.DEBUG)
    logger.addHandler(h)

    # Set formatter
    formatter = logging.Formatter('%(asctime)s %(name)-12s [%(levelname)s] %(message)s')
    h.setFormatter(formatter)

    # Now, the client logs the URLs it fetches.
    d = discogs_client.Client('ExampleApplication/0.1')
    logger.debug('Testing artist lookup...')
    a = d.artist(101943)
    logger.debug('Artist %d: %s', a.id, a.name)

if __name__ == "__main__":
    main()

