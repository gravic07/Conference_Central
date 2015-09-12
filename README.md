# Conference Central

This application was created as my submission for project 4 of Udacity's
Full Stack Nanodegree program.  The objective of project 4 is develop a
EndPoints using Google's App Engine.  All of the work done was focused on the
back end and creating the API.


## Design Decisions
#### Sessions
Sessions are the individual events that make up a conference.  Sessions can
have several formats.  Workshop, Lecture, Keynote, Demo and Panel have been
provided as options for the **SessionType**.  Since you can not have a
session without a conference, sessions require a conference key to be passed
under **parentConfKey**.  This conference key is used to establish an ancestor
relationship between the conference and the session. In addition to
**parentConfKey**, the **name** property is also a required field.  To prevent
unwanted sessions being created, only the creator of a conference can add
sessions to it.

#### Speakers
In their current capacity, speakers are associated with most sessions as the
main attraction.  Since a speaker can attend more than one session, or even
more than one conference, speakers are there own entity with the following
properties: **name**, **briefBio**, **company** and **projects**.  **name**
is the only required property for a speaker.  A speaker has no ancestor
relationship since a speaker can attend multiple conferences and sessions.

#### Session & Speaker Relationship
A speaker is added to a session using the speaker's key, through the session's
**speakerKey**.  A session's **speakerKey** property allows for more than one
speaker since sessions can have multiple speakers or a panel.  Each key is
passed is verified individually and an exception is thrown if one is invalid.

#### Featured Speakers
A featured speaker is defined as a speaker that is assigned to two or more
sessions within a conference.  When a session is created within
`_createSessionObject()`, a check is performed on each **speakerKey** that is
passed in.  For each speakerKey, the number of sessions for the speaker is
calculated.  The speaker with the most sessions is then set as the featured
speaker and added to the task queue through `_cacheFeaturedSpeaker()` to be
added to memcache.  If there is a tie for number of sessions, the last speaker
passed is assigned the featured speaker.

#### User Wish Lists
A User can add sessions to their wish list using `addSessionToWishlist()` and
passing in the session key.  A user must be registered to the parent
conference of a session to add it to their wish list.  The session's key is
added to the user's profile under the **sessionWishList** property.  A user
can also remove a session from their wish list using
`removeSessionFromWishlist()`.  Additionally you can retrieve all sessions in
a user's wish list by calling getSessionWishlist() while a user is authed.

#### Additional Queries
- `getSpeakersByConference()` takes in a conference key and returns all
speakers in that conference, regardless of session.  This can be used to
quickly see the speaker lineup for an entire conference.
- `getConferenceSessionsByDate()` takes in a conference key and date to return
all sessions for the parent conference matching the specified date.  This
would allow a participant to decided what days might be more valuable to them
based on the sessions that are available.

#### Query Problem Solution
**Question posed in project:** Let’s say that you don't like workshops and you
don't like sessions after 7 pm. How would you handle a query for all non-
workshop sessions before 7 pm? What is the problem for implementing this query?
What ways to solve it did you think of?

###### The Problem
The problem here is that we are trying to perform inequality filters on two
separate properties.  Within Datastore, inequality filters can only be applied
to one property.  Additionally, any properties with an inequality filter must
be sorted first, all though this is not an issue with the above problem.

###### Possible Solutions
- **Comparing two separate queries:** The first solution that I thought of was
to perform two separate queries, one for sessions no later then 7pm and another
for sessions that are not workshops.  With both of these queries complete, the
results can then be compared and only the matching sessions will be returned as
the result.  
This was the solution that I used in `getConferenceSessionsByTimeAndType()`
- **Filter results programmatically:** This solution would perform a query on
the database and then filter the results using the language of choice; Python
in this case.  In the above example, we could query for sessions that are not
workshops and store them locally.  We could then filter the stored results by
**startTime**.
- **Combinding properties into new property:** This is a solution that I found
through a bit of Googling that peaked my interest.  From what I have read, this
would be a great solution for larger data bases that have a specific multi-
property inequality filter that is used frequently.  Essentially we would need
to rewrite the Model and session creation function so that the **startTime**
property and **typeOfSession** property could be combined into a new value.  
This one was a little over my head, but I found it interesting enough to
include.


## Important Files
| File | Description |
|------|-------------|
| **conference.py** | This is the main Python file which contains the ConferenceApi(). |
| **models.py** | This Python file holds the Model and Message structures for Google's Datastore (ndb). |
| **main.py** | This Python file contains the HTTP controller handlers for memcache & task queue. |
| **settings.py** | This Python file holds a user's client IDs. *This file will need to be updated if you are wanting to deploy the application.* |
| **utils.py** | This Python file holds a utility function to grab a user's ID. |
| **app.yaml** | Google App Engine configuration file containing application and path information. |
| **cron.yaml** | Google App Engine configuration file containing settings for scheduled tasks. |
| **index.yaml** | Google App Engine configuration file containing indexes for queries. |
| **templates Folder** | Stores the main HTML template for the application. |
| **static Folder** | Stores all dependencies/resources for the HTML templates, including partials.. |


## Installation & Use
####Prerequisites:
| Prerequisite | Documentation | Download |
|---------------|---------------|----------|
| **Git** | [docs](https://git-scm.com/doc) | [download](http://git-scm.com/downloads) |
| **Python 2.7** | [docs](https://docs.python.org/2.7/) | [download](https://www.python.org/downloads/) |
| **Google App Engine SDK** | [docs](https://cloud.google.com/appengine/docs) | [download](https://cloud.google.com/appengine/downloads) |


#### Installation Steps:
1. Open terminal:
  - Windows: Use the Git Bash program (installed with Git) to get a Unix-style
  terminal.
  - Other systems: Use your favorite terminal program.
2. Change to the desired parent directory
  - Example: `cd Desktop/`
3. Using Git, clone this project:
  - Run: `git clone https://github.com/gravic07/Conference_Central.git
  Conference_Central`
  - This will create a directory inside of your parent directory titled
  *Conference_Central*.
4. Download the Google App Engine SDK *for Python* using the link listed under
**Prerequisites**.
5. Once the SDK is installed, open GoogleAppEngineLauncher.
6. Under File, select *Add Existing Application...*.
7. Select *Browse* and navigate to the newly created Conference_Central Folder.
8. (Optional) Adjust the *Admin Port* and *Port* if desired and make note of
both.
9. With the newly added application highlighted, press *Run*.
10. The APIs explorer should now be available at
http://localhost:8080/_ah/api/explorer
  - The url above assumes the default port.  If *Port* was altered in step 8,
  replace *8080* with the new port provided.
11. Select *conference API* to access all EndPoints.


## EndPoints
- **addSessionToWishlist** - Adds an existing session to the authed user's wish
list using the Session's key.
- **createConference** - Creates a conference; *name* property is required.
- **createSession** - Creates a session; *name* and *parentConfKey* properties
are required.
- **createSpeaker** - Creates a ppeaker; *name* property is required.
- **getAnnouncement** - Retrieve announcement for conferences that are almost
sold out.
- **getConfSessionsByDate** - Retrieve sessions by conference key and date.
- **getConfSessionsByType** - Retrieve sessions by conference key and session
type.
- **getConference** - Retrieve conference by conference key.
- **getConferencesCreated** - Retrieve conference created by authed user.
- **getConferencesToAttend** - Retrieve conferences that authed user has
registered for.
- **getFeaturedSpeaker** - Retrieve the current featured speaker from memcache.
- **getProfile** - Retrieve the profile of the current authed user.
- **getSessionWishlist** - Retrieve the session wish list for the current
authed user.
- **getSessionsByConference** - Retrieve all sessions by conference key.
- **getSessionsBySpeaker** - Retrieve all sessions by speaker key.
- **getSpeakersByConference** - Retrieve all speakers by conference key.
- **queryConferences** - Retrieve conferences based on custom filters.
- **registerForConference** - Register the authed user for a conference using
the conference key.
- **removeSessionFromWishlist** - Removes a session from the authed user's
Wishlist using the session's key.
- **saveProfile** - Saves the authed user's profile after editing.
- **unregisterFromConference** - Unregister the authed user for a conference
using the conference key.


## Contributing
In the off chance someone would like to contribute to this project, follow the
usual steps:

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D


## Credits
Base code provided by Udacity and edited by gravic07


## License
See [License](https://github.com/gravic07/Conference_Central/blob/master/LICENSE)
