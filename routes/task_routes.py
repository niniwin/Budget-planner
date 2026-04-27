#@app.route("/<name>")
#def user(name):
 #   return f"Hello {name}!"
#@app.route("/admin")
#def admin():
 #   return redirect(url_for("user",name="Admin!"))
# @app.route("/login",methods=["POST","GET"])
# def login():
#     if request.method == "POST":
#         user=request.form["nm"]
#         session["user"]=user
#         session.permanent=True #This line is important
#         flash("login Successful!")
#         return redirect(url_for("user"))

    
#     else:
#         if "user" in session:
#             flash("Already logged In!")
#             return redirect(url_for("user"))
#         return render_template("login.html")

# @app.route("/user")
# def user():
#     if "user" in session:
#         user=session["user"]
#         return render_template("user.html",user=user)
#     else:
#         return redirect(url_for("login"))
    
# @app.route("/logout")   
# def logout():
   
#     flash("You have logged out!","info")
#     session.pop("user",None)
    
#     return redirect(url_for("login"))
