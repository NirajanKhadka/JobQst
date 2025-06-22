class GreenhouseSubmitter:
    def __init__(self, profile_name: str = "default"):
        self.profile_name = profile_name
        self.ats_name = 'Greenhouse'

    def get_field_mapping(self):
        return {'first_name': 'First Name', 'last_name': 'Last Name'}

    def submit_application(self, data):
        return True

    def detect_form_structure(self):
        return {'fields': ['first_name', 'last_name']} 