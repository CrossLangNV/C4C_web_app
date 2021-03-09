URL = 'url'
TITLE = 'title'
PHONE = 'phone'
EMAILS = 'emails'
OPENING_HOURS = 'opening_hours'


class ContactPoint:
    """
    Represent the CPSV-AP contact point.
    """

    l_phone: list = None
    l_emails: list = None
    l_opening_hours: list = None

    def __init__(self,
                 l_phone=[],
                 l_emails=[],
                 l_opening_hours=[]):
        """

        :param l_phone: (Optional) List with phone numbers
        :param l_emails: (Optional) List with email contacts
        :param l_opening_hours: (Optional) List with information about opening hours
        """

        self.l_phone = l_phone
        self.l_emails = l_emails
        self.l_opening_hours = l_opening_hours

    @classmethod
    def from_dict(cls, page: dict):

        l_phone = _get_list(page.pop(PHONE))
        l_emails = _get_list(page.pop(EMAILS))
        l_opening_hours = _get_list(page.pop(OPENING_HOURS))

        try:
            return cls(l_phone=l_phone,
                       l_emails=l_emails,
                       l_opening_hours=l_opening_hours
                       )
        except Exception as e:
            print(e,
                  "If certain variables are not yet defined. It's because they were not found, while they should have!")

    def get_l_emails(self):
        return self.l_emails

    def get_l_phone(self):
        return self.l_phone

    def get_l_opening_hours(self):
        return self.l_opening_hours

    def add_email(self, email: str = None):
        self.l_emails.append(email)

    def add_phone(self, telephone_number: str = None):
        self.l_phone.append(telephone_number)

    def add_opening_hours(self, opening_hours: str = None):
        self.l_opening_hours.append(opening_hours)


class PublicService:
    uri: str = None
    title: str = None

    def __init__(self,
                 uri: str,
                 title: str):
        """

        :param url: will be used as the unique id for the PS as URI.
        """

        self.uri = uri
        self.title = title

        pass

    @classmethod
    def from_dict(cls, page: dict):

        url = _get_url(page.pop(URL))
        title = _get_title(page.pop(TITLE))

        try:
            return cls(uri=url,
                       title=title
                       )
        except Exception as e:
            print(e,
                  "If certain variables are not yet defined. It's because they were not found, while they should have!")


class PublicOrganization:
    preferred_label: str = None
    spatial: str = None

    def __init__(self,
                 preferred_label: str,
                 spatial: str):
        """

        :param preferredLabel:
        :param spatial: URI to the location
        """

        self.preferred_label = preferred_label
        self.spatial = spatial

    def get_preferred_label(self):
        return self.preferred_label

    def get_spatial(self):
        return self.spatial


def _get_list(v):
    assert isinstance(v, list)
    return v


def _get_url(v):
    assert isinstance(v, list)
    assert len(v) == 1
    return v[0]


def _get_title(v):
    assert isinstance(v, str)
    return v