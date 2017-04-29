from flask import Flask, render_template, url_for, request, redirect, flash, jsonify

# import CRUD operations
from database_setup import Base, Restaurant, MenuItem, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu APP"

engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()


# create anti-forgery stae token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)for x in xrange(32))
    login_session['state'] = state
    print login_session['state']
    return render_template('login.html', STATE=state)


# gconnect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # validate state token
    print request.args.get('state')
    print login_session['state']
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter!'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # obtain authorization code
    code = request.data

    try:
        # upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade authorization code'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # check that acess toke is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url,'GET')[1])

    # if there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-type'] = 'application/json'
        return response

    # verfiy that the access token is for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID does not match given usser ID"), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    # verify that the response token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match app's"), 401)
        response.headers['Content-type'] = 'application/json'
        return response


    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user is already connected"), 200)
        response.headers['Content-type'] = 'application/json'
        return response

    # store the access token info in the session for later use
    login_session['access_token'] = credentials.access_token
    print credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token':credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url,params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style="width:300px; height:300px; border-radius:150px; -webkit-border-radius:150px;-moz-border-radius:150px"'
    flash("You are now logged in as %s" % login_session['username'])
    print "Done"
    return output


# Disconnect - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # only disconnect a connected user
    print login_session.keys()

    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-type'] = 'application/json'
        return response

    url = "https://accounts.google.com/o/oauth2/revoke?token=%s" % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user', 400))
        response.headers['Content-type'] = 'application/json'
        return response


# Making an API endpoint (GET request)
@app.route('/restaurant/<int:restaurant_id>/menu/json')
def restaurantMenuJson(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id).all()

    return jsonify(MenuItem = [i.serialize for i in items] )

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/json')
def menuItemJson(restaurant_id,menu_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    item = session.query(MenuItem).filter_by(id=menu_id).one()

    return jsonify(MenuItem=item.serialize)


@app.route('/')

@app.route('/restaurant')
def restaurants():
    restaurants = session.query(Restaurant)
    return render_template('restaurants.html',restaurants=restaurants)


@app.route('/restaurant/<int:restaurant_id>/')
def restaurantMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id=restaurant_id)
    return render_template('menu.html', restaurant=restaurant, items=items)


@app.route('/restaurant/new', methods=['GET','POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newRestaurant = Restaurant(name=request.form['name'], user_id=login_session['user_id'])
        session.add(newRestaurant)
        session.commit()
        return redirect('/restaurant')
    else:
        return render_template('newrestaurant.html')


@app.route('/restaurant/<int:restaurant_id>/edit', methods=['GET','POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')

    editRestaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        editRestaurant.name = request.form['name']
        session.add(editRestaurant)
        session.commit()
        return redirect('/restaurant')
    else:
        return render_template('editrestaurant.html',restaurant=editRestaurant)


@app.route('/restaurant/<int:restaurant_id>/delete', methods=['GET','POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')

    deleteRestaurant =session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        session.delete(deleteRestaurant)
        session.commit()
        return redirect('/restaurant')
    else:
        return render_template('deleterestaurant.html', restaurant=deleteRestaurant)


# add new menu item
@app.route('/restaurant/<int:restaurant_id>/add/', methods=['GET','POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect('/login')

    restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], description=request.form['description'],
                           price=request.form['price'], course=request.form['course'], restaurant_id=restaurant.id,
                           user_id=restaurant.user_id)

        session.add(newItem)
        session.commit()
        flash("New menu item created!!!")
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('newmenuitem.html', restaurant_id=restaurant_id)

# edit menu Item
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit/', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')

    itemToEdit = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']
        if request.form['price']:
            itemToEdit.price = request.form['price']
        if request.form['course']:
            itemToEdit.course = request.form['course']
            session.add(itemToEdit)
            session.commit()
            return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id=restaurant_id, menu_id=menu_id, item=itemToEdit)

# delete menu item
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete/', methods=['GET','POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect('/login')

    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('restaurantMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deletemenuitem.html', restaurant_id=restaurant_id, item=itemToDelete)


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
