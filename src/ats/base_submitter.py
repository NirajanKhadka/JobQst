class BaseSubmitter:
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.ats_name = 'Base'
        self.supported_fields = ['first_name', 'last_name', 'email', 'phone']

# Backward compatibility alias
BaseATSSubmitter = BaseSubmitter 