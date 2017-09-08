# Restaurant
This application provides a list of restaurants. Also provides a user registration and authentication system. Registered users will have the ablity to add, edit and delete their own restaurants.

## Setup

* Install Vagrant
* Install VirtualBox

## Usage

To use this project -
* Clone the repo using git clone https://github.com/lubgade/restaurant

OR

* Fork the repo  
* Launch the vagrant VM using `vagrant up`
* Run `vagrant ssh` which takes the user to vagrant shell
* At the command line `cd /vagrant`
* Move to the project folder
* Run `python items.py` to populate test entries in the database
* Run `project.py` to run the application
* Access & test the application at `http://localhost:8000`

## Features

* CRUD operations - Only authenticated users can create, update & delete their own restaurants & menu items
* Provides third party (Google) authorization and authentication service


