import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# XXX: The URI should be in the format of: 
#
#     postgresql://zy2232:4ayq7@104.196.175.120/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
DATABASEURI = "postgresql://zy2232:4ayq7@104.196.175.120/postgres"
# This line creates a database engine that knows how to connect to the URI above
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None
    
@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass
  
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
@app.route('/')
def index():
  return render_template("index.html")


#sign in
@app.route('/signin',methods=['POST'])
def sign():
  username = request.form['username']
  password = request.form['password']
  t=request.form['name']
  record=g.conn.execute('SELECT username FROM person WHERE username = %s',username)
  print record
  if not record.fetchone():
    return render_template("signinerror.html")
    record.close()
  else:
    record=g.conn.execute('SELECT password FROM person WHERE username = %s',username)
    print record
    p= record.fetchone()
    record.close()
    if p[0] == password:
      if t =='employer':
        cur=g.conn.execute("select e.* from employer as e, person as p  where e.user_id=p.user_id and p.username='%s';",username)
        print cur
        a=cur.first()
        if a==None:
          return render_template("signinerror.html")
        else:                  
          return redirect('/employer/%s', username)
      else:
        cur=g.conn.execute("select j.* from jobseeker as j, person as p  where j.user_id=p.user_id and p.username='%s';",username)
        print cur
        a=cur.first()
        if a==None:
          return render_template("signinerror.html")
        else:
          return redirect('/jobseeker/%s', username)  
    else: 
      return render_template("signinerror.html")


#sign in error
@app.route('/signinerror')
def signinerror():
  return render_template("signinerror.html")

#sign up
@app.route('/signup')
def signup():
  return render_template("signup.html")


#add user
@app.route('/signup/add',methods=['POST'])
def add():
  username = request.form['username']
  firstname = request.form['first_name']
  lastname = request.form['last_name']
  email = request.form['email']
  password = request.form['password']
  usertype = request.form['usertype']
  name=request.form['name']
  start=username[0]
  #username exists
  cursor = g.conn.execute("SELECT username FROM person")
  allnames = []
  for result in cursor:
    allnames.append(result[0])  # can also be accessed using result[0]
  cursor.close()
  #username exists end
  #
  #email exists
  cursor1 = g.conn.execute("SELECT email FROM person")
  allemails = []
  for result in cursor1: 
    allemails.append(result[0])  # can also be accessed using result[0]
  cursor1.close()
  #email exists end
  if username in allnames or email in allemails:
    return render_template("signuperror.html")
  else:
    #Check username valid
    if type(start)!=str or '@' not in email:
      return render_template("signupinvalid.html")
    else:        
      #new user_id
      record1 = g.conn.execute("select max(user_id)+1 from person")
      record=record1.fetchone()
      uid=record[0]
      record1.close()
      #new user_id end
      cmd = 'INSERT INTO person VALUES (:username1, :uid1, :firstname1, :lastname1, :email1, :password1)';
      g.conn.execute(text(cmd), username1=username,uid1=uid, firstname1=firstname,lastname1=lastname,email1=email, password1=password);
      if usertpye=='jobseeker':
        recordj = g.conn.execute("select max(jobseeker_id)+1 from jobseeker")
        jid=recordj.first()[0]
        g.conn.execute("insert into jobseeker values (:uid1, :jid1)", uid1=uid, jid1=jid)
      else:
        recorde = g.conn.execute("select max(employer_id)+1 from employer")
        eid=recorde.first()[0]
        g.conn.execute("insert into employer values (:uid1, :eid1,:name1)", uid1=uid, eid1=eid, name1=name)
      return render_template("sus.html")


#employer
@app.route('/employer/<username>')
def profile_e(username): pass
  

#jobseeker
@app.route('/jobseeker/<username>')
def profile_j(username): 
  cursor=g.conn.execute("select user_id from person where username='%s';",username)
  uid=cursor.first()[0]
  cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
  profile=cur.first()
  if profile==None:
    update_time=None
    birthday=None
    self_introduction=None
    field=None
  else:
    update_time=profile[1]
    birthday=profile[2]
    self_introduction=profile[4]
    field=profile[5]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  print friends
  if friends==None:
    update_time_f=None
    friendlist=None
  else:
    update_time_f=friends[1]
    friendlist=friends[2].split(',')
  return render_template("jobseeker.html",**locals())

#friendlist
@app.route('/friendlist/<username>')
def list(username):
  cursor=g.conn.execute("select user_id from person where username='%s';",username)
  uid=cursor.first()[0]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  print friends
  if friends==None:
    update_time_f=None
    friendlist=None
  else:
    update_time_f=friends[1]
    friendlist=friends[2]
    return render_template("friendlist.html",**locals())
  
#view profile
@app.route('/viewprofile',methods=['POST'])
def viewp():
  username = request.form['proname']
  cursor=g.conn.execute("select user_id from person where username='%s';",username)
  uid=cursor.first()[0]
  cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
  profile=cur.first()
  if profile==None:
    update_time=None
    birthday=None
    self_introduction=None
    field=None
  else:
    update_time=profile[1]
    birthday=profile[2]
    self_introduction=profile[4]
    field=profile[5]
  return render_template("viewprofile.html",**locals())
  

#add friend
@app.route('/friendlist/<username>/add',methods=['POST'])
def add_f(username):
  newname = request.form['addname']
  cursor = g.conn.execute("SELECT username FROM person")
  allnames = []
  for result in cursor:
    allnames.append(result[0])  # can also be accessed using result[0]
  cursor.close()
  if newname not in allnames:
    return render_template('frienderror.html')
  else:
    cursor=g.conn.execute("select user_id from person where username='%s';",username)
    uid=cursor.first()[0]
    cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
    friends=cursor.first()  
    friendlist=friends[2]
    a=friendlist.split(',')
    a.append(newname)
    content = ",".join(a)
    time=g.conn.execute("select current_date;")
    updatetime=time.first()[0]
    g.conn.execute("update friendlist set update_time=timestamp'%s',username='%s' where user_id=%s;"%(updatetime,content,uid))
    return render_template('friendsus.html')

#delete friend
@app.route('/friendlist/<username>/delete',methods=['POST'])
def delete_f(username):
  oldname = request.form['delname']
  cursor=g.conn.execute("select user_id from person where username='%s';",username)
  uid=cursor.first()[0]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  friendlist=friends[2]
  a=friendlist.split(',')
  if oldname not in a:
    return render_template('frienderror.html')
  else:
    a.remove(old)
    content = ",".join(a)
    time=g.conn.execute("select current_date;")
    updatetime=time.first()[0]
    g.conn.execute("update friendlist set update_time=timestamp'%s',username='%s' where user_id=%s;"%(updatetime,content,uid))
    return render_template('friendsus.html')
           
#update employer profile
@app.route('/employer/<username>/update')
def update_e(username):
  cursor=g.conn.execute("select user_id from person where username='%s';",username)
  uid=cursor.first()[0]
  cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
  profile=cur.first()
  if profile==None:
    update_time=None
    birthday=None
    self_introduction=None
    field=None
  else:
    update_time=profile[1]
    birthday=profile[2]
    self_introduction=profile[4]
    field=profile[5]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  print friends
  if friends==None:
    update_time_f=None
    friendlist=None
  else:
    update_time_f=friends[1]
    friendlist=friends[2].split(',')
  return render_template("employer.html",**locals())

           
#update jobseeker profile
@app.route('/jobseeker/<username>/update')
def update_j(username):pass 
           
           
#jobs of an employer
@app.route('/employer/<username>/job')
def job_posted(username):pass
           
       
#post new job
@app.route('/employer/<username>/postjob')
def add_j(username):pass
           
  
#delete job
@app.route('/employer/<username>/deletejob')
def delete_j(username):pass


#all jobs for employer
@app.route('/job')
def job():pass
           

#resume
@app.route('/jobseeker/<username>/resume')
def resume(username):pass
           

#update resume
@app.route('/jobseeker/<username>/resume/update')
def resume_update(username):pass
          
           
#search job
@app.route('/jobseeker/<username>/search')
def search_j(username):pass
           
           
#apply job
@app.route('/jobseeker/<username>/applyjob')
def apply_job(username):pass
           
           
#view job apply and interview for jobseeker
@app.route('/jobseeker/<username>/status')
def apply(username):pass
           

#search resume
@app.route('/employer/<username>/searchresume')
def search_r(username):pass
           

#resume followed
@app.route('/employer/<username>/resume')
def resume_followed(username):pass

          
#follow resume
@app.route('/employer/<username>/follow')
def follow(username):pass

           
#view application and interview for employer
@app.route('/employer/<username>/application')
def application(username):pass
           
           
#edit status of application
@app.route('/editstatus')
def edit():pass

           
           
           
           
           
           
           
           
           
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
