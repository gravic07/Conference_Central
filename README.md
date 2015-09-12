App Engine application for the Udacity training course.

## Products
- [App Engine][1]

## Language
- [Python][2]

## APIs
- [Google Cloud Endpoints][3]

## Setup Instructions
1. Update the value of `application` in `app.yaml` to the app ID you
   have registered in the App Engine admin console and would like to use to host
   your instance of this sample.
1. Update the values at the top of `settings.py` to
   reflect the respective client IDs you have registered in the
   [Developer Console][4].
1. Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID
1. (Optional) Mark the configuration files as unchanged as follows:
   `$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js`
1. Run the app with the devserver using `dev_appserver.py DIR`, and ensure it's running by visiting your local server's address (by default [localhost:8080][5].)
1. (Optional) Generate your client library(ies) with [the endpoints tool][6].
1. Deploy your application.


[1]: https://developers.google.com/appengine
[2]: http://python.org
[3]: https://developers.google.com/appengine/docs/python/endpoints/
[4]: https://console.developers.google.com/
[5]: https://localhost:8080/
[6]: https://developers.google.com/appengine/docs/python/endpoints/endpoints_tool








###############################################################################
###############################################################################


## EndPoints
- **addSessionToWishlist** -
- **createConference** -
- **createSession** -
- **createSpeaker** -
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


###############################################################################
###############################################################################











#The Library


This application was created as my submission for project 3 of Udacity's
Full Stack Nanodegree program.  The objective of project 3 is to develop a
web application that provides a list of items within a variety of categories
 and to integrate third party user registration and authentication.  I
 decided to make an application called The Library where users can create
 collections of books to share with their friends.


##Important Files
| File | Description |
|------|-------------|
| **library.py** | This is the main Python file which uses the Flask framework to build a dynamic website. |
| **library_setup.py** | This Python file will create a PostgreSQL database at a specified location. |
| **boxOfBoxes.py** | A Python file that will populate the The Library with some test data. |
| **requirements.txt** | Lists all required dependencies for The Library. |
| **templates Folder** | Stores all HTML templates for the application. |
| **static Folder** | Stores all dependencies/resources for the HTML templates. |



## Installation
####Prerequisites:
| Prerequisite | Documentation | Download |
|---------------|---------------|----------|
| **Git** | [docs](https://git-scm.com/doc) | [download](http://git-scm.com/downloads) |
| **Virtual Box** | [docs](https://www.virtualbox.org/wiki/Documentation) | [download](https://www.virtualbox.org/wiki/Downloads)|
| **Vagrant** | [docs](https://docs.vagrantup.com/v2/) | [download](https://www.vagrantup.com/downloads)       |
| **Python 2.7** | [docs](https://docs.python.org/2.7/) | [download](https://www.python.org/downloads/) |
| **Vagrant** | [docs](https://docs.vagrantup.com/v2/) | [download](https://www.vagrantup.com/downloads) |

| Python Library | Documentation |
|----------------|---------------|
| **Flask** | [docs](http://flask.pocoo.org/docs/0.10/) |
| **SQLAlchemy** | [docs](http://docs.sqlalchemy.org/en/rel_1_0/) |
| **Requests** | [docs](http://docs.python-requests.org/en/latest/) |
| **Httplib2** | [docs](https://github.com/jcgregorio/httplib2) |
| **oauth2client.client** | [docs](https://developers.google.com/api-client-library/python/guide/aaa_oauth) |


####Installation Steps:
1. Open terminal:
  - Windows: Use the Git Bash program (installed with Git) to get a Unix-style terminal.
  - Other systems: Use your favorite terminal program.
2. Change to the desired parent directory
  - Example: `cd Desktop/`
3. Using Git, clone the VM configuration from Udacity:
  - Run: `git clone http://github.com/udacity/fullstack-nanodegree-vm fullstack`
  - This will create a new directory titled **fullstack** that contains all of the necessary configurations to run this application.
4. Move to the **vagrant** folder by executing: `cd fullstack/vagrant/`
5. Using Git, clone this project:
  - Run: `git clone https://github.com/gravic07/the_library.git the_library`
  - This will create a directory inside the *vagrant* directory titled *the_library*.
6. Run Vagrant by executing: `vagrant up`
7. SSH into Vagrant by executing: `vagrant ssh`
8. Move to the **the_library** directory by executing: `cd /vagrant/the_library/`
9. Create a local database be executing: `python library_setup.py`
  - This will create a PostgreSQL database within the **the_library** directory entitled **theArchive.db**
10. (Optional) Populate the database with some test information by executing: `python boxOfBoxes.py`
11. Deploy the app by executing: `python library.py`


## Usage
Once the installation steps are complete, you are ready to open the application.

1. Open a browser and enter the url **http://localhost:5000**.
  - If you run into issues at this point, ensure that nothing else is already using port 5000.
2. The application should now be running and fully functional


## Contributing
In the off chance someone would like to contribute to this project, follow the usual steps:

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request :D


## Credits
Created by gravic07


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
