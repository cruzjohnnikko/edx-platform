"""
Utility functions for setting "logged in" cookies used by subdomains.
"""
from __future__ import unicode_literals

import json
import time

import six
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse
from django.dispatch import Signal
from django.utils.http import cookie_date
from oauth2_provider.models import Application

<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py
from edx_rest_framework_extensions.auth.jwt import cookies as jwt_cookies
from openedx.core.djangoapps.user_api.accounts.utils import retrieve_last_sitewide_block_completed
from openedx.core.djangoapps.user_authn.waffle import JWT_COOKIES_FLAG
=======
from openedx.core.djangoapps.oauth_dispatch.adapters.dot import DOTAdapter
from openedx.core.djangoapps.user_api.accounts.utils import retrieve_last_sitewide_block_completed
from openedx.core.lib.token_utils import JwtBuilder
>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py
from student.models import CourseEnrollment


CREATE_LOGON_COOKIE = Signal(providing_args=['user', 'response'])

LOGGED_IN_COOKIE_NAMES = (
    settings.EDXMKTG_LOGGED_IN_COOKIE_NAME,
    settings.EDXMKTG_USER_INFO_COOKIE_NAME,
    settings.JWT_AUTH['JWT_AUTH_COOKIE_HEADER_PAYLOAD'],
    settings.JWT_AUTH['JWT_AUTH_COOKIE_SIGNATURE'],
    settings.JWT_AUTH['JWT_AUTH_COOKIE_REFRESH_TOKEN'],
)


JWT_COOKIE_NAMES = (
    # Header and payload sections of a JSON Web Token containing user
    # information and used as an access token.
    jwt_cookies.jwt_cookie_header_payload_name(),

    # Signature section of a JSON Web Token.
    jwt_cookies.jwt_cookie_signature_name(),

    # Refresh token, which can be used to get a new JSON Web Token.
    jwt_cookies.jwt_refresh_cookie_name(),
)

# TODO (ARCH-245): Remove the following deprecated cookies.
DEPRECATED_LOGGED_IN_COOKIE_NAMES = (
    # Set to 'true' if the user is logged in.
    settings.EDXMKTG_LOGGED_IN_COOKIE_NAME,

    # JSON-encoded dictionary with user information.
    settings.EDXMKTG_USER_INFO_COOKIE_NAME,
)

ALL_LOGGED_IN_COOKIE_NAMES = JWT_COOKIE_NAMES + DEPRECATED_LOGGED_IN_COOKIE_NAMES


def is_logged_in_cookie_set(request):
    """ Check whether the request has logged in cookies set. """
    if JWT_COOKIES_FLAG.is_enabled():
        expected_cookie_names = ALL_LOGGED_IN_COOKIE_NAMES
    else:
        expected_cookie_names = DEPRECATED_LOGGED_IN_COOKIE_NAMES

    return all(
        cookie_name in request.COOKIES
        for cookie_name in expected_cookie_names
    )


def delete_logged_in_cookies(response):
    """
    Delete cookies indicating that the user is logged in.
    Arguments:
        response (HttpResponse): The response sent to the client.
    Returns:
        HttpResponse
    """
    for cookie_name in ALL_LOGGED_IN_COOKIE_NAMES:
        response.delete_cookie(
            cookie_name.encode('utf-8'),
            path='/',
            domain=settings.SESSION_COOKIE_DOMAIN
        )

    return response


def standard_cookie_settings(request):
    """ Returns the common cookie settings (e.g. expiration time). """

    if request.session.get_expire_at_browser_close():
        max_age = None
        expires = None
    else:
        max_age = request.session.get_expiry_age()
<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py
        expires = _cookie_expiration_based_on_max_age(max_age)
=======
        expires = _cookie_expires_from_max_age(max_age)
>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py

    cookie_settings = {
        'max_age': max_age,
        'expires': expires,
        'domain': settings.SESSION_COOKIE_DOMAIN,
        'path': '/',
        'httponly': None,
    }

    # In production, TLS should be enabled so that this cookie is encrypted
    # when we send it.  We also need to set "secure" to True so that the browser
    # will transmit it only over secure connections.
    #
    # In non-production environments (acceptance tests, devstack, and sandboxes),
    # we still want to set this cookie.  However, we do NOT want to set it to "secure"
    # because the browser won't send it back to us.  This can cause an infinite redirect
    # loop in the third-party auth flow, which calls `is_logged_in_cookie_set` to determine
    # whether it needs to set the cookie or continue to the next pipeline stage.
    cookie_settings['secure'] = request.is_secure()

    return cookie_settings


def _cookie_expires_from_max_age(max_age):
    expires_time = time.time() + max_age
    return cookie_date(expires_time)


def set_logged_in_cookies(request, response, user):
    """
<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py
    Set cookies at the time of user login. See ALL_LOGGED_IN_COOKIE_NAMES to see
    which cookies are set.
=======
    Set cookies indicating that the user is logged in.

    Some installations have an external marketing site configured
    that displays a different UI when the user is logged in
    (e.g. a link to the student dashboard instead of to the login page)

    Currently, five cookies are set:

    * EDXMKTG_LOGGED_IN_COOKIE_NAME: Set to 'true' if the user is logged in.
    * EDXMKTG_USER_INFO_COOKIE_VERSION: JSON-encoded dictionary with user information (see below).
    * JWT_AUTH_COOKIE_HEADER_PAYLOAD: Header and payload sections of a JSON Web Token containing user information and used as an access token.
    * JWT_AUTH_COOKIE_SIGNATURE: Signature section of a JSON Web Token.
    * JWT_AUTH_COOKIE_REFRESH_TOKEN: Refresh token which can be used to get a new access token.

    The user info cookie has the following format:
    {
        "version": 1,
        "username": "test-user",
        "header_urls": {
            "account_settings": "https://example.com/account/settings",
            "resume_block":
                "https://example.com//courses/org.0/course_0/Run_0/jump_to/i4x://org.0/course_0/vertical/vertical_4"
            "learner_profile": "https://example.com/u/test-user",
            "logout": "https://example.com/logout"
        }
    }
>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py

    Arguments:
        request (HttpRequest): The request to the view, used to calculate
            the cookie's expiration date based on the session expiration date.
        response (HttpResponse): The response on which the cookie will be set.
        user (User): The currently logged in user.

    Returns:
        HttpResponse

    """
    # Note: The user may not yet be set on the request object by this time,
    # especially during third party authentication.  So use the user object
    # that is passed in when needed.
    if user.is_authenticated and not user.is_anonymous:
<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py

        _set_deprecated_logged_in_cookie(response, request)
        _set_deprecated_user_info_cookie(response, request, user)
        _set_jwt_cookies(response, request, user)
=======
        _set_deprecated_logged_in_cookie(response, request)
        _set_user_info_cookie(response, request, user)
        _set_jwt_cookies(response, request, user)
         # give signal receivers a chance to add cookies
>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py
        CREATE_LOGON_COOKIE.send(sender=None, user=user, response=response)

    return response


def _set_deprecated_logged_in_cookie(response, request):
    """ Sets the logged in cookie on the response. """

    # Backwards compatibility: set the cookie indicating that the user
    # is logged in.  This is just a boolean value, so it's not very useful.
    # In the future, we should be able to replace this with the "user info"
    # cookie set below.
    cookie_settings = standard_cookie_settings(request)

    response.set_cookie(
        settings.EDXMKTG_LOGGED_IN_COOKIE_NAME.encode('utf-8'),
        'true',
        **cookie_settings
    )

    return response


<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py
def _set_deprecated_user_info_cookie(response, request, user):
    """
    Sets the user info cookie on the response.

    The user info cookie has the following format:
    {
        "version": 1,
        "username": "test-user",
        "header_urls": {
            "account_settings": "https://example.com/account/settings",
            "resume_block":
                "https://example.com//courses/org.0/course_0/Run_0/jump_to/i4x://org.0/course_0/vertical/vertical_4"
            "learner_profile": "https://example.com/u/test-user",
            "logout": "https://example.com/logout"
        }
    }
    """
    cookie_settings = standard_cookie_settings(request)

=======
def _set_user_info_cookie(response, request, user):
    """ Sets the user info cookie on the response. """
    cookie_settings = standard_cookie_settings(request)

>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py
    user_info = _get_user_info_cookie_data(request, user)
    response.set_cookie(
        settings.EDXMKTG_USER_INFO_COOKIE_NAME.encode('utf-8'),
        json.dumps(user_info),
        **cookie_settings
    )

def _set_jwt_cookies(response, request, user):
    """ Sets a cookie containing a JWT on the response. """
    cookie_settings = standard_cookie_settings(request)

    oauth_application = Application.objects.get(client_id='doug-id')
    access_token = DOTAdapter().create_access_token(request, request.user, 0, oauth_application)

    jwt_parts = _build_jwt(user).split('.')
    response.set_cookie(
        settings.JWT_AUTH['JWT_AUTH_COOKIE_HEADER_PAYLOAD'].encode('utf-8'),
        '.'.join(jwt_parts[0:2]),
        **cookie_settings
    )

    cookie_settings['httponly'] = True
    response.set_cookie(
        settings.JWT_AUTH['JWT_AUTH_COOKIE_REFRESH_TOKEN'].encode('utf-8'),
        access_token['refresh_token'],
        **cookie_settings
    )
    response.set_cookie(
        settings.JWT_AUTH['JWT_AUTH_COOKIE_SIGNATURE'].encode('utf-8'),
        jwt_parts[2],
        **cookie_settings
    )


def _build_jwt(user):
    """ Builds and returns a JWT. """
    jwt_builder = JwtBuilder(user, asymmetric=True)
    scopes = ['email', 'profile']
    additional_claims = {
        'filters': [],
        'is_restricted': False,
    }
    return jwt_builder.build_token(scopes, additional_claims=additional_claims)


<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py
def _set_jwt_cookies(response, request, user):  # pylint: disable=unused-argument
    """ Sets a cookie containing a JWT on the response. """
    if not JWT_COOKIES_FLAG.is_enabled():
        return
    # TODO (ARCH-236)


def _get_user_info_cookie_data(request, user):
    """ Returns information that will populate the user info cookie. """
=======
def set_experiments_is_enterprise_cookie(request, response, experiments_is_enterprise):
    """ Sets the experiments_is_enterprise cookie on the response.
    This cookie can be used for tests or minor features,
    but should not be used for payment related or other critical work
    since users can edit their cookies
    """
    cookie_settings = standard_cookie_settings(request)

    response.set_cookie(
        'experiments_is_enterprise',
        json.dumps(experiments_is_enterprise),
        **cookie_settings
    )


def _get_user_info_cookie_data(request, user):
    """ Returns information that wil populate the user info cookie. """
>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py

    # Set a cookie with user info.  This can be used by external sites
    # to customize content based on user information.  Currently,
    # we include information that's used to customize the "account"
    # links in the header of subdomain sites (such as the marketing site).
    header_urls = {'logout': reverse('logout')}

    # Unfortunately, this app is currently used by both the LMS and Studio login pages.
    # If we're in Studio, we won't be able to reverse the account/profile URLs.
    # To handle this, we don't add the URLs if we can't reverse them.
    # External sites will need to have fallback mechanisms to handle this case
    # (most likely just hiding the links).
    try:
        header_urls['account_settings'] = reverse('account_settings')
        header_urls['learner_profile'] = reverse('learner_profile', kwargs={'username': user.username})
    except NoReverseMatch:
        pass

    # Add 'resume course' last completed block
    try:
        header_urls['resume_block'] = retrieve_last_sitewide_block_completed(user)
    except User.DoesNotExist:
        pass

    # Convert relative URL paths to absolute URIs
    for url_name, url_path in six.iteritems(header_urls):
        header_urls[url_name] = request.build_absolute_uri(url_path)

    user_info = {
        'version': settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
        'username': user.username,
        'header_urls': header_urls,
        'enrollmentStatusHash': CourseEnrollment.generate_enrollment_status_hash(user)
    }

    return user_info


<<<<<<< HEAD:openedx/core/djangoapps/user_authn/cookies.py
def _cookie_expiration_based_on_max_age(max_age):
    expires_time = time.time() + max_age
    return cookie_date(expires_time)
=======
def delete_logged_in_cookies(response):
    """
    Delete cookies indicating that the user is logged in.

    Arguments:
        response (HttpResponse): The response sent to the client.

    Returns:
        HttpResponse

    """
    for cookie_name in LOGGED_IN_COOKIE_NAMES:
        response.delete_cookie(
            cookie_name.encode('utf-8'),
            path='/',
            domain=settings.SESSION_COOKIE_DOMAIN
        )

    return response


def is_logged_in_cookie_set(request):
    """Check whether the request has logged in cookies set. """
    return all(
        cookie_name in request.COOKIES
        for cookie_name in LOGGED_IN_COOKIE_NAMES
    )
>>>>>>> 2169ccba62... Set JWT cookie auth related cookies on login.:common/djangoapps/student/cookies.py