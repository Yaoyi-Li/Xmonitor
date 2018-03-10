import logging


_BLACK, _RED, _GREEN, _YELLOW, _BLUE, _MAGENTA, _CYAN, _WHITE = range(8)
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS = {
    'WARNING': _YELLOW,
    'INFO': _WHITE,
    'DEBUG': _BLUE,
    'CRITICAL': _YELLOW,
    'ERROR': _RED
}

LOG_LEVEL = logging.INFO


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, datefmt, use_color = True):
        logging.Formatter.__init__(self, msg, datefmt)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):
    COLOR_FORMAT = '[%(asctime)s] %(levelname)-20s: %(message)s'
    DATE_FORMAT = '%H:%M:%S'
    def __init__(self, name):
        logging.Logger.__init__(self, name, LOG_LEVEL)                

        color_formatter = ColoredFormatter(self.COLOR_FORMAT, self.DATE_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return




def getLogger(name):

    logging.setLoggerClass(ColoredLogger)
    return logging.getLogger(name)
