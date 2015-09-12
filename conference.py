#!/usr/bin/env python

"""
conference.py -- Udacity conference server-side Python App Engine API;
    uses Google Cloud Endpoints

$Id: conference.py,v 1.25 2014/05/24 23:42:19 wesc Exp wesc $

created by wesc on 2014 apr 21

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'


from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models import ConflictException
from models import Profile
from models import ProfileMiniForm
from models import ProfileForm
from models import BooleanMessage
from models import Conference
from models import ConferenceForm
from models import ConferenceForms
from models import ConferenceQueryForms
from models import Session
from models import SessionForm
from models import SessionForms
from models import SessionType
from models import Speaker
from models import SpeakerForm
from models import SpeakerForms
from models import TeeShirtSize
from models import StringMessage

from utils import getUserId

from settings import WEB_CLIENT_ID

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# Memcache keys
MEMCACHE_ANNOUNCEMENTS_KEY    = "RECENT_ANNOUNCEMENTS"
MEMCACHE_FEATURED_SPEAKER_KEY = "FEATURED_SPEAKER"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CONF_DEFAULTS = {'city'           : 'Default City',
                 'maxAttendees'   : 0,
                 'seatsAvailable' : 0,
                 'topics'         : ['Default', 'Topic'],
                 }

SESH_DEFAULTS = {'duration'      : 0,
                 'typeOfSession' : SessionType.Not_Specified,
                 }

OPERATORS = {'EQ'   : '=',
             'GT'   : '>',
             'GTEQ' : '>=',
             'LT'   : '<',
             'LTEQ' : '<=',
             'NE'   : '!='
             }

FIELDS = {'CITY'          : 'city',
          'TOPIC'         : 'topics',
          'MONTH'         : 'month',
          'MAX_ATTENDEES' : 'maxAttendees',
          }


CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage, websafeConferenceKey=messages.StringField(1))

CONF_POST_REQUEST = endpoints.ResourceContainer(
    ConferenceForm, websafeConferenceKey=messages.StringField(1))

SESH_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm, websafeConferenceKey=messages.StringField(1))

SESH_BY_TYPE_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required=True),
    typeOfSession        = messages.StringField(2, required=True))

SESH_BY_DATE_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required=True),
    date                 = messages.StringField(2, required=True))

SESH_BY_SPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    speakerKey = messages.StringField(1, required=True))

SESH_BY_TIME_AND_TYPE_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required=True),
    noLaterThen          = messages.StringField(2, required=True),
    typeOfSession        = messages.StringField(3, required=True))

SESH_POST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    webSafeSeshKey = messages.StringField(1, required=True))


@endpoints.api(name               = 'conference',
               version            = 'v1',
               allowed_client_ids = [WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
               scopes             = [EMAIL_SCOPE])
class ConferenceApi(remote.Service):
    """Conference API v0.1"""


# - - - Speaker objects - - - - - - - - - - - - - - - - -

    def _copySpeakerToForm(self, speaker):
        """Copy relevant fields from Speaker to SpeakerForm"""
        sf = SpeakerForm()
        for field in sf.all_fields():
            if hasattr(speaker, field.name):
                setattr(sf, field.name, getattr(speaker, field.name))
            elif field.name == "websafeKey":
                setattr(sf, field.name, speaker.key.urlsafe())
        sf.check_initialized()
        return sf

    def _createSpeakerObject(self, request):
        """Create a Speaker object, returning SpeakerForm/request."""
        # Ensure that the current user is logged in and get user ID
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        # Verify that a name was provided for the speaker
        if not request.name:
            raise endpoints.BadRequestException(
                "Speaker 'name' field required")
        # Copy SpeakerForm/ProtoRPC Message into dict
        data = ({field.name: getattr(request, field.name)
                for field in request.all_fields()})
        # Create a key for the Speaker
        s_id  = Session.allocate_ids(size=1)[0]
        s_key = ndb.Key(Speaker, s_id)
        # Update stored session with session keys
        data['key'] = s_key
        # create Session, send email to organizer confirming
        # creation of Session & return (modified) SessionForm
        Speaker(**data).put()
        taskqueue.add(
            params = {
                'email'   : user.email(),
                'subject' : 'You Added %s as a Speaker!' % data['name'],
                'body'    : 'Here are the details for the added speaker:',
                'info'    : repr(request)},
            url    = '/tasks/send_confirmation_email')
        return request

    @endpoints.method(SpeakerForm, SpeakerForm,
                      path        = 'speaker',
                      http_method = 'POST',
                      name        = 'createSpeaker')
    def createSpeaker(self, request):
        """Create a new Speaker."""
        print '::::: request = %s' % request
        return self._createSpeakerObject(request)

    @endpoints.method(CONF_GET_REQUEST, SpeakerForms,
                      path        = ('getSpeakersByConference/'
                                     '{websafeConferenceKey}'),
                      http_method = 'GET',
                      name        = 'getSpeakersByConference')
    def getSpeakersByConference(self, request):
        """Given a conference, return all speakers."""
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Retrieve the Conference key
        try:
            c_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        except Exception:
            raise endpoints.BadRequestException(
                'The websafeConferenceKey given is invalid.')
        # Verify that the conference exists
        conf = c_key.get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found for the key provided: %s'
                % request.websafeConferenceKey)
        # Store the Sessions that are ancestors of the Conference
        sessions = Session.query(ancestor=c_key)
        # Retrieve Speaker Keys from each Session in a Conference
        speakerKeys = set([])
        for sesh in sessions:
            for wssk in sesh.speakerKey:
                speaker_key = ndb.Key(urlsafe=wssk)
                # Utilize add to set to eliminate duplicate results
                speakerKeys.add(speaker_key)
        # Get each speaker using its key and appended it to the final list
        speakers = []
        for spkr in speakerKeys:
            speaker = spkr.get()
            speakers.append(speaker)
        # Return a SpeakerForm for each Speaker
        return SpeakerForms(
            items = [self._copySpeakerToForm(
                spkr) for spkr in speakers])


# - - - wishList methods - - - - - - - - - - - - - - - - - - -

    def _sessionWishlist(self, request, add=True):
        """Add or remove a session to a User's wishlist."""
        retval = None
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Get user's profile
        prof = self._getProfileFromUser()
        # Get Session being passed
        try:
            sesh_key = ndb.Key(urlsafe=request.webSafeSeshKey)
        except Exception:
            raise endpoints.BadRequestException(
                'The websafeSessionKey given is invalid.')
        session = sesh_key.get()
        # Throw Not Found Error if no Session found
        if not sesh_key:
            raise endpoints.NotFoundException(
                'No session found with key: {0}'.format(sesh_key))
        # Get Session parent key and associated Conference
        conference = session.key.parent().get()
        conf_key = conference.key.urlsafe()
        # Ensure that conference is in User's conferenceKeysToAttend
        if conf_key not in prof.conferenceKeysToAttend:
            raise ConflictException(
                "You must be register for the parent confernce before adding",
                "a session to your wishlist.")
        if add:
            # Check if session is already in wishlist
            if request.webSafeSeshKey in prof.sessionWishList:
                raise ConflictException(
                    "This Session is already in your wishlist.")
            # Add session to User's wishlist
            prof.sessionWishList.append(request.webSafeSeshKey)
            retval = True
        else:
            # Check if session is already in wishlist
            if request.webSafeSeshKey in prof.sessionWishList:
                # Remove Session from User's wishlist
                prof.sessionWishList.remove(request.webSafeSeshKey)
                retval = True
            else:
                retval = False
        prof.put()
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, SessionForms,
                      path        = 'view/session_wishlist',
                      http_method = 'GET',
                      name        = 'getSessionWishlist')
    def getSessionWishlist(self, request):
        """Get list of sessions in the current user's wishlist."""
        # Get user's profile
        prof = self._getProfileFromUser()
        sesh_keys = [ndb.Key(urlsafe=wssk) for wssk in
                     prof.sessionWishList]
        sessions = ndb.get_multi(sesh_keys)
        # return set of SessionForm objects per Session
        return SessionForms(
            items=[self._copyConferenceSessionToForm(
                sesh) for sesh in sessions])

    @endpoints.method(SESH_POST_REQUEST, BooleanMessage,
                      path        = 'sessionToWishlist/{webSafeSeshKey}',
                      http_method = 'POST',
                      name        = 'addSessionToWishlist')
    def addSessionToWishlist(self, request):
        """Add a session to the User's wishlist."""
        return self._sessionWishlist(request)

    @endpoints.method(SESH_POST_REQUEST, BooleanMessage,
                      path        = 'removeSessionFromWishlist/'
                                    '{webSafeSeshKey}',
                      http_method = 'DELETE',
                      name        = 'removeSessionFromWishlist')
    def removeSessionFromWishlist(self, request):
        """Remove a session from the User's wishlist."""
        return self._sessionWishlist(request, add=False)


# - - - Session objects - - - - - - - - - - - - - - - - -

    def _copyConferenceSessionToForm(self, sesh):
        """Copy relevant fields from Session to SessionForm."""
        sf = SessionForm()
        for field in sf.all_fields():
            if hasattr(sesh, field.name):
                # Convert date and startTime fields to strings
                if field.name == 'date' or field.name == 'startTime':
                    setattr(sf, field.name, str(getattr(sesh, field.name)))
                # Convert typeOfSession to enum
                elif field.name == 'typeOfSession':
                    setattr(sf, field.name, getattr(SessionType,
                                                    getattr(sesh, field.name)))
                # Just copy over the remaining fields
                else:
                    setattr(sf, field.name, getattr(sesh, field.name))
            # Convert Datastore keys in to URL compatible strings
            elif field.name == 'parentConfKey' or field.name == 'speakerKey':
                setattr(sf, field.name, sesh.key.urlsafe())
        sf.check_initialized()
        return sf

    @endpoints.method(CONF_GET_REQUEST, SessionForms,
                      path        = 'getSessionsByConference/'
                                    '{websafeConferenceKey}',
                      http_method = 'GET',
                      name        = 'getSessionsByConference')
    def getConferenceSessions(self, request):
        """Given a conference, return all sessions."""
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Retrieve the Conference key
        try:
            c_key = ndb.Key(urlsafe=request.websafeConferenceKey)
        except Exception:
            raise endpoints.BadRequestException(
                'The websafeConferenceKey given is invalid.')
        # Verify that the Conference exists
        conf = c_key.get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found for the key provided: %s'
                % request.websafeConferenceKey)
        # Store the Sessions that are ancestors of the Conference
        sessions = Session.query(ancestor=c_key)
        # Return a SessionForm for each Session
        return SessionForms(
            items = [self._copyConferenceSessionToForm(
                sesh) for sesh in sessions])

    @endpoints.method(SESH_BY_TYPE_GET_REQUEST, SessionForms,
                      path        = 'getConfSessionsByType/'
                                    '{websafeConferenceKey}/{typeOfSession}',
                      http_method = 'GET',
                      name        = 'getConfSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Given a conference and session type, return matching sessions."""
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Limit Sessions by Conference key
        sessions = Session.query(
            ancestor=ndb.Key(urlsafe=request.websafeConferenceKey))
        # Filter remaining Sessions by type specified
        sessions = sessions.filter(
            Session.typeOfSession == request.typeOfSession)
        # Return a SessionForm for each Session
        return SessionForms(
            items = [self._copyConferenceSessionToForm(
                sesh) for sesh in sessions])

    @endpoints.method(SESH_BY_DATE_GET_REQUEST, SessionForms,
                      path        = 'getConfSessionsByDate/'
                                    '{websafeConferenceKey}/{date}',
                      http_method = 'GET',
                      name        = 'getConfSessionsByDate')
    def getConferenceSessionsByDate(self, request):
        """Given a conference and date, return matching sessions."""
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Limit Sessions by Conference key
        sessions = Session.query(
            ancestor=ndb.Key(urlsafe=request.websafeConferenceKey))
        # Convert the date string passed to date object
        date = datetime.strptime(request.date[:10], "%Y-%m-%d").date()
        # Filter remaining Sessions by date
        sessions = sessions.filter(Session.date == date)
        # Return a SessionForm for each Session
        return SessionForms(
            items = [self._copyConferenceSessionToForm(
                sesh) for sesh in sessions])

    # Implementation of Task 3 challenge
    @endpoints.method(SESH_BY_TIME_AND_TYPE_GET_REQUEST, SessionForms,
                      path        = 'getConfSessionsByTimeType/'
                                    '{websafeConferenceKey}',
                      http_method = 'GET',
                      name        = 'getConfSessionsByTimeAndType')
    def getConferenceSessionsByTimeAndType(self, request):
        """Given a conference, Session Type and date,
        return matching sessions.
        """
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Limit Sessions by Conference key
        confSessions = Session.query(
            ancestor=ndb.Key(urlsafe=request.websafeConferenceKey))
        # convert the time string passed to time() object
        lastTime = datetime.strptime(request.noLaterThen[:5], "%H:%M").time()
        # Retrieve Sessions that start on or before the noLaterThen time
        timeSessions = confSessions.filter(Session.startTime <= lastTime)
        # Store a list of the Keys that meet the time criteria
        timeKeys = [sesh.key for sesh in timeSessions]
        # Retrieve Sessions that are not of the typeOfSession passed in
        typeSessions = confSessions.filter(
            Session.typeOfSession != request.typeOfSession)
        # filter typeSessions by timeSession Keys
        sessions = typeSessions.filter(Session.key.IN(timeKeys))
        # Return a SessionForm for each Session
        return SessionForms(
            items = [self._copyConferenceSessionToForm(
                sesh) for sesh in sessions])

    @endpoints.method(SESH_BY_SPEAKER_GET_REQUEST, SessionForms,
                      path        = 'getSessionsBySpeaker/{speakerKey}',
                      http_method = 'GET',
                      name        = 'getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Given a Speaker, return all sessions with that Speaker, regardless
        of Conference.
        """
        # Ensure that user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        # Filter Sessions by Speaker key
        sessions = Session.query(Session.speakerKey == request.speakerKey)
        # Return a SessionForm for each Session
        return SessionForms(
            items = [self._copyConferenceSessionToForm(
                sesh) for sesh in sessions])

    def _createSessionObject(self, request):
        """Create a Session object, returning SessionForm/request."""
        # Ensure that the current user is logged in and get user ID
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        # Verify that a name and parentConfKey were provided for the Session
        if not request.name and request.parentConfKey:
            raise endpoints.BadRequestException(
                "Session 'name' and 'parentConfKey' are required fields.")
        # Attempt to retrieve the Conference details using the Confernce key
        try:
            c_key = ndb.Key(urlsafe=request.parentConfKey)
        except Exception:
            raise endpoints.BadRequestException(
                'The parentConfKey given is invalid.')
        conf = c_key.get()
        # Verify that the current user created the conference
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the conference creator can add a session to it.')
        # Verify the the speakerKeys provided are valid and store in speakers
        speakers = []
        if request.speakerKey:
            for speakerKey in request.speakerKey:
                try:
                    speaker = ndb.Key(urlsafe=speakerKey).get()
                    speakers.append(speaker)
                except Exception:
                    raise endpoints.BadRequestException(
                        'speakerKey {0} is invalid.'.format(speakerKey))
        # Copy SessionForm/ProtoRPC Message into dict
        data = ({field.name: getattr(request, field.name)
                for field in request.all_fields()})
        # If values not given for Session defaults, add defaults
        for df in SESH_DEFAULTS:
            if data[df] in (None, []):
                data[df] = SESH_DEFAULTS[df]
                setattr(request, df, SESH_DEFAULTS[df])
        # Convert dates from strings to Date objects;
        # set month based on start_date
        if data['date']:
            data['date'] = (datetime.strptime(
                            data['date'][:10], "%Y-%m-%d").date())
            data['month'] = data['date'].month
        else:
            data['month'] = conf.month
        # Convert startTime from string to Time object
        if data['startTime']:
            data['startTime'] = (datetime.strptime(
                                 data['startTime'][:5], "%H:%M").time())
        # Convert typeOfSession Enum to string
        if data['typeOfSession']:
            data['typeOfSession'] = str(data['typeOfSession'])
        # Create a key for the Session
        s_id  = Session.allocate_ids(size=1, parent=c_key)[0]
        s_key = ndb.Key(Session, s_id, parent=c_key)
        # Update stored session with session keys
        data['key'] = s_key
        # Check that speakerKeys were passed with request
        if speakers:
            # Adding checks here to prevent task creation if not needed
            # TODO Is it better to perform these checks here or
            # in _cacheFeaturedSpeaker?
            s = Session.query(
                ancestor=ndb.Key(urlsafe=request.parentConfKey))
            # Determine which Speaker is associated with the most Sessions
            featured = None
            minSessions = 0
            for spkr in data['speakerKey']:
                count = s.filter(Session.speakerKey == spkr).count()
                if count >= minSessions:
                    featured = spkr
                    minSessions = count
            # If a speaker is associated with more than 1 Session, add them as
            # the featured speaker
            if featured:
                taskqueue.add(
                    params = {
                        'websafeConferenceKey': request.parentConfKey,
                        'websafeSpeakerKey'   : featured},
                    url    = '/tasks/set_featured_speaker',
                    method = 'GET')
        # Store the created Session in the datastore
        Session(**data).put()
        # Send an email to the conference organizer
        taskqueue.add(
            params = {
                'email'   : user.email(),
                'subject' : 'You Created a New Session for %s!' % conf.name,
                'body'    : 'Here are the details for your session:',
                'info'    : repr(request)},
            url    = '/tasks/send_confirmation_email')
        return request

    @endpoints.method(SessionForm, SessionForm,
                      path        = 'session',
                      http_method = 'POST',
                      name        = 'createSession')
    def createSession(self, request):
        """Create a new Session."""
        return self._createSessionObject(request)


# - - - Conference objects - - - - - - - - - - - - - - - - -

    def _copyConferenceToForm(self, conf, displayName):
        """Copy relevant fields from Conference to ConferenceForm."""
        cf = ConferenceForm()
        for field in cf.all_fields():
            if hasattr(conf, field.name):
                # convert Date to date string; just copy others
                if field.name.endswith('Date'):
                    setattr(cf, field.name, str(getattr(conf, field.name)))
                else:
                    setattr(cf, field.name, getattr(conf, field.name))
            elif field.name == "websafeKey":
                setattr(cf, field.name, conf.key.urlsafe())
        if displayName:
            setattr(cf, 'organizerDisplayName', displayName)
        cf.check_initialized()
        return cf

    @endpoints.method(CONF_GET_REQUEST, ConferenceForm,
                      path        = 'conference/{websafeConferenceKey}',
                      http_method = 'GET',
                      name        = 'getConference')
    def getConference(self, request):
        """Return requested conference (by websafeConferenceKey)."""
        # get Conference object from request; bail if not found
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)
        prof = conf.key.parent().get()
        # return ConferenceForm
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    def _createConferenceObject(self, request):
        """Create a Conference object, returning ConferenceForm/request."""
        # preload necessary data items
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        if not request.name:
            raise endpoints.BadRequestException(
                "Conference 'name' field required")
        # copy ConferenceForm/ProtoRPC Message into dict
        data = ({field.name: getattr(request, field.name)
                for field in request.all_fields()})
        del data['websafeKey']
        del data['organizerDisplayName']
        # add default values for those missing
        # (both data model & outbound Message)
        for df in CONF_DEFAULTS:
            if data[df] in (None, []):
                data[df] = CONF_DEFAULTS[df]
                setattr(request, df, CONF_DEFAULTS[df])
        # convert dates from strings to Date objects;
        # set month based on start_date
        if data['startDate']:
            data['startDate'] = (
                datetime.strptime(data['startDate'][:10], "%Y-%m-%d").date()
            )
            data['month']     = data['startDate'].month
        else:
            data['month'] = 0
        if data['endDate']:
            data['endDate'] = (
                datetime.strptime(data['endDate'][:10], "%Y-%m-%d").date()
            )
        # set seatsAvailable to be same as maxAttendees on creation
        if data["maxAttendees"] > 0:
            data["seatsAvailable"] = data["maxAttendees"]
        # generate Profile Key based on user ID and Conference
        # ID based on Profile key get Conference key from ID
        p_key = ndb.Key(Profile, user_id)
        c_id  = Conference.allocate_ids(size=1, parent=p_key)[0]
        c_key = ndb.Key(Conference, c_id, parent=p_key)
        # Update stored conference with profile and conference keys
        data['key']             = c_key
        data['organizerUserId'] = request.organizerUserId = user_id
        # create Conference, send email to organizer confirming
        # creation of Conference & return (modified) ConferenceForm
        Conference(**data).put()
        taskqueue.add(
            params = {
                'email'   : user.email(),
                'subject' : 'You Created a New Conference!',
                'body'    : 'Here are the details for your conference:',
                'info'    : repr(request)},
            url    = '/tasks/send_confirmation_email')
        return request

    @endpoints.method(ConferenceForm, ConferenceForm,
                      path        = 'conference',
                      http_method = 'POST',
                      name        = 'createConference')
    def createConference(self, request):
        """Create new conference."""
        return self._createConferenceObject(request)

    @ndb.transactional()
    def _updateConferenceObject(self, request):
        """Update a Conference object, returning the updated ConferenceForm().
        """
        # Get user if logged in, if not throw exception
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        # copy ConferenceForm/ProtoRPC Message into dict
        data = ({field.name: getattr(request, field.name)
                for field in request.all_fields()}
                )
        # update existing conference
        conf = ndb.Key(urlsafe=request.websafeConferenceKey).get()
        # check that conference exists
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s'
                % request.websafeConferenceKey)
        # check that user is owner
        if user_id != conf.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')
        # Not getting all the fields, so don't create a new object; just
        # copy relevant fields from ConferenceForm to Conference object
        for field in request.all_fields():
            data = getattr(request, field.name)
            # only copy fields where we get data
            if data not in (None, []):
                # special handling for dates (convert string to Date)
                if field.name in ('startDate', 'endDate'):
                    data = datetime.strptime(data, "%Y-%m-%d").date()
                    if field.name == 'startDate':
                        conf.month = data.month
                # write to Conference object
                setattr(conf, field.name, data)
        conf.put()
        prof = ndb.Key(Profile, user_id).get()
        return self._copyConferenceToForm(conf, getattr(prof, 'displayName'))

    def _getQuery(self, request):
        """Return formatted query from the submitted filters."""
        q = Conference.query()
        inequality_filter, filters = self._formatFilters(request.filters)
        # If exists, sort on inequality filter first
        if not inequality_filter:
            q = q.order(Conference.name)
        else:
            q = q.order(ndb.GenericProperty(inequality_filter))
            q = q.order(Conference.name)
        # Format filters and store in a formatted query
        for filtr in filters:
            if filtr["field"] in ["month", "maxAttendees"]:
                filtr["value"] = int(filtr["value"])
            formatted_query = ndb.query.FilterNode(filtr["field"],
                                                   filtr["operator"],
                                                   filtr["value"])
            q = q.filter(formatted_query)
        return q

    def _formatFilters(self, filters):
        """Parse, check validity and format user supplied filters."""
        formatted_filters = []
        inequality_field = None
        for f in filters:
            filtr = ({field.name: getattr(f, field.name)
                     for field in f.all_fields()})
            try:
                filtr["field"]    = FIELDS[filtr["field"]]
                filtr["operator"] = OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException(
                    "Filter contains invalid field or operator.")
            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                # check if inequality operation has been used in previous
                # filters and disallow the filter if inequality was
                # performed on a different field before
                # Also track the field on which the inequality operation
                # is performed
                if inequality_field and inequality_field != filtr["field"]:
                    raise endpoints.BadRequestException(
                        "Inequality filter is allowed on only one field.")
                else:
                    inequality_field = filtr["field"]
            # Update formatted_fiters with new formatting
            formatted_filters.append(filtr)
        return (inequality_field, formatted_filters)

    @endpoints.method(ConferenceQueryForms, ConferenceForms,
                      path        = 'queryConferences',
                      http_method = 'POST',
                      name        = 'queryConferences')
    def queryConferences(self, request):
        """Query for conferences."""
        conferences = self._getQuery(request)
        # need to fetch organiser displayName from profiles
        # get all keys and use get_multi for speed
        organisers = ([(ndb.Key(Profile, conf.organizerUserId)) for conf in
                      conferences])
        profiles = ndb.get_multi(organisers)
        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName
        # return individual ConferenceForm object per Conference
        return ConferenceForms(
            items = [self._copyConferenceToForm(
                conf, names[conf.organizerUserId]) for conf in conferences])

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path        = 'getConferencesCreated',
                      http_method = 'POST',
                      name        = 'getConferencesCreated')
    def getConferencesCreated(self, request):
        """Return conferences created by user."""
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        user_id = getUserId(user)
        # create ancestor query for all key matches for this user
        confs = Conference.query(ancestor=ndb.Key(Profile, user_id))
        prof = ndb.Key(Profile, user_id).get()
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items = [self._copyConferenceToForm(
                conf, getattr(prof, 'displayName')) for conf in confs])


# - - - Profile objects - - - - - - - - - - - - - - - - - - -

    def _copyProfileToForm(self, prof):
        """Copy relevant fields from Profile to ProfileForm."""
        # copy relevant fields from Profile to ProfileForm
        pf = ProfileForm()
        for field in pf.all_fields():
            if hasattr(prof, field.name):
                # convert t-shirt string to Enum; just copy others
                if field.name == 'teeShirtSize':
                    setattr(pf, field.name,
                            getattr(TeeShirtSize, getattr(prof, field.name)))
                else:
                    setattr(pf, field.name, getattr(prof, field.name))
        pf.check_initialized()
        return pf

    def _getProfileFromUser(self):
        """Return user Profile from datastore,
        creating new one if non-existent.
        """
        # make sure user is authed
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        # get Profile from datastore
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        profile = p_key.get()
        # create new Profile if not there
        if not profile:
            profile = Profile(key          = p_key,
                              displayName  = user.nickname(),
                              mainEmail    = user.email(),
                              teeShirtSize = str(TeeShirtSize.NOT_SPECIFIED),)
            profile.put()
        return profile  # return Profile

    def _doProfile(self, save_request=None):
        """Get user Profile and return to user, possibly updating it first."""
        # get user Profile
        prof = self._getProfileFromUser()
        # if saveProfile(), process user-modifyable fields
        if save_request:
            for field in ('displayName', 'teeShirtSize'):
                if hasattr(save_request, field):
                    val = getattr(save_request, field)
                    if val:
                        setattr(prof, field, str(val))
                        if field == 'teeShirtSize':
                            setattr(prof, field, str(val).upper())
                        else:
                            setattr(prof, field, val)
            prof.put()
        # return ProfileForm
        return self._copyProfileToForm(prof)

    @endpoints.method(message_types.VoidMessage, ProfileForm,
                      path        = 'profile',
                      http_method = 'GET',
                      name        = 'getProfile')
    def getProfile(self, request):
        """Return user profile."""
        return self._doProfile()

    @endpoints.method(ProfileMiniForm, ProfileForm,
                      path        = 'profile',
                      http_method = 'POST',
                      name        = 'saveProfile')
    def saveProfile(self, request):
        """Update & return user profile."""
        return self._doProfile(request)


# - - - Registration - - - - - - - - - - - - - - - - - - - -

    @ndb.transactional(xg=True)
    def _conferenceRegistration(self, request, reg=True):
        """Register or unregister user for selected conference."""
        retval = None
        prof = self._getProfileFromUser()  # get user Profile
        # check if conf exists given websafeConfKey
        # get conference; check that it exists
        wsck = request.websafeConferenceKey
        conf = ndb.Key(urlsafe=wsck).get()
        if not conf:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % wsck)
        # register
        if reg:
            # check if user already registered otherwise add
            if wsck in prof.conferenceKeysToAttend:
                raise ConflictException(
                    "You have already registered for this conference")
            # check if seats avail
            if conf.seatsAvailable <= 0:
                raise ConflictException(
                    "There are no seats available.")
            # register user, take away one seat
            prof.conferenceKeysToAttend.append(wsck)
            conf.seatsAvailable -= 1
            retval = True
        # unregister
        else:
            # check if user already registered
            if wsck in prof.conferenceKeysToAttend:

                # unregister user, add back one seat
                prof.conferenceKeysToAttend.remove(wsck)
                conf.seatsAvailable += 1
                retval = True
            else:
                retval = False
        # write things back to the datastore & return
        prof.put()
        conf.put()
        return BooleanMessage(data=retval)

    @endpoints.method(message_types.VoidMessage, ConferenceForms,
                      path        = 'conferences/attending',
                      http_method = 'GET',
                      name        = 'getConferencesToAttend')
    def getConferencesToAttend(self, request):
        """Get list of conferences that user has registered for."""
        prof = self._getProfileFromUser()  # get user Profile
        conf_keys = [ndb.Key(urlsafe=wsck) for wsck in
                     prof.conferenceKeysToAttend]
        conferences = ndb.get_multi(conf_keys)
        # get organizers
        organisers = [ndb.Key(Profile, conf.organizerUserId) for conf in
                      conferences]
        profiles = ndb.get_multi(organisers)
        # put display names in a dict for easier fetching
        names = {}
        for profile in profiles:
            names[profile.key.id()] = profile.displayName
        # return set of ConferenceForm objects per Conference
        return ConferenceForms(
            items=[self._copyConferenceToForm(
                conf, names[conf.organizerUserId])
                for conf in conferences])

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path        = 'conference/{websafeConferenceKey}',
                      http_method = 'POST',
                      name        = 'registerForConference')
    def registerForConference(self, request):
        """Register user for selected conference."""
        return self._conferenceRegistration(request)

    @endpoints.method(CONF_GET_REQUEST, BooleanMessage,
                      path        = 'conference/{websafeConferenceKey}',
                      http_method = 'DELETE',
                      name        = 'unregisterFromConference')
    def unregisterFromConference(self, request):
        """Unregister user for selected conference."""
        return self._conferenceRegistration(request, reg=False)


# - - - Announcements - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheAnnouncement():
        """Create Announcement & assign to memcache.
        """
        confs = Conference.query(ndb.AND(
            Conference.seatsAvailable <= 5,
            Conference.seatsAvailable > 0)
        ).fetch(projection=[Conference.name])
        if confs:
            # If there are almost sold out conferences,
            # format announcement and set it in memcache
            announcement = '%s %s' % (
                'Last chance to attend! The following conferences '
                'are nearly sold out:',
                ', '.join(conf.name for conf in confs))
            memcache.set(MEMCACHE_ANNOUNCEMENTS_KEY, announcement)
        else:
            # If there are no sold out conferences,
            # delete the memcache announcements entry
            announcement = ""
            memcache.delete(MEMCACHE_ANNOUNCEMENTS_KEY)
        return announcement

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path        = 'conference/announcement/get',
                      http_method = 'GET',
                      name        = 'getAnnouncement')
    def getAnnouncement(self, request):
        """Return Announcement from memcache."""
        # return an existing announcement from Memcache or an empty string.
        announcement = memcache.get(MEMCACHE_ANNOUNCEMENTS_KEY)
        if not announcement:
            announcement = ""
        return StringMessage(data=announcement)


# - - - Featured Speakers - - - - - - - - - - - - - - - - - - - -

    @staticmethod
    def _cacheFeaturedSpeaker(websafeConferenceKey, websafeSpeakerKey):
        """Create Featured Speaker & assign to memcache."""
        # TODO The example given was to perform checks here
        # (ie speaker in 2 or more sessions), however for this function,
        # I performed the check in the _createSessionObject function
        # Which is better and why?

        c_key = ndb.Key(urlsafe=websafeConferenceKey)
        conf = c_key.get()
        print '::::: conf = {0}'.format(conf)

        s_key = ndb.Key(urlsafe=websafeSpeakerKey)
        speaker = s_key.get()

        featured = '{0}{1}{2}'.format(speaker.name,
                                      ' has been added as a'
                                      ' featured speaker at ',
                                      conf.name)
        memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, featured)
        return featured

    @endpoints.method(message_types.VoidMessage, StringMessage,
                      path        = 'featured_speaker/get',
                      http_method = 'GET',
                      name        = 'getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Return Featured Speaker from memcache."""
        # return an existing Featured Speaker from Memcache or an empty string.
        featured = memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY)
        if not featured:
            featured = ""
        return StringMessage(data=featured)

api = endpoints.api_server([ConferenceApi])  # register API
