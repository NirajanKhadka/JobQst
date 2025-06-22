class FallbackSubmitter:
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.fallback_strategy = 'retry_with_delay'

# Backward compatibility alias
FallbackATSSubmitter = FallbackSubmitter 