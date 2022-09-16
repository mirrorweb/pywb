""" Utility module for Web Continuity url resolution """
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


# redirect on continuity url not found in archive
DEFAULT_CNF_REDIRECT = '?cnf='
DEFAULT_TIMEOUT = 3
OK_STATUS_CODE_STARTSWITH = ('2', '3')
DEFAULT_CONTINUITY_NETLOCS_FILE = 'allowed_continuity_netlocs.txt'
CONTINUITY_NETLOCS = None


class ContinuityUrl(object):
    """ Web Continuity object.  Check whether a URL exists on the internet """

    def __init__(self, url, timeout=None, ok_status_codes=None):
        self.url = url
        try:
            self.timeout = int(timeout)
        except TypeError:
            self.timeout = DEFAULT_TIMEOUT

        if isinstance(ok_status_codes, tuple):
            self.okay_status_codes = self.int_list_to_str_tuple(ok_status_codes)
        elif isinstance(ok_status_codes, list):
            self.okay_status_codes = self.int_list_to_str_tuple(ok_status_codes)
        else:
            self.okay_status_codes = OK_STATUS_CODE_STARTSWITH

    def is_live_and_okay(self):
        """ Check for a 200 response code """
        # TODO: don't just return True, implement better check logic and move this to check on request, not on render
        resp = True
        # try:
        #     resp = str(self.get_url_head().status).startswith(
        #         self.okay_status_codes)
        # except Exception as e:
        #     print(e)
        #     resp = False
        return resp

    @staticmethod
    def int_list_to_str_tuple(codes):
        try:
            return tuple([str(code) for code in codes])
        except Exception:
            pass
        return tuple()


def allowed_continuity_redirect(netloc, allowed_netlocs=None, netlocs_file=None):
    try:
        if not allowed_netlocs:
            global CONTINUITY_NETLOCS
            if not CONTINUITY_NETLOCS:
                if not netlocs_file:
                    netlocs_file = DEFAULT_CONTINUITY_NETLOCS_FILE
                CONTINUITY_NETLOCS = [x.strip() for x in open(netlocs_file, 'r').readlines()]
            allowed_netlocs = CONTINUITY_NETLOCS
        if isinstance(allowed_netlocs, str):
            allowed_netlocs = [allowed_netlocs]
        if netloc.endswith(tuple(allowed_netlocs)):
            return True
    except Exception as ex:
        pass
    return False