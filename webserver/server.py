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
        cur=g.conn.execute("select e.* from employer as e, person as p  where e.user_id=p.user_id and p.username=%s;",username)
        print cur
        a=cur.first()
        if a==None:
          return render_template("signinerror.html")
        else:                  
          return redirect('/employer/%s', username)
      else:
        cur=g.conn.execute("select j.* from jobseeker as j, person as p  where j.user_id=p.user_id and p.username=%s;",username)
        print cur
        a=cur.first()
        if a==None:
          return render_template("signinerror.html")
        else:
          return redirect('/jobseeker/%s', username)  
    else: 
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
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
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
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
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
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
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
    return render_template('frienderror.html',name=username,username=newname)
  else:
    cursor=g.conn.execute("select user_id from person where username=%s;",username)
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
    return render_template('friendsus.html',name=username)

#delete friend
@app.route('/friendlist/<username>/delete',methods=['POST'])
def delete_f(username):
  oldname = request.form['delname']
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
  uid=cursor.first()[0]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  friendlist=friends[2]
  a=friendlist.split(',')
  if oldname not in a:
    return render_template('frienderror.html',name=username,username=oldname)
  else:
    a.remove(old)
    content = ",".join(a)
    time=g.conn.execute("select current_date;")
    updatetime=time.first()[0]
    g.conn.execute("update friendlist set update_time=timestamp'%s',username='%s' where user_id=%s;"%(updatetime,content,uid))
    return render_template('friendsus.html',name=username)
           
#update  profile
@app.route('/profileupdate/<username>')
def profile_update(username):
  
  ~~~~
  return render_template('update_profile.html',**locals())


           
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
def resume(username):
  cursor=g.conn.execute("select j.jobseeker_id from jobseeker as j, person as p where j.user_id=p.user_id and p.username=%s",username)
  jid=cursor.first()[0]
  cursor1=g.conn.execute("select * from resume_updated where jobseeker_id=%s;",jid)
  resume=cursor1.first()
  if resume==None:
    rid=None
    education=None
    skills=None
    volunteer=None
    honor=None
    work_experience=None
    certificate=None
    address=None
    email=None
    number=None
  else: 
    rid=resume[0]
    education=resume[2]
    skills=resume[3]
    volunteer=resume[4]
    honor=resume[5]
    work_experience=resume[6]
    certificate=resume[7]
    address=resume[8]
    email=resume[9]
    number=resume[10]
  return render_template('resume.html',**locals())
  
  
           

#update resume
@app.route('/jobseeker/<username>/resume/update',methods=['POST'])
def resume_update(username):
  cursor=g.conn.execute("select j.jobseeker_id from jobseeker as j, person as p where j.user_id=p.user_id and p.username=%s",username)
  jid=cursor.first()[0]
  education=request.form['education']
  skills=request.form['skills']
  volunteer=request.form['volunteer']
  honor=request.form['honor']
  work_experience=request.form['work_experience']
  certificate=request.form['certificate']
  address=request.form['address']
  email=request.form['email']
  number=request.form['phonenumber']
  if education!=None:
    g.conn.execute("update resume_updated set education=%s where jobseeker_id=%s;",(education,jid))
  if skills!=None:
    g.conn.execute("update resume_updated set skills=%s where jobseeker_id=%s;"%(skills,jid))
  if volunteer!=None:
    g.conn.execute("update resume_updated set volunteer=%s where jobseeker_id=%s;",(volunteer,jid))
  if honor!=None:
    g.conn.execute("update resume_updated set honor=%s where jobseeker_id=%s;",(honor,jid))
  if work_experience!=None:
    g.conn.execute("update resume_updated set work_experience=%s where jobseeker_id=%s;",(work_experience,jid))
  if certificate!=None:
    g.conn.execute("update resume_updated set certificate=%s where jobseeker_id=%s;",(certificate,jid))
  if address!=None:
    g.conn.execute("update resume_updated set address=%s where jobseeker_id=%s;",(address,jid))
  if email!=None:
    if '@' not in email:
      return render_template('update_resume_error.html',username=username)
    else:
      g.conn.execute("update resume_updated set email=%s where jobseeker_id=%s;",(email,jid))
  if number!=None:
    if number[3]!='-' or number[7]!='-':
      return render_template('update_resume_error.html',username=username)
    else:
      g.conn.execute("update resume_updated set phone_number=%s where jobseeker_id=%s;",(number,jid))
  return render_template('update_resume_sus.html')

           
#search job
@app.route('/jobseeker/<username>/search',methods=['POST'])
def search_j(username):
  cursor=g.conn.execute("select j.jobseeker_id from jobseeker as j, person as p where j.user_id=p.user_id and p.username=%s",username)
  jid=cursor.first()[0]
  catagory=request.form['type']
  employer=request.form['employer']
  title=request.form['title']
  location=request.form['location']
  salary=request.form['salary']
  where=[]
  m=[]
  c=' catagory=%s'
  where.append(c)
  m.append(catagory)
  if employer!=None:
    e=' employer like %s'
    where.append(e)
    emp='%'+employer+'%'
    m.append(emp)
  if title!=None:
    t=' title like %s'
    where.append(t)
    tit='%'+title+'%'
    m.append(tit)
  if location!=None:
    l=' location like %s'
    where.append(l)
    loc='%'+location+'%'
    m.append(loc)
  if salary!=None:
    s=' salary>%s'
    where.append(s)
    m.append(salary)
  w=where[0]
  i=1
  while i<len(where):
    w=w+' and'+where[i]
    i+=1
  c='select * from job_posted where'
  cmd=c+w+';'
  cur=g.conn.execute(cmd,m)
  jobs=cur.fetchall()
  cur.close()
  e_name=[]
  data=[]
  alljid=[]
  for n in jobs:
    b=n[:]
    alljid.append(b[2])
    cur=conn.execute("select name from employer where employer_id=%s;",b[0])
    name=cur.first()[0]
    b1=[]
    b1.append(name)
    for i in range(1,len(b)):
        b1.append(b[i])
    data.append(b1)
  return render_template('jobsearch.html',**locals())
    
  
#apply job
@app.route('/jobseeker/<username>/applyjob',methods=['POST'])
def apply_job(username):pass
           
  
  
  
  
  
  
  
  
           
#view job apply and interview for jobseeker
@app.route('/jobseeker/<username>/status')
def apply(username):
  cur=g.conn.execute("select a.* from jobseeker as j, person as p, applyjob as a where a.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id and p.username=%s;",username)
  s=cur.fetchall()
  cur.close()
  info=[]
  for m in s:
    cursor=g.conn.execute("select e.name,j.title from job_posted as j,employer as e where j.job_id=%s and e.employer_id=%s;",(m[1],m[3]))
    n=cursor.first()
    info.append(n)
    cursor.close()
  time=[]
  for m in s:
    if m[2]=='interview':
        cursor=conn.execute("select time from interview where job_id=%s and employer_id=%s and jobseeker_id=%s;",(m[1],m[3],m[0]))
        t=cursor.first()[0]
        time.append(t)   
  applications=[]
  interviews=[]
  for i in range(0,len(m1)) :
    a=m1[i][1]
    b=info[i][0]
    c=info[i][1]
    d=m1[i][2]
    e=time[i]
    applications.append([a,b,c,d])
    interviews.append([a,b,c,e])
  return render_template('application_j.html',**locals())

  
  

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
