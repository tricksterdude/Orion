import ctypes
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.runtime import OrionRuntime


PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIRECTORY = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIRECTORY / "orion.log"

MUTEX_NAME = "Local\\OrionHomeCinema"
ERROR_ALREADY_EXISTS = 183


class LogStream:

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, logger, level):

        self.logger = logger
        self.level = level
        self._pending = ""

    def write(self, message):

        self._pending += message

        while "\n" in self._pending:

            line, self._pending = (
                self._pending.split(
                    "\n",
                    1,
                )
            )

            line = line.rstrip()

            if line:

                self.logger.log(
                    self.level,
                    line,
                )

        return len(message)

    def flush(self):

        line = self._pending.rstrip()

        if line:

            self.logger.log(
                self.level,
                line,
            )

        self._pending = ""

        for handler in self.logger.handlers:

            handler.flush()

    def isatty(self):

        return False

    def writable(self):

        return True


def configure_logging():

    LOG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger(
        "orion.background"
    )

    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:

        handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | "
                "%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

        logger.addHandler(handler)

    sys.stdout = LogStream(
        logger,
        logging.INFO,
    )

    sys.stderr = LogStream(
        logger,
        logging.ERROR,
    )

    return logger


def acquire_single_instance():

    kernel32 = ctypes.windll.kernel32

    handle = kernel32.CreateMutexW(
        None,
        False,
        MUTEX_NAME,
    )

    if not handle:

        raise ctypes.WinError()

    if kernel32.GetLastError() == (
        ERROR_ALREADY_EXISTS
    ):

        kernel32.CloseHandle(handle)
        return None

    return handle


def main():

    os.chdir(PROJECT_ROOT)

    logger = configure_logging()
    mutex = acquire_single_instance()

    if mutex is None:

        logger.info(
            "Orion is already running; "
            "second launch cancelled."
        )
        return

    logger.info(
        "Orion background runtime starting."
    )

    try:

        runtime = OrionRuntime()
        runtime.run()

    except Exception:

        logger.exception(
            "Orion stopped because of "
            "an unexpected error."
        )
        raise

    finally:

        logger.info(
            "Orion background runtime stopped."
        )

        ctypes.windll.kernel32.CloseHandle(
            mutex
        )


if __name__ == "__main__":

    main()