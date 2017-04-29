from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi

# import CRUD operations
from database_setup import Base, Restaurant, MenuItem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()



class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.endswith('/restaurant/new'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<body><html>"
                output += "<form method='POST' enctype='multipart/form-data' action='/restaurant/new'>"
                output += "<input name='newRestaurantName' type='text' placeholder='New Restaurant Name'>"
                output += "<input type='submit' value='Create'>"
                output += "</form></body></html>"
                self.wfile.write(output)
                return

            if self.path.endswith('/edit'):
                restaurantIDPath = self.path.split("/")[2]
                query = session.query(Restaurant).filter_by(id=restaurantIDPath).one()

                if query != []:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = "<body><html>"
                    output += "<h1>"
                    output += query.name
                    output += "</h1>"
                    output += "<form method='POST' enctype='multipart/form-data' action='/restaurant/%s/edit'>" % restaurantIDPath
                    output += "<input name='newRestaurantName' type='text' placeholder='%s'>" % query.name
                    output += "<input type='submit' value='Rename'>"
                    output += "</form></body></html>"
                    self.wfile.write(output)
                    return

            if self.path.endswith('/delete'):
                restaurantIDPath = self.path.split("/")[2]
                query = session.query(Restaurant).filter_by(id=restaurantIDPath).one()

                if query != []:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    output = "<body><html>"
                    output += "<h1>Are you sure you want to delete %s</h1>" % query.name
                    output += "<form method='POST' enctype='multipart/form-data' action='/restaurant/%s/delete'>" % restaurantIDPath
                    output += "<input type='submit' value='Delete'>"
                    output += "</form></body></html>"
                    self.wfile.write(output)
                    return



            if self.path.endswith('/restaurant'):
                restaurants = session.query(Restaurant).all()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                output = ""
                output += "<body><html>"
                for r in restaurants:
                    output += r.name
                    output += "</br>"
                    output += "<a href='/restaurant/%s/edit'>edit</a>" % r.id
                    output += "</br>"
                    output += "<a href='/restaurant/%s/delete'>Delete</a>" % r.id
                    output += "</br></br>"

                output += "<a href='/restaurant/new'>Add a new restaurant</a></br></br>"
                output += "</body></html>"
                self.wfile.write(output)


            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<h1>Hello!</h1>"
                output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>what would you like me to say</h2><input name="message" type="text"><input type="submit" value="Submit"></form>'''
                output += "</body></html>"
                self.wfile.write(output)
                #print output
                return
            if self.path.endswith("/hola"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<h1>&#161Hola </h1>"
                output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>what would you like me to say</h2><input name="message" type="text"><input type="submit" value="Submit"></form>'''
                output += "</body></html>"
                self.wfile.write(output)
                #print output
                return

        except IOError:
            self.send_error(400, "File not found %s" % self.path)

    def do_POST(self):
        try:
            if self.path.endswith('/restaurant/new'):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')

                    # Create a new restaurant object
                    newRestaurant = Restaurant(name=messagecontent[0])
                    session.add(newRestaurant)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Content-type', 'text/html')
                    self.send_header('Location', '/restaurant')
                    self.end_headers()

                    return

            if self.path.endswith('/edit'):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    messagecontent = fields.get('newRestaurantName')

                    restaurantIDPath = self.path.split("/")[2]
                    query = session.query(Restaurant).filter_by(id=restaurantIDPath).one()
                    if query != []:
                        query.name=messagecontent[0]
                        session.add(query)
                        session.commit()

                        self.send_response(301)
                        self.send_header('Conyent-type', 'text/html')
                        self.send_header('Location', '/restaurant')
                        self.end_headers()
                        return

            if self.path.endswith('/delete'):
                restaurantIDPath = self.path.split("/")[2]
                query = session.query(Restaurant).filter_by(id=restaurantIDPath).one()
                if query != []:
                    session.delete(query)
                    session.commit()

                    self.send_response(301)
                    self.send_header('Conyent-type', 'text/html')
                    self.send_header('Location', '/restaurant')
                    self.end_headers()
                    return








                    # self.send_response(301)
            # self.send_header('Content-type', 'text/html')
            # self.end_headers()
            #
            # ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            # if ctype == 'multipart/form-data':
            #     fields = cgi.parse_multipart(self.rfile,pdict)
            #     messagecontent = fields.get('message')
            #
            #     output = ""
            #     output += "<html><body>"
            #     output += "<h2>Okay, how about this:</h2>"
            #     output += "<h1>%s</h1>" % messagecontent[0]
            #     output += '''<form method='POST' enctype='multipart/form-data' action='/hello'><h2>what would you like me to say</h2><input name="message" type="text"><input type="submit" value="Submit"></form>'''
            #     output += "</body></html>"
            #     self.wfile.write(output)
            #     print output
            #     return

        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print "Server running at port %s" % port
        server.serve_forever()

    except KeyboardInterrupt:
        print "^C entered, stopping web server...."
        server.socket.close()


if __name__ == '__main__':
    main()