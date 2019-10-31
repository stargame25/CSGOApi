# CSGOApi
Website, wrapper for steam-csgo library, used to represent scraped data. Project provides capability to use app as performance indicator,
to keep you more competitive. App can be used in personal or public purpose, app supports multi-user usage. 
## Warning!
Never use trustless online versions
## Installation
### For end-user
Download any release, choose way to start: console (starts a Flask server with website avalible at localhost) or standalone package
(not avalible at the moment)
### For communities
To host application, download any release, choose way to start: console or download binary and deploy on vps
## Configuration
Project provides deep configuration. By default configs generated with LAN based settings. 
For additional information check documentation (TODO)
## Usage
Start with signing in. To sign in use your Steam login data,
to be sure it's secure way to login in, password encrypting in your browser before sending.
## Functionality
Functionality based on a few things: 
- Website own API key - if website decide to provide you an API key, you can use all functions like unlimited user, even if you are
- On functionality of your Steam account:
  - Limited (account spend $5 in total) - will not have access to: cheater statistic
  - Unlimited - will have full access
- As additional tool you can provide others API key, as it's not provide access to account manipulations and safe to use for other users
