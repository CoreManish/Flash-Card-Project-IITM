from flask import Flask,render_template,request,redirect,url_for, session
import sqlite3
from datetime import datetime
import time

app=Flask(__name__)
app.config['SECRET_KEY']='HELLO@54'

#-----Check session for each end point except allowed routes
@app.before_request
def require_login():
    allowed_routes=['login','register']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')
@app.route('/logout')
def logout():
    session.pop('username',None)
    return redirect('/')
    


@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        conn=sqlite3.connect("project.db")
        cur=conn.cursor()
        query="""SELECT * FROM users WHERE username=? AND password=?"""
        cur.execute(query,(username,password))
        rows=cur.fetchall()
        
        if len(rows) ==1:
            #set session
            session['username']=username
            return redirect(url_for('index'))
        else:
            return redirect(url_for('register'))
    return render_template('login.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=="POST":
        name=request.form['name']
        username=request.form['username']
        password=request.form['password']
        conn=sqlite3.connect("project.db")
        cur=conn.cursor()
        try:
            query="""INSERT INTO users (name,username,password) VALUES (?,?,?)"""
            cur.execute(query,(name,username,password))
            conn.commit()
            
            if cur.rowcount ==1:
                return "Registered successfully <a href='/login'>Go to Login</a>"
        except:
            return "Username already exists <a href='/register'>Try Register again</a>"
        
    return render_template('register.html')


@app.route('/')
def index():
    conn=sqlite3.connect("project.db")
    cur=conn.cursor()
    query="""SELECT deckname,score,reviewtime from cards WHERE front IS NULL"""
    cur.execute(query)
    rows=cur.fetchall()
    
    return render_template('index.html',rows=rows)

@app.route('/createdeck',methods=['GET','POST'])
def createdeck():
    if request.method=="POST":
        deckname=request.form['deckname']
        conn=sqlite3.connect("project.db")
        cur=conn.cursor()
        query="""INSERT INTO cards (deckname) VALUES (?)"""
        cur.execute(query,(deckname,))
        conn.commit()
        return redirect(url_for('index'))
    return render_template('createdeck.html')

@app.route('/deletedeck/<deckname>')
def deletedeck(deckname):
    conn=sqlite3.connect("project.db")
    cur=conn.cursor()
    query="""DELETE FROM cards WHERE deckname=?"""
    cur.execute(query,(deckname,))
    conn.commit()
    return redirect(url_for('index'))

@app.route('/updatedeck/<deckname>',methods=['GET','POST'])
def updatedeck(deckname):
    if request.method=="POST":
        old=deckname
        new=request.form['new']
        conn=sqlite3.connect("project.db")
        cur=conn.cursor()
        query="""UPDATE cards SET deckname=? WHERE deckname=?"""
        cur.execute(query,(new,old))
        conn.commit()
        return redirect(url_for('index'))
    return render_template('updatedeck.html',deckname=deckname)


@app.route('/review/<deckname>')
def review(deckname):
    t=time.time()
    t=datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    conn=sqlite3.connect("project.db")
    cur=conn.cursor()
    query="""SELECT * FROM cards WHERE deckname=? AND nextviewtime<? AND front IS NOT NULL ORDER BY RANDOM() LIMIT 1"""
    #query="""SELECT * FROM cards WHERE deckname=? AND front IS NOT NULL"""
    cur.execute(query,(deckname,t))
    rows=cur.fetchone()
    if rows is not None:
        return render_template('review.html',deckname=deckname,rows=rows)
    else:
        return redirect(url_for('index'))

@app.route('/updatecard/<deckname>/<cardname>', methods=['GET','POST'])
def updatecard(deckname,cardname):
    if request.method=="POST":
        hardness=request.form['hardness']
        if hardness=='easy':
            score=10
            nextviewtime=time.time()+600 #show after 10 minute
        elif hardness=='medium':
            score=5
            nextviewtime=time.time()+300 #show after 5 minute
        elif hardness=='hard':
            score=1
            nextviewtime=time.time()+60 #show after 1 minute
        else:
            return redirect(url_for('index'))
        t=datetime.now()
        t=t.strftime("%Y-%m-%d %H:%M:%S")

        nextviewtime=datetime.fromtimestamp(nextviewtime).strftime("%Y-%m-%d %H:%M:%S")
        
        conn=sqlite3.connect("project.db")
        cur=conn.cursor()
        query="""UPDATE cards SET reviewtime=?,hardness=?,score=?,nextviewtime=? WHERE deckname=? AND front=?"""
        cur.execute(query,(t,hardness,score,nextviewtime,deckname,cardname))
        conn.commit()
        query1="""SELECT AVG(score) as avgscore FROM cards WHERE score IS NOT NULL AND front IS NOT NULL AND deckname=?"""
        cur.execute(query1,(deckname,))
        row=cur.fetchone()
        score=round(row[0],2)
        query2="""UPDATE cards SET reviewtime=?,score=? WHERE deckname=? AND front IS NULL"""
        cur.execute(query2,(t,score,deckname))
        conn.commit()
        return redirect(f'/review/{deckname}')

@app.route('/addcard/<deckname>',methods=['GET','POST'])
def addcard(deckname):
    if request.method=="POST":
        front=request.form['front']
        back=request.form['back']
        t=time.time()
        t=datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
        conn=sqlite3.connect("project.db")
        cur=conn.cursor()
        query="""INSERT INTO cards (deckname,front,back,nextviewtime) VALUES (?,?,?,?)"""
        cur.execute(query,(deckname,front,back,t))
        conn.commit()
        return redirect(url_for('index'))
    return render_template('addcard.html',deckname=deckname)

if __name__=="__main__":
    app.run(debug=True)