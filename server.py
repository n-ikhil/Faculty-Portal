from flask import Flask, session, redirect, request, url_for,flash
from flask.templating import render_template
from database.nosql import nosql
from database.psql import psql


app = Flask(__name__)
pobj= None
nobj=None
app.secret_key = 'qwertyuiopqazwsx'
uneditable_content_personal=["","_id","eid","name","department"]
private_content={"_id":0,"eid":0}


def initializer():
    global pobj,nobj
    pobj=psql()
    nobj=nosql()

def filter_dictionary_personal_profile(old,new_html):

    new={}
    siz=(int((len(new_html)/2))-1)
    for x in range(siz):
        h=new_html["head"+str(x)]
        p=new_html["par"+str(x)]
        if h not in uneditable_content_personal:
            new[h]=p
    ###
    uns={}
    upd={}
    for o in old:
        if o not in new and o not in uneditable_content_personal:
            uns[o]=1
            continue
        
    for n in new:
        if n not in old or old[n]!=new[n]:
            upd[n]=new[n]
    
    newh=new_html["newh"]
    newp=new_html["newp"]
    if newh not in uneditable_content_personal:
        upd[newh]=newp

    return (uns,upd) 


@app.route("/",methods=["GET","POST"])
def public():
    return render_template("root.html")

@app.route("/public",methods=["GET"])
def root():

    res=nobj.get_list_pretty()
    return render_template("public_list.html",lis=res)

@app.route("/public/<num>")
def public_personal_profile(num):
    query={"eid":int(num,10)}
    result=nobj.get_data(query,private_content)
    return render_template("public_profile.html",dict=result)


@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="GET":        
        return render_template("login.html")
    
    else:
        ans=request.form.to_dict()
        if(ans["eid"].isnumeric()!=True):
            return redirect(url_for("login"))
        eid=int(ans["eid"],10)
        if(pobj.verify_user({"eid":eid,"pass":ans["pass"]})):
            session['username']=eid
            if(eid==201700):
                return redirect(url_for("admin"))
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("login"))

@app.route("/logout",methods=["POST","GET"])
def logout():
    if 'username' in session:
        session.pop('username',None)
    return redirect(url_for("login"))


@app.route("/register",methods=['POST','GET'])
def register_page():
    if(request.method=="GET"):
        return render_template('register.html')
    else:
        input=request.form.to_dict()
        eid=pobj.insert(data=input)
        if(eid!=-1):
            nobj.insert_data({"eid":eid,"name":input["name"],"email":input["email"],"department":input["dept"]})
            return render_template("registration_successfull.html",eid=str(eid))
        else:
            flash("Kindly use a different email address")
            return redirect(url_for("register_page"))

@app.route("/delete",methods=["GET","POST"])
def delete():
    nobj.clear_data()
    pobj.clear_data()
    return redirect(url_for("login"))


@app.route("/dashboard",methods=["GET"])
def dashboard():
    if 'username' in session:
        eid=session['username']
        thisyear_leaves=pobj.get_leaves(eid)
        return render_template("dashboard.html",thisyear=thisyear_leaves)
    else:
        return redirect(url_for("login"))

@app.route("/dashboard/personal_profile",methods=["GET","POST"])
def personal_profile():
    if 'username' in session:
        eid=session['username']

        if request.method=="GET":
            query={"eid":eid}
            result=nobj.get_data(query,private_content)
            return render_template("personal_profile.html",dict=result,eid=eid)
        else:
            query={"eid":eid}
            result=nobj.get_data(query,private_content)
            new=request.form.to_dict()
            (uns,upd)=filter_dictionary_personal_profile(result,new)
            
            if(len(uns)!=0):
                nobj.unset_field(query,uns)
            
            if(len(upd)!=0):
                nobj.update_data(query,upd)
            

            if(request.form["sub"]=="SUBMIT"):
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("personal_profile"))
    else:
        return redirect(url_for("login"))
        

@app.route("/admin",methods=["GET","POST"])
def admin():
    if 'username' not in session or session['username']!=201700:
        return redirect(url_for("login"))
        
    if request.method=="GET":
        return render_template("admin_base.html",lis=nobj.get_list_pretty())
    else:
        input=request.form.to_dict()
        print(input)
        if(input["submit"]=="promotion"):
            tedi=int(input["eid"],10)
            input["eid"]=tedi
            res=pobj.promote(input)
            if(res==False):
                flash("your previuos attempt was unsuccesfull")
                return redirect(url_for("admin"))
            else:
                flash("your previuos attempt was succesfull")
                return redirect(url_for("admin"))
        elif(input["submit"]=="leaves"):
            res=pobj.change_leaves(input)
            if(res==False):
                flash("your previuos attempt was unsuccesfull")
                return redirect(url_for("admin"))
            else:
                flash("your previuos attempt was succesfull")
                return redirect(url_for("admin"))
        elif(input["submit"]=="route"):
            first=input["P1"]
            second=input["p2"]
            res=pobj.change_route(first,second)
            if(res==False):
                flash("your previuos attempt was unsuccesfull")
                return redirect(url_for("admin"))
            else:
                flash("your previuos attempt was succesfull")
                return redirect(url_for("admin"))
            

        
@app.route("/dashboard/new_application",methods=["GET","POST"])
def new_application():
    if 'username' not in session:
        return redirect(url_for("login"))
    eid=session['username']
    if request.method=="GET":
        return render_template("leave_application.html")
    else:
        input=request.form.to_dict()
        input["eid"]=eid
        res=pobj.apply_leave(input)
        if(res):
            flash("Applied successfully")
            return redirect(url_for("dashboard"))
        else:
            flash("previous application attempt was not possible")
            return redirect(url_for("dashboard"))

@app.route("/dashboard/application_status_history",methods=["GET","POST"])
def application_status_history():
    if 'username' not in session:
        return redirect(url_for("login"))
    eid=session['username']
    if request.method=="GET":
        lis=pobj.get_leave_history(eid)
        return render_template("leave_history.html",data=lis)
    else:
        lid=request.form["sub"]
        return redirect(url_for("dashboard"))
    
@app.route("/application_status",methods=["GET","POST"])
def application_status():
    if 'username' not in session:
        return redirect(url_for("login"))
    eid=session['username']
    if request.method=="POST":
        input=request.form.to_dict()
        if "sub" in input:
            lid=input["sub"]
            data=pobj.get_leave_data(lid)
            return render_template("leave_detail.html",data=data)
        else:
            res=pobj.add_detail(input)
            if(res):
                flash("your previous operation was successfull")
                return redirect(url_for("application_status_history"))
            else:
                flash("your previous operation was not successfull")
                return redirect(url_for("application_status_history"))




if __name__ == "__main__":
    initializer()
    
    app.debug = True
    app.run()
    app.run(debug = True)
