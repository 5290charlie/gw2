#!/usr/bin/env python

import sys, time, tools, logging, urllib3, ssl
from multiprocessing import Pool, TimeoutError
from daemon import Daemon
from models import *

logging.basicConfig(filename='/var/log/syslog', level=logging.WARNING)

verbose = config.get('verbose')
timeout = int(config.get('timeout'))
log_freq = int(config.get('log_freq'))
max_threads = int(config.get('max_threads'))
timeout_limit = int(config.get('timeout_limit'))
timeout_reset = int(config.get('timeout_reset'))

class Miner(Daemon):
    name = 'GW2 Miner v2'
    pool = None
    last_log = 0
    iteration = 0
    last_timeout = 0
    timeout_count = 0

    def run(self):
        try:
            tools.log("%s daemon started" % self.name, True)

            if verbose:
                tools.log("Daemon is verbose")

            matches = Match.get_current()

            num_threads = matches.count()
            num_worlds = World.select().count()

            if num_threads == 0 or num_threads > max_threads:
                tools.log("Cannot create more than %d threads! (attempted to create %d)" % (max_threads, num_threads))
                num_threads = max_threads

            self.pool = Pool(num_threads)

            tools.log("Created thread pool with %d threads" % num_threads)

            db.connect()

            while True:
                self.iteration += 1
                self.log()

                try:
                    date_now = datetime.utcnow()

                    if matches.count() == 0 or matches.count() < (num_worlds / 3):
                        raise MatchNotCurrent

                    for match in matches:
                        if not match.is_current():
                            raise MatchNotCurrent

                    responses = self.pool.imap_unordered(tools.mine_match, matches)

                    for r in responses:
                        tools.log("Unordered imap response: %s" % r)

                    # args = [match for match in matches]

                    # jobs = self.pool.map_async(tools.mine_match, matches)
                    # responses = jobs.get(timeout=timeout)

                    # if responses.count(None) != len(responses):
                    #     tools.log("Job returned NOT None response! RESPONSES=%s" % responses, True)
                except MatchNotCurrent:
                    tools.sync()
                    matches = Match.get_current()
                except (ApiRequestError, TimeoutError, ssl.SSLError):
                    tools.log("Job timed out! [timeout=%d(s), counter=%d]" % (timeout, self.timeout_count), True)
                    self.pool.terminate()
                    self.pool.join()
                    tools.log("Thread pool terminated", True)

                    since_last = time.time() - self.last_timeout

                    if self.last_timeout == 0:
                        self.last_timeout = time.time()
                    elif since_last >= timeout_reset:
                        tools.log("%d seconds (%0.1f hours) since last timeout, resetting timeout counter" % (since_last, since_last / 3600))
                        self.timeout_count = 0

                    self.timeout_count += 1
                    self.last_timeout = time.time()

                    if self.timeout_count < timeout_limit:
                        self.pool = Pool(num_threads)
                        tools.log("Created thread pool with %d threads" % num_threads, True)
                    else:
                        tools.log("Timeout limit reached! %d timeout(s) within %d seconds (%0.1f hours)" % (timeout_limit, timeout_reset, timeout_reset / 3600), True)
                        raise TimeoutError

        except:
            logging.exception("Exiting due to exception!")
            raise

            # type, value, traceback = sys.exc_info()
            # tools.log("%s exiting due to exception! %s" % (self.name, type), True)
            # tools.log("%s %s" % (value, traceback), True)
        else:
            tools.log("%s is exiting cleanly" % self.name, True)
        finally:
            self.pool.close()
            self.pool.join()

    def log(self):
        if self.last_log == 0 or (time.time() - self.last_log) >= log_freq:
            tools.log("%s is running (iteration #%d)" % (self.name, self.iteration), True)
            self.last_log = time.time()


if __name__ == "__main__":
    daemon = Miner("/tmp/service.pid")
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'status' == sys.argv[1]:
            daemon.status()
        elif 'init' == sys.argv[1]:
            tools.init()
            tools.sync()
        elif 'sync' == sys.argv[1]:
            tools.sync()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
