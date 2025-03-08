from flask import Flask, render_template, request , jsonify
from utils.actions import login_validation_check , selling_injection_in_mongo , generate_response , signup_mongo ,compute_plan_agri , apple_count , weed_detection , leaf_disease_detection , fetch_store_documents,scrape_agriculture_news, get_weather
import os
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")  # Ensure MongoDB is running
db = client.agribot 

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/farmerlogin")
def farmerlogin():
    return render_template("farmerlogin.html")

@app.route("/buyerlogin")
def buyerlogin():   
    return render_template("buyerlogin.html")

@app.route("/farmerloginauth", methods=["POST"])
def farmerloginauth():
    number = request.form.get("number")
    password = request.form.get("password")
    validation_result = login_validation_check(number, password,"farmer")
    if validation_result:
        return render_template("homepage.html")
    else:
        return "Wrong password", 401

@app.route("/buyerloginauth", methods=["POST"])
def buyerloginauth():
    number = request.form.get("number")
    password = request.form.get("password")
    validation_result = login_validation_check(number, password, "buyer")
    if validation_result:
        return render_template("homepage.html")
    else:
        return "Wrong password", 401

@app.route("/buyersignup")
def buyersignup():
    return render_template("signup.html")

@app.route("/farmersignup")
def farmersignup():
    return render_template("signupfarmer.html")  

@app.route("/signupprocessfarmer", methods=["POST"])
def signupprocessfarmer():
    name = request.form.get('fname') + " " + request.form.get('lname')
    mobile_number = int(request.form.get('mobileno'))
    password = request.form.get('password')
    address = request.form.get('address')
    gender = request.form.get('gender')
    age = int(request.form.get('age'))
    dateofbirth = request.form.get('dob')
    email = request.form.get('email')
    blood_group = request.form.get('bloodgroup')
    unique_id = request.form.get('uniqueid')
    state = request.form.get('state')
    country = request.form.get('country')

    signup_mongo(name, mobile_number, password, address, gender, age, dateofbirth, email, blood_group, unique_id, state, country)
    return render_template("homepage.html")

@app.route("/signupprocessbuyer", methods=["POST"])
def signupprocessbuyer():
    return render_template("homepage.html")

@app.route("/newspage")
def newspage():
    scrape_agriculture_news()
    collection = db.news
    city = request.args.get("city")
    # Fetch all news articles from MongoDB
    news_articles = list(collection.find({}, {"_id": 0})) 
    weather_data = get_weather(city) if city else None  # Exclude _id for clean JSON
    
    return render_template("news1.html", news_articles=news_articles,weather_data=weather_data, city=city) 

@app.route("/communicationpage")
def communicationpage():
    return render_template("communication.html") 

@app.route("/storepage", methods=["GET"])
def storepage():
    search_term = request.args.get('search', '')
    category_filter = request.args.get('category', 'all')
    sort_by = request.args.get('sort', 'default')

    products = fetch_store_documents()

    # Ensure image_path is properly formatted
    for product in products:
        if 'image_path' in product and product['image_path']:  # Check if image exists
            product['image_path'] = product['image_path']
        else:
            product['image_path'] = '/static/uploads/default.jpg'  # Fallback image

        # Ensure price is stored as a float for proper sorting
        try:
            product['price'] = float(product['price'])
        except ValueError:
            product['price'] = 0.0  # If conversion fails, set default price

    # Apply category filter
    if category_filter != 'all':
        products = [p for p in products if p['product_category'].lower() == category_filter.lower()]

    # Apply search filter
    if search_term:
        products = [
            p for p in products if search_term.lower() in p['product_name'].lower() 
            or search_term.lower() in p['description'].lower()
        ]

    # Apply sorting
    if sort_by == 'price-low':
        products.sort(key=lambda p: p['price'])
    elif sort_by == 'price-high':
        products.sort(key=lambda p: p['price'], reverse=True)
    elif sort_by == 'name-a-z':
        products.sort(key=lambda p: p['product_name'].lower())
    elif sort_by == 'name-z-a':
        products.sort(key=lambda p: p['product_name'].lower(), reverse=True)

    return render_template("store.html", products=products, search_term=search_term, category_filter=category_filter, sort_by=sort_by)




@app.route("/quickstartpage")
def quickstartpage():
    return render_template("quickfarm.html") 

@app.route("/compute_plan",methods=['POST'])
def compute_plan():
    landMeasurements = request.form.get("landMeasurements")
    budget = request.form.get("budget")
    machinery = request.form.get("machinery")
    labours = request.form.get("labours")
    soilType = request.form.get("soilType")
    irrigationMethod = request.form.get("irrigationMethod")
    storageFacilities = request.form.get("storageFacilities")

    response = compute_plan_agri(landMeasurements,budget,machinery,labours,soilType,irrigationMethod,storageFacilities)
    return render_template('chatbot_response.html', user_input=response)

@app.route("/sellingpage")
def sellingpage():
    return render_template("selling_page.html") 

@app.route("/financialpage")
def financialpage():
    return render_template("financial.html")

@app.route("/Insurancepage")
def Insurancepage():
    return render_template("insurance.html")

@app.route("/loanpage")
def loanpage():
    return render_template("loan.html")

@app.route("/loanformpage")
def loanformpage():
    return render_template("loanform.html")

@app.route("/insuranceformpage")
def insuranceformpage():
    return render_template("insuranceform.html")

@app.route("/chatbotpage")
def chatbotpage():
    return render_template("chatbot.html")

@app.route("/dashboardpage")
def dashboardpage():
    return render_template("dashboard.html")


@app.route("/sellingprocess", methods=["POST"])
def sellingprocess():
    name = request.form["name"]
    email = request.form["email"]
    contact = request.form["contact"]
    address = request.form["address"]
    product_name = request.form["productName"]
    product_type = request.form["productType"]
    quantity = request.form["quantity"]
    price = request.form["price"]
    description = request.form["description"]
    
    image_path = None
    if "productImage" in request.files:
        file = request.files["productImage"]
        if file.filename != "":
            filename = file.filename  
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename) 
            file.save(filepath)  

            image_path = f"/static/uploads/{filename}"
    
    if selling_injection_in_mongo(name, email, contact, address, product_name, product_type, quantity, price, description, image_path):
        return render_template("confirmation_post.html", name=name, email=email, contact=contact, 
                               address=address, product_name=product_name, 
                               product_type=product_type, quantity=quantity, 
                               price=price, description=description, image_path=image_path)

@app.route("/cvpage")
def cvpage():
    return render_template("cv.html")

@app.route('/leafbase', methods=['GET', 'POST'])
def leafbase():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            # Call the leaf model function here
            result = leaf_disease_detection(filepath)
            return render_template('leafresult.html', result=result)
    return render_template('upload_form.html', task='leaf')

@app.route('/weedbase', methods=['GET', 'POST'])
def weedbase():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            # Call the leaf model function here
            result = weed_detection(filepath)
            return render_template('weedresult.html', result=result)
    return render_template('upload_form.html', task='weed')

@app.route('/countbase', methods=['GET', 'POST'])
def countbase():
    if request.method == 'POST':
        file = request.files['image']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            # Call the leaf model function here
            result = apple_count(filepath)
            return render_template('countresult.html', result=result)
    return render_template('upload_form.html', task='count')

@app.route('/chatprocess', methods=['POST'])
def chatprocess():
    user_input = request.form['user_input'] 
    llm_type = request.form['llm_type'] 
    category = request.form['category']
    response = generate_response(user_input,llm_type,category)
    return render_template('chatbot_response.html', user_input=response)

if __name__ == "__main__":
    app.run(debug=True)
