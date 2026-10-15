
class StreamStatsError(Exception):
    def __init__(self, error_code, message):
        super().__init__(message)
        self.error_code = error_code


class UnsupportedFormatError(StreamStatsError):
    pass


class InvalidEventError(StreamStatsError):
    pass


class InvalidTimestampError(StreamStatsError):
    pass


class CliConfigurationError(StreamStatsError):
    pass
