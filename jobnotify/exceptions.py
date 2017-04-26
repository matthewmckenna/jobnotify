class ConfigurationFileError(Exception):
    """Base exception class for errors relating to configuration files."""


class BlankKeyError(ConfigurationFileError):
    """Raised when a key is left blank in the config file."""


class SectionNotFoundError(ConfigurationFileError):
    """Raised when a section is missing from the config file."""


class RequiredKeyMissingError(ConfigurationFileError):
    """Raised when a required key is missing from the config fie."""


class NotificationsNotConfiguredError(ConfigurationFileError):
    """Raised when neither notification option is set."""


class SlackCfgError(ConfigurationFileError):
    """Base exception class for errors relation to the Slack Configuration."""


class EmailAuthenticationError(ConfigurationFileError):
    """Raised when either `email_from` or `password` are incorrect in config file."""


class IndeedAuthenticationError(ConfigurationFileError):
    """Raised when there is an issue with the Indeed publisher key."""
