import re

class ManageUserPage(object):
    url_regex = re.compile('http://[^/]+/user/[0-9]+')