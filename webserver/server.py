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
  if not record.fetchone():
    return render_template("signinerror.html")
    record.close()
  else:
    record=g.conn.execute('SELECT password FROM person WHERE username = %s',username)
    p= record.fetchone()
    record.close()
    if p[0] == password:
      if t =='employer':
        cur=g.conn.execute("select e.* from employer as e, person as p  where e.user_id=p.user_id and p.username=%s;",username)
        a=cur.first()
        if a==None:
          return render_template("signinerror.html")
        else:                  
          return redirect('/employer/%s'%username)
      else:
        cur=g.conn.execute("select j.* from jobseeker as j, person as p  where j.user_id=p.user_id and p.username=%s;",username)
        a=cur.first()
        if a==None:
          return render_template("signinerror.html")
        else:
          return redirect('/jobseeker/%s'%username)  
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
  if username=='' or firstname=='' or lastname=='' or email=='' or password=='':
    return render_template("signupinvalid.html")
  start=str(username[0])
  #username exists
  cursor = g.conn.execute("SELECT username FROM person;")
  allnames = []
  for result in cursor:
    allnames.append(result[0])  # can also be accessed using result[0]
  cursor.close()
  #username exists end
  #
  #email exists
  cursor1 = g.conn.execute("SELECT email FROM person;")
  allemails = []
  for result in cursor1: 
    allemails.append(result[0])  # can also be accessed using result[0]
  cursor1.close()
  #email exists end
  
  if username in allnames or email in allemails:
    return render_template("signuperror.html")
  else:
    #Check username valid
    if str.isdigit(start) or email.count('@')!=1 or len(username)<6 or len(password)<8:
      return render_template("signupinvalid.html")
    else:        
      #new user_id
      record = g.conn.execute("select max(user_id)+1 from person")
      uid=record.first()[0]
      #new user_id end
      cmd = 'INSERT INTO person VALUES (:username1, :uid1, :firstname1, :lastname1, :email1, :password1)';
      g.conn.execute(text(cmd), username1=username,uid1=uid, firstname1=firstname,lastname1=lastname,email1=email, password1=password);
      if usertype=='jobseeker':
        recordj = g.conn.execute("select max(jobseeker_id)+1 from jobseeker")
        jid=recordj.first()[0]
        g.conn.execute("insert into jobseeker values (%s, %s);",(uid,jid))
      else:
        recorde = g.conn.execute("select max(employer_id)+1 from employer")
        eid=recorde.first()[0]
        g.conn.execute("insert into employer values (%s, %s,%s)",(uid,eid,username))
      return render_template("sus.html")


#employer
@app.route('/employer/<username>')
def profile_e(username): 
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
  uid=cursor.first()[0]
  cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
  profile=cur.first()
  if profile==None:
    update_time=''
    birthday=''
    self_introduction=''
    field=''
  else:
    update_time=profile[1]
    birthday=profile[2]
    self_introduction=profile[4]
    field=profile[5]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  if friends==None:
    update_time_f=''
    friendlist=''
  else:
    update_time_f=friends[1]
    friendlist=friends[2].split(',')
  return render_template("employer.html",**locals())
 
#jobseeker
@app.route('/jobseeker/<username>')
def profile_j(username): 
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
  uid=cursor.first()[0]
  cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
  profile=cur.first()
  if profile==None:
    update_time=''
    birthday=''
    self_introduction=''
    field=''
  else:
    update_time=profile[1]
    birthday=profile[2]
    self_introduction=profile[4]
    field=profile[5]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  if friends==None:
    update_time_f=''
    friendlist=''
  else:
    update_time_f=friends[1]
    friendlist=friends[2].split(',')
  return render_template("jobseeker.html",**locals())

#view profile to update
@app.route('/view_to_update/<username>')
def view_to_update(username):
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
  uid=cursor.first()[0]
  cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
  profile=cur.first()
  if profile==None:
    update_time=''
    birthday=''
    self_introduction=''
    field=''
  else:
    update_time=profile[1]
    birthday=profile[2]
    self_introduction=profile[4]
    field=profile[5]
  return render_template('update_profile.html',**locals())

#update  profile
@app.route('/profileupdate/<username>',methods=['POST'])
def profileupdate(username):
    cursor=g.conn.execute("select user_id from person where username=%s;",username)
    uid=cursor.first()[0]
    birthday=str(request.form['birthday'])
    field=request.form['Field']
    selfintro=request.form['Self introduction']
    time=g.conn.execute("select current_date;")
    updatetime=time.first()[0]
    #check birthday valid
    if birthday!='':
      cursor=g.conn.execute("select %s like '19__-__-__';",birthday)
      birthvalid=cursor.first()[0]
      if not birthvalid:
        return render_template("profileinvalid.html",username=username)
      else:
        t=birthday.split('-')
        if not str.isdigit(t[0]) or not str.isdigit(t[1]) or not str.isdigit(t[2]):
          return render_template("profileinvalid.html",username=username)
        else:
          if int(t[1])>12 or int(t[1])<1 or int(t[2])<1:
            return render_template("profileinvalid.html",username=username)
          else:
            if int(t[1]) in (1,3,5,7,8,10,12) and int(t[2])>31:
              return render_template("profileinvalid.html",username=username)
            elif int(t[1]) in (4,6,9,11) and int(t[2])>30:
              return render_template("profileinvalid.html",username=username)
            elif int(t[1])==2 and int(t[2])>28:
              return render_template("profileinvalid.html",username=username)
            else:
              cur=g.conn.execute("select age(timestamp %s);",birthday)
              a1=cur.first()[0]
              cur=g.conn.execute("select extract(day from %s);",a1)
              if cur.first()[0]<0:
                return render_template("profileinvalid.html",username=username)
    cur=g.conn.execute("select * from profile_update where user_id=%s;",uid)
    profile=cur.first()
    if profile!=None:
      g.conn.execute("update Profile_update set update_time=timestamp %s where user_id=%s;",(updatetime,uid))
      if birthday!='':
        g.conn.execute("update Profile_update set birthday=timestamp %s where user_id=%s;",(birthday,uid))
      if field!='':
        g.conn.execute("update Profile_update set field=%s where user_id=%s;",(field,uid))
      if selfintro!='':
        g.conn.execute("update Profile_update set self_introduction=%s where user_id=%s;",(selfintro,uid))
    else:
      g.conn.execute("insert into Profile_update values (%s,timestamp %s,timestamp %s,'url',%s,%s);",(uid,updatetime,birthday,selfintro,field))
    return render_template("profilesus.html",username=username)

#friendlist
@app.route('/friendlist/<username>')
def list(username):
  cursor=g.conn.execute("select user_id from person where username=%s;",username)
  uid=cursor.first()[0]
  cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
  friends=cursor.first()
  if friends==None:
    update_time=''
    friendlist=''
    a=['Please update']
  else:
    update_time=friends[1]
    friendlist=friends[2]
    a=friendlist.split(',')
  return render_template("friendlist.html",**locals())
  
### for test  
@app.route('/test')
def test():
    update_time=''
    friendlist=''
    a=['Please update']
    username='NBCU'
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
    update_time=''
    birthday=''
    self_introduction=''
    field=''
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
    time=g.conn.execute("select current_date;")
    updatetime=time.first()[0]
    cursor=g.conn.execute("select user_id from person where username=%s;",username)
    uid=cursor.first()[0]
    cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
    friends=cursor.first()
    if friends!=None:
      friendlist=friends[2]
      a=friendlist.split(',')
      if newname in a:
        return render_template('frienderror1.html',name=username,username=newname)
      cursor=g.conn.execute("select user_id from person where username=%s;",username)
      uid=cursor.first()[0]
      cursor=g.conn.execute("select * from friendlist where user_id=%s;",uid)
      friends=cursor.first()  
      friendlist=friends[2]
      a=friendlist.split(',')
      a.append(newname)
      content = ",".join(a)
      g.conn.execute("update friendlist set update_time=timestamp %s,username= %s where user_id=%s;",(updatetime,content,uid))
    else:
      g.conn.execute("insert into friendlist values (%s,timestamp %s, %s);",(uid, updatetime, newname))
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
  a.remove(oldname)
  content = ",".join(a)
  time=g.conn.execute("select current_date;")
  updatetime=time.first()[0]
  g.conn.execute("update friendlist set update_time=timestamp %s,username=%s where user_id=%s;",(updatetime,content,uid))
  return render_template('friendsus.html',name=username)

  
#jobs of an employer
@app.route('/employer/<username>/job')
def job_posted(username):
  cursor=g.conn.execute("select e.employer_id from person as p, employer as e where p.user_id=e.user_id and p.username=%s;",username)
  eid=cursor.first()[0]
  cursor=g.conn.execute("select * from job_posted  where employer_id=%s;",eid)
  s=cursor.fetchall()
  cursor.close()
  if s==None:
    jobs =''
    jidlist=''
  else:
    jobs = []
    jidlist=[]
    for result in s:
      b=result[:]
      jidlist.append(b[2])
      b1=[]
      for i in range(1,len(b)):
        b1.append(b[i])
      jobs.append(b1)
  return render_template("employer_job.html",**locals())
           
       
#post new job
@app.route('/employer/<username>/postjob',methods=['POST'])
def add_j(username):
  cursor=g.conn.execute("select e.employer_id from person as p, employer as e where p.user_id=e.user_id and p.username=%s;",username)
  eid=cursor.first()[0]
  catagory=request.form['type']
  title=request.form['title']
  location=request.form['location']
  description=request.form['description']
  salary1=str(request.form['salary'])
  if not str.isdigit(salary1):
    return render_template('jobpost_invalid.html',username=username)
  else:
    salary=int(salary1)
    if salary<1000:
      return render_template('jobpost_invalid.html',username=username)
  #new job_id
  record1 = g.conn.execute("select max(job_id) from job_posted where employer_id=%s;",eid)
  jid0=record1.first()[0]
  if jid0==None:
    jid=100*eid+1
  else: 
    jid=jid0+1
  time=g.conn.execute("select current_date;")
  updatetime=time.first()[0]
  cmd = 'INSERT INTO job_posted VALUES (%s, timestamp %s, %s, %s, %s, %s, %s ,%s);'
  g.conn.execute(cmd,(eid, updatetime, jid, title, location, salary, catagory, description))
  return render_template('jobpost_sus.html',username=username)

           
#delete job
@app.route('/employer/<username>/deletejob',methods=['POST'])
def delete_j(username):
  cursor=g.conn.execute("select e.employer_id from person as p, employer as e where p.user_id=e.user_id and p.username=%s;",username)
  eid=cursor.first()[0]
  deljid= request.form['deljid']
  g.conn.execute("delete from job_posted where employer_id=%s and job_id=%s;",(eid,deljid))
  return render_template('jobpost_sus.html',username=username)

#resume
@app.route('/jobseeker/<username>/resume')
def resume(username):
  cursor=g.conn.execute("select j.jobseeker_id from jobseeker as j, person as p where j.user_id=p.user_id and p.username=%s",username)
  jid=cursor.first()[0]
  cursor1=g.conn.execute("select * from resume_updated where jobseeker_id=%s;",jid)
  resume=cursor1.first()
  if resume==None:
    rid=''
    education=''
    skills=''
    volunteer=''
    honor=''
    work_experience=''
    certificate=''
    address=''
    email=''
    number=''
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
  number=str(request.form['phonenumber'])
  ##check valid
  if email!='':
    if email.count('@')!=1 or email[-1]=='@' or email[0]=='@':
      return render_template('update_resume_error.html',username=username)
  if number!='':
    if number[3]!='-' or number[7]!='-' or number.count('-')>2 or len(number)!=12:
      return render_template('update_resume_error.html',username=username)
    else:
      n=number.split('-')
      if not str.isdigit(n[0])  or  not str.isdigit(n[1]) or not str.isdigit(n[1]):
        return render_template('update_resume_error.html',username=username)
   ##check end
  cur=g.conn.execute("select * from resume_updated where jobseeker_id=%s;", jid)
  resume=cur.first()
  if resume==None:
    cur.g.conn.execute("select max(resume_id)+1 from resume_updated;")
    rid=cur.first()[0]
    g.conn.execute("insert into resume_updated values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(rid,jid,education,skills,volunteer,honor,work_experience,certificate,address,email,number))
  else:
    if education!='':
      g.conn.execute("update resume_updated set education=%s where jobseeker_id=%s;",(education,jid))
    if skills!='':
      g.conn.execute("update resume_updated set skills=%s where jobseeker_id=%s;"%(skills,jid))
    if volunteer!='':
      g.conn.execute("update resume_updated set volunteer=%s where jobseeker_id=%s;",(volunteer,jid))
    if honor!='':
      g.conn.execute("update resume_updated set honor=%s where jobseeker_id=%s;",(honor,jid))
    if work_experience!='':
      g.conn.execute("update resume_updated set work_experience=%s where jobseeker_id=%s;",(work_experience,jid))
    if certificate!='':
      g.conn.execute("update resume_updated set certificate=%s where jobseeker_id=%s;",(certificate,jid))
    if address!='':
      g.conn.execute("update resume_updated set address=%s where jobseeker_id=%s;",(address,jid))
    if email!='':
      g.conn.execute("update resume_updated set email=%s where jobseeker_id=%s;",(email,jid))
    if number!='':
      g.conn.execute("update resume_updated set phone_number=%s where jobseeker_id=%s;",(number,jid))
  return render_template('update_resume_sus.html',username=username)

           
#search job
@app.route('/jobseeker/<username>/search',methods=['POST'])
def search_j(username):
  cursor=g.conn.execute("select j.jobseeker_id from jobseeker as j, person as p where j.user_id=p.user_id and p.username=%s",username)
  jid=cursor.first()[0]
  catagory=request.form['type'].lower()
  employer=request.form['employer'].lower()
  title=request.form['title'].lower()
  location=request.form['location'].lower()
  salary1=str(request.form['salary'])
  if salary1!='':
    if not str.isdigit(salary1):
      return render_template('jobsearch_invalid.html')
    else:
      salary=int(salary1)
  where=[]
  m=[]
  c=' and j.catagory=%s'
  where.append(c)
  m.append(catagory)
  if employer!='':
    e=' lower(e.name) like %s'
    where.append(e)
    emp='%'+employer+'%'
    m.append(emp)
  if title!='':
    t=' lower(j.title) like %s'
    where.append(t)
    tit='%'+title+'%'
    m.append(tit)
  if location!='':
    l=' lower(j.location) like %s'
    where.append(l)
    loc='%'+location+'%'
    m.append(loc)
  if salary1!='':
    s=' j.salary>%s'
    where.append(s)
    m.append(salary)
  w=where[0]
  i=1
  while i<len(where):
    w=w+' and'+where[i]
    i+=1
  c='select j.* from job_posted as j, employer as e where e.employer_id=j.employer_id'
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
    cur=g.conn.execute("select name from employer where employer_id=%s;",b[0])
    name=cur.first()[0]
    b1=[]
    b1.append(name)
    for i in range(1,len(b)):
        b1.append(b[i])
    data.append(b1)
  return render_template('jobsearch.html',**locals())
    
  
#apply job
@app.route('/jobseeker/<username>/applyjob',methods=['POST'])
def apply_job(username):
  jobid=int(request.form['job_id'])
  cursor=g.conn.execute("select j.jobseeker_id from jobseeker as j, person as p where j.user_id=p.user_id and p.username=%s",username)
  jid=cursor.first()[0]
  pair=(jid,jobid)
  cur=g.conn.execute("select jobseeker_id,job_id from applyjob;")
  allpairs=cur.fetchall()
  if pair in allpairs:
    return render_template('applyjob_error.html',username=username)
  else:
    cur=g.conn.execute("select employer_id from job_posted where job_id=%s;",jobid)
    ename=cur.first()[0]
    new=(jid,jobid,ename)
    g.conn.execute("insert into applyjob values (%s,%s,'apply',%s);",new)
    return render_template('applyjob_sus.html',username=username)
  
           
#view application and interview for jobseeker
@app.route('/jobseeker/<username>/status')
def apply(username):
  cur=g.conn.execute("select a.* from jobseeker as j, person as p, applyjob as a where a.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id and p.username=%s;",username)
  s=cur.fetchall()
  cur.close()
  applications=[]
  for m in s:
    cursor=g.conn.execute("select e.name,j.title from job_posted as j,employer as e where j.job_id=%s and e.employer_id=%s;",(m[1],m[3]))
    n=cursor.first()
    applications.append((m[1],n[0],n[1],m[2]))
  interviews=[]
  for m in s:
    if m[2]=='interview':
        cursor=g.conn.execute("select e.name,j.title from job_posted as j,employer as e where j.job_id=%s and e.employer_id=%s;",(m[1],m[3]))
        n=cursor.first()
        cursor=g.conn.execute("select time from interview where job_id=%s and employer_id=%s and jobseeker_id=%s;",(m[1],m[3],m[0]))
        n2=cursor.first()[0]
        interviews.append((m[1],n[0],n[1],n2))
  return render_template('application_j.html',**locals())


#view application and interview for employer
@app.route('/employer/<username>/application')
def application(username):
  cur=g.conn.execute("select a.* from employer as e, person as p, applyjob as a where a.employer_id=e.employer_id and e.user_id=p.user_id and p.username=%s;",username)
  s=cur.fetchall()
  cur.close()
  applications=[]
  alljid=[]
  allname=[]
  for m in s:
    cursor=g.conn.execute("select p.username from jobseeker as j,person as p where j.jobseeker_id=%s and p.user_id=j.user_id;",m[0])
    n=cursor.first()[0]
    cursor=g.conn.execute("select title from job_posted where job_id=%s;",m[1])
    n1=cursor.first()[0]
    applications.append((m[1],n1,n,m[2]))
    if m[1] not in alljid:
      alljid.append(m[1])
    if n not in allname:
      allname.append(n)
  interviews=[]
  for m in s:
    if m[2]=='interview':
        cursor=g.conn.execute("select p.username from jobseeker as j,person as p where j.jobseeker_id=%s and p.user_id=j.user_id;",m[0])
        n=cursor.first()[0]
        cursor=g.conn.execute("select title from job_posted where job_id=%s;",m[1])
        n1=cursor.first()[0]
        cursor=g.conn.execute("select time from interview where job_id=%s and employer_id=%s and jobseeker_id=%s;",(m[1],m[3],m[0]))
        n2=cursor.first()[0]
        interviews.append((m[1],n1,n,n2))
  
  return render_template('application_e.html',**locals())
  
           
           
#edit status of application
@app.route('/editstatus/<username>',methods=['POST']) 
def edit(username):
  job=request.form['job_id']
  name=request.form['jobseeker']
  status=request.form['status']
  time=str(request.form['time'])
  if job=='' or name=='':
    return render_template('status_invalid.html')
  cur=g.conn.execute("select j.jobseeker_id from jobseeker as j,person as p where p.user_id=j.user_id and p.username=%s;",name)
  jid=cur.first()[0]
  #check jobid and name
  jobid=int(job)
  cursor=g.conn.execute("select a.job_id, p.username from applyjob as a,person as p,jobseeker as j where a.job_id=%s and a.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id;",jobid)
  pair=cursor.fetchall()
  cursor.close()
  if (jobid, name) not in pair:
    return render_template('status_invalid.html')
  #check status
  cursor=g.conn.execute("select status from applyjob where jobseeker_id=%s and job_id=%s;",(jid,jobid))
  s=cursor.first()[0]
  if s=='employed':
    return render_template('status_error.html')
  #check time
  if status=='interview':
    if time=='':
      return render_template('status_invalid.html')
    else:
      cursor=g.conn.execute("select %s like '201_-__-__';",time)
      valid=cursor.first()[0]
      if not valid:
        return render_template('status_invalid.html')
      else:
        t=time.split('-')
        if not str.isdigit(t[0]) or not str.isdigit(t[1]) or not str.isdigit(t[2]):
          return render_template('status_invalid.html')
        else:
          if int(t[0])<2016 or int(t[1])>12 or int(t[1])<1 or int(t[2])<1:
            return render_template('status_invalid.html')
          else:
            if int(t[1]) in (1,3,5,7,8,10,12) and int(t[2])>31:
              return render_template('status_invalid.html')
            elif int(t[1]) in (4,6,9,11) and int(t[2])>30:
              return render_template('status_invalid.html')
            elif int(t[1])==2 and int(t[2])>28:
              return render_template('status_invalid.html')
            else:
              cur=g.conn.execute("select age(timestamp %s);",time)
              a1=cur.first()[0]
              cur=g.conn.execute("select extract(day from %s);",a1)
              if cur.first()[0]>0:
                return render_template('status_invalid.html')
  #check end
  g.conn.execute("update applyjob set status=%s where job_id=%s and jobseeker_id=%s;",(status, jobid,jid))
  if status=='interview' and s=='apply':
    cur=g.conn.execute("select employer_id from job_posted where job_id=%s;",jobid)
    eid=cur.first()[0]
    cur=g.conn.execute("select max(interview_id)+1 from interview;")
    iid=cur.first()[0]
    g.conn.execute("insert into interview values (%s,timestamp %s, %s, %s, %s);",(iid, time, eid, jid, jobid))
  elif status=='interview' and s=='interview':
    g.conn.execute("update interview set time=timestamp %s where jobseeker_id=%s and job_id=%s;",(time,jid,jobid))
  elif status=='employed' and s=='interview':
    g.conn.execute("delete from interview where jobseeker_id=%s and job_id=%s;", (jid,jobid))
  return render_template('status_sus.html')
    
  
  

#search resume
@app.route('/employer/<username>/search',methods=['POST'])
def search_r(username):
  cursor=g.conn.execute("select e.employer_id from employer as e, person as p where e.user_id=p.user_id and p.username=%s",username)
  eid=cursor.first()[0]
  jobseeker=request.form['jobseeker'].lower()
  skills=request.form['skills'].lower()
  honor=request.form['honor'].lower()
  volunteer=request.form['Volunteer'].lower()
  work_experience=request.form['work_experience'].lower()
  certificate=request.form['Certificate'].lower()
  where=[]
  m=[]
  if jobseeker!='':
    j=' lower(jobseeker) like %s'
    where.append(j)
    jseeker='%'+jobseeker+'%'
    m.append(jseeker)
  if skills!='':
    s=' lower(skills) like %s'
    where.append(s)
    sk='%'+skills+'%'
    m.append(sk)
  if honor!='':
    h=' lower(honor) like %s'
    where.append(h)
    hn='%'+honor+'%'
    m.append(hn)
  if volunteer!='':
    v=' lower(volunteer) like %s'
    where.append(v)
    vl='%'+volunteer+'%'
    m.append(vl)  
  if work_experience!='':
    work=' lower(work_experience) like %s'
    where.append(work)
    wo='%'+work_experience+'%'
    m.append(wo)
  if certificate!='':
    cert=' lower(certificate) like %s'
    where.append(cert)
    ce='%'+certificate+'%'
    m.append(ce)
  w=where[0]
  i=1
  while i<len(where):
    w=w+' and'+where[i]
    i+=1
  c='select * from resume_updated where'
  cmd=c+w+';'
  cur=g.conn.execute(cmd,m)
  res=cur.fetchall()
  cur.close()
  j_name=[]
  data=[]
  for n in res:
    b=n[:]
    cur=g.conn.execute("select p.username from jobseeker j,person p where p.user_id=j.user_id and jobseeker_id=%s;",b[1])
    name=cur.first()[0]
    b1=[]
    b1.append(name)
    j_name.append(name)
    for i in range(2,len(b)):
        b1.append(b[i])
    data.append(b1)
  return render_template('resumesearch.html',**locals())
           

#resume followed
@app.route('/employer/<username>/resume')
def resume_followed(username):
  cursor=g.conn.execute("select e.employer_id from person as p,employer as e where p.user_id=e.user_id and p.username=%s;",username)
  eid=cursor.first()[0]
  cursor=g.conn.execute("select p.username from follow as f,resume_updated as r,person as p,jobseeker as j where f.resume_id=r.resume_id and r.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id and f.employer_id=%s;",eid)
  resumelist = []
  for row in cursor:
    resumelist.append(row[0])
  cursor.close()
  names=(',').join(resumelist)
  return render_template("resume_followed.html",**locals())

#view resume
@app.route('/viewresume', methods=['POST'])
def viewr():
  rname= request.form['proname']
  cur=g.conn.execute("select p.username,r.* from resume_updated r,person p where r.jobseeker_id=p.user_id and p.username=%s;",rname)
  resume=cur.first()
  if resume==None:
    education=''
    skills=''
    volunteer=''
    honor=''
    work_experience=''
    certificate=''
    address=''
    email=''
    phone_number=''
  else:
    name=resume[0]
    education=resume[3]
    skills=resume[4]
    volunteer=resume[5]
    honor=resume[6]
    work_experience=resume[7]
    certificate=resume[8]
    address=resume[9]
    email=resume[10]
    phone_number=resume[11]
  return render_template("viewresume.html",**locals())


#add follow resume
@app.route('/employer/<username>/addfollow',methods=['POST'])
def addfollow(username):
  newname = request.form['addname']
  cursor = g.conn.execute("SELECT p.username FROM person as p,jobseeker as j where j.user_id=p.user_id;")
  allnames = []
  for result in cursor:
    allnames.append(result[0])
  cursor.close()
  if newname not in allnames:
    return render_template('followerror.html',name=username,username=newname)
  cursor=g.conn.execute("select e.employer_id from person as p,employer as e where p.user_id=e.user_id and p.username=%s;",username)
  eid=cursor.first()[0]
  cursor=g.conn.execute("select p.username from follow as f,resume_updated as r,person as p,jobseeker as j where f.resume_id=r.resume_id and r.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id and f.employer_id=%s;",eid)
  resumelist = []
  for row in cursor:
    resumelist.append(row[0])
  cursor.close()
  if newname in resumelist:
    return render_template('followerror1.html',name=username,username=newname)
  else:
    cur=g.conn.execute("select r.resume_id from resume_updated as r,person as p,jobseeker as j where r.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id and p.username=%s;",newname)
    newid=cur.first()[0]
    g.conn.execute("insert into follow values(%s,%s)",(eid,newid))
    return render_template('followsus.html',name=username)

#delete follow resume
@app.route('/employer/<username>/deletefollow',methods=['POST'])
def deletefollow(username):
  cursor=g.conn.execute("select e.employer_id from person as p,employer as e where p.user_id=e.user_id and p.username=%s;",username)
  eid=cursor.first()[0]
  oldname = request.form['delname']
  cur=g.conn.execute("select r.resume_id from resume_updated as r,person as p,jobseeker as j where r.jobseeker_id=j.jobseeker_id and j.user_id=p.user_id and p.username=%s;",oldname)
  oldid=cur.first()[0]
  g.conn.execute("delete from follow where employer_id=%s and resume_id=%s;",(eid,oldid))
  return render_template('followsus.html',name=username)

           

           
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
