import logging
import colorlog


class LogStreamHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        fmt = "%(log_color)s[%(asctime)s] %(levelname)-8s: %(message)s"
        fmt_date = "%Y-%m-%d %T"
        formatter = colorlog.ColoredFormatter(
            fmt=fmt,
            datefmt=fmt_date,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )

        self.setFormatter(formatter)
