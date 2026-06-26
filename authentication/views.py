from django.http import HttpResponseRedirect,HttpResponseForbidden
from django.contrib.auth import login, logout
from django.urls import reverse_lazy

import os # import os to access environment variables defined in .env
import dotenv
from django.conf import settings
from authentication.auth.auth_utils import (
    get_sign_in_flow,
    get_token_from_code,
    get_user,
    get_django_user,
    get_logout_url,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add .env variables before assiging the values to the SECRET_KEY variable
dotenv_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

"""
Stephen Mburu modified this view function to support language translations. It
required understanding the custom app built using MSAL Python Azure AD library
Please note that production redirect URIs may have the wrong schema (e.g. http://
instead of https://). In such a case, modify the URLs variables in env to HTTPS:
"""
def microsoft_login(request):
    host = request.get_host()
    language = request.LANGUAGE_CODE # very important here!
    # import pdb; pdb.set_trace()
    if (host.startswith('dct')) or ('stage' in host):
        if language=='en' or language==None:
            redirect=os.environ['REDIRECT_EN'] # redirects to English callback URL
        elif language=='fr':
            redirect=os.environ['REDIRECT_FR'] # redirects to English callback UR
        else:
            redirect=os.environ['REDIRECT_PT'] # redirects to English callback UR
    else:
        if language=='en' or language==None:
            redirect=os.environ['REDIRECT_PYEN'] # redirects to English callback URL
        elif language=='fr':
            redirect=os.environ['REDIRECT_PYFR'] # redirects to English callback UR
        else:
            redirect=os.environ['REDIRECT_PYPT'] # redirects to English callback UR

    flow = get_sign_in_flow(redirect)# Important! pass redirect arg to auth_utils
    request.session['auth_flow'] = flow
    request.session.save()
    return HttpResponseRedirect(flow['auth_uri'])


def microsoft_logout(request):
    logout(request)
    return HttpResponseRedirect(get_logout_url())


"""
Stephen Mburu modified this view function to capture more user profile like email.
first name and surname. These values are passed to get_django_user in auth_utils:
"""

def callback(request):
    firstname = None # initialize user first name attribute
    surname = None # initialize user surname attribute
    result = get_token_from_code(request)
    ms_user = get_user(result['access_token'])
    ms_user['displayName']

    if ms_user['displayName']: # get other use attributes from token
        try:
            if ms_user['displayName'].split()[0]: # get first name
                firstname = ms_user['displayName'].split()[0]
            if ms_user['displayName'].split()[1]:  # get surname
                surname = ms_user['displayName'].split(' ',3)[2]
            else:
                surname = ms_user['displayName'].split()[1]
        except IndexError:
            firstname = ms_user['mail'].split('@')[0]
            surname = ms_user['mail'].split('@')[0]

    user = get_django_user(email=ms_user['mail'],firstname=firstname,
            surname=surname)
    # import pdb; pdb.set_trace()

    if user:
        login(request, user)
    else:
        return HttpResponseForbidden("Invalid email for DCT User.")
    return HttpResponseRedirect(reverse_lazy(settings.LOGIN_REDIRECT_URL or "/admin"))
