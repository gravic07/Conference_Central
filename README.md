# Conference Central

This application was created as my submission for project 4 of Udacity's
Full Stack Nanodegree program.  The objective of project 4 is develop a
EndPoints using Google's App Engine.  All of the work done was focused on the
back end and creating the API.


## Design Decisions
##### Sessions
Sessions are the individual events that make up a conference.  Sessions can
have several formats.  Workshop, Lecture, Keynote, Demo and Panel have been
provided as options for the **SessionType**.  Since you can not have a
session without a conference, sessions require a conference key to be passed
under **parentConfKey**.  This conference key is used to establish an ancestor
relationship between the conference and the session. In addition to
**parentConfKey**, the **name** property is also a required field.  To prevent
unwanted sessions being created, only the creator of a conference can add
sessions to it.

##### Speakers
In their current capacity, speakers are associated with most sessions as the
main attraction.  Since a speaker can attend more than one session, or even
more than one conference, speakers are there own entity with the following
properties: **name**, **briefBio**, **company** and **projects**.  **name**
is the only required property for a speaker.  A speaker has no ancestor
relationship since a speaker can attend multiple conferences and sessions.

##### Session & Speaker Relationship
A speaker is added to a session using the speaker's key, through the session's
**speakerKey**.  A session's **speakerKey** property allows for more than one
speaker since sessions can have multiple speakers or a panel.  Each key is
passed is verified individually and an exception is thrown if one is invalid.

##### Featured Speakers
A featured speaker is defined as a speaker that is assigned to two or more
sessions within a conference.  When a session is created within
`_createSessionObject()`, a check is performed on each **speakerKey** that is
passed in.  For each speakerKey, the number of sessions for the speaker is
calculated.  The speaker with the most sessions is then set as the featured
speaker and added to the task queue through `_cacheFeaturedSpeaker()`.  If
there is a tie for number of sessions, the last speaker passed is assigned
the featured speaker.

##### User Wish Lists
A User can add sessions to their wish list using `addSessionToWishlist()` and
passing in the session key.  A user must be registered to the parent
conference of a session to add it to their wish list.  The session's key is
added to the user's profile under the **sessionWishList** property.  A user
can also remove a session from their wish list using
`removeSessionFromWishlist()`.  Additionally you can retrieve all sessions in
a user's wish list by calling getSessionWishlist() while a user is authed.

##### Additional Queries
- `getSpeakersByConference()` takes in a conference key and returns all
speakers in that conference, regardless of session.  This can be used to
quickly see the speaker lineup for an entire conference.
- `getConferenceSessionsByDate()` takes in a conference key and date to return
all sessions for the parent conference matching the specified date.  This
would allow a participant to decided what days might be more valuable to them
based on the sessions that are available.

##### Problem








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
  - Windows: Use the Git Bash program (installed with Git) to get a Unix-style terminal.
  - Other systems: Use your favorite terminal program.
2. Change to the desired parent directory
  - Example: `cd Desktop/`
3. Using Git, clone this project:
  - Run: `git clone https://github.com/gravic07/Conference_Central.git Conference_Central`
  - This will create a directory inside of your parent directory titled *Conference_Central*.
4. Download the Google App Engine SDK *for Python* using the link listed under **Prerequisites**.
5. Once the SDK is installed, open GoogleAppEngineLauncher.
6. Under File, select *Add Existing Application...*.
7. Select *Browse* and navigate to the newly created Conference_Central Folder.
8. (Optional) Adjust the *Admin Port* and *Port* if desired and make note of both.
9. With the newly added application highlighted, press *Run*.
10. The APIs explorer should now be available at http://localhost:8080/_ah/api/explorer
  - The url above assumes the default port.  If *Port* was altered in step 8, replace *8080* with the new port provided.
11. Select *conference API* to access all EndPoints.


## EndPoints
- **addSessionToWishlist** - Adds an existing Session to a user's Wishlist using the Session's key.
- **createConference** - Creates a Conference; *name* property is required.
- **createSession** - Creates a Session; *name* and *parentConfKey* properties are required.
- **createSpeaker** - Creates a Speaker; *name* property is required.
- **getAnnouncement** -
- **getConfSessionsByDate** -
- **getConfSessionsByType** -
- **getConference** -
- **getConferencesCreated** -
- **getConferencesToAttend** -
- **getFeaturedSpeaker** -
- **getProfile** -
- **getSessionWishlist** -
- **getSessionsByConference** -
- **getSessionsBySpeaker** -
- **getSpeakersByConference** -
- **queryConferences** -
- **registerForConference** -
- **removeSessionFromWishlist** -
- **saveProfile** -
- **unregisterFromConference** -


## Contributing
In the off chance someone would like to contribute to this project, follow the usual steps:

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D


## Credits
Base code provided by Udacity and edited by gravic07


## License
Licensed under the MIT License (MIT)
```
Copyright (c) [2015] [gravicDesign]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
