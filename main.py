from flask import Flask, render_template, request , jsonify, session, app, Response, send_from_directory
from utils.actions import login_validation_check , selling_injection_in_mongo , generate_response , signup_mongo ,compute_plan_agri , apple_count , weed_detection , leaf_disease_detection , fetch_store_documents,scrape_agriculture_news, get_weather
import os
from pymongo import MongoClient
import ollama
import time
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
from ultralytics import YOLO
import numpy as np
import cv2
client = MongoClient("mongodb://localhost:27017/")  # Ensure MongoDB is running
db = client["agribot"]



os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

app = Flask(__name__)

app.secret_key = "summasecretkey"
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
    session['number']=number
    session['type']="farmer"
    if validation_result:
        return render_template("homepage.html")
    else:
        return "Wrong password", 401
    
    

@app.route("/buyerloginauth", methods=["POST"])
def buyerloginauth():
    number = request.form.get("number")
    password = request.form.get("password")
    validation_result = login_validation_check(number, password, "buyer")
    session['number']=number
    session['type']="buyer"
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
    mobile_number = (request.form.get('mobileno'))
    password = request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    address = request.form.get('address')
    gender = request.form.get('gender')
    age = int(request.form.get('age'))
    dateofbirth = request.form.get('dob')
    email = request.form.get('email')
    blood_group = request.form.get('bloodgroup')
    unique_id = request.form.get('aadhaar')
    state = request.form.get('state')
    country = request.form.get('country')
    type="farmer"

    

    if password != confirm_password:
        return jsonify({"message": "Passwords do not match!"}), 400

    signup_mongo(name, mobile_number, password, address, gender, age, dateofbirth, email, blood_group, unique_id, state, country,type)

    session["type"]=type
    session["number"]=mobile_number
    return render_template("farmerlogin.html")

@app.route("/signupprocessbuyer", methods=["POST"])
def signupprocessbuyer():
    name = request.form.get('fname') + " " + request.form.get('lname')
    mobile_number = int(request.form.get('mobileno'))
    password = request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    address = request.form.get('address')
    gender = request.form.get('gender')
    age = int(request.form.get('age'))
    dateofbirth = request.form.get('dob')
    email = request.form.get('email')
    blood_group = request.form.get('bloodgroup')
    unique_id = request.form.get('aadhaar')
    state = request.form.get('state')
    country = request.form.get('country')
    type="buyer"

    if password != confirm_password:
        return jsonify({"message": "Passwords do not match!"}), 400

    signup_mongo(name, mobile_number, password, address, gender, age, dateofbirth, email, blood_group, unique_id, state, country,type)

    session["type"]=type
    session["number"]=mobile_number

    return render_template("buyerlogin.html")

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

    for product in products:
        # Handle different types of image_path (single string or list)
        if isinstance(product.get('image_path'), list) and product['image_path']:
            product['image_path'] = product['image_path']  # Use all images in the list
        elif isinstance(product.get('image_path'), str) and product['image_path']:
            product['image_path'] = [product['image_path']]  # Convert single string to list
        else:
            product['image_path'] = ['/static/uploads/default.jpg']  # Fallback image

        # Convert price to float for sorting
        try:
            product['price'] = float(product['price'])
        except ValueError:
            product['price'] = 0.0

    # Apply category filter
    if category_filter != 'all':
        products = [p for p in products if p['product_type'].lower() == category_filter.lower()]

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

@app.route("/compute_plan", methods=['POST'])
def compute_plan():
    if "number" not in session or "type" not in session:
        return "User not logged in", 401  # Unauthorized access

    mobile_number = str(session["number"])  # Ensure it's a string
    user_type = session["type"]  
    landMeasurements = request.form.get("landMeasurements")
    budget = request.form.get("budget")
    machinery = request.form.get("machinery")
    labours = request.form.get("labours")
    soilType = request.form.get("soilType")
    irrigationMethod = request.form.get("irrigationMethod")
    storageFacilities = request.form.get("storageFacilities")
    waterAvailability = request.form.get("waterAvailability")
    waterQuantity = request.form.get("waterQuantity")
    farmingType = request.form.get("farmingType")
    current_month = datetime.now().strftime("%B")

    collection = db["farmer_details"] if user_type == "farmer" else db["buyer_details"]

    # Fetch user details from MongoDB
    user_data = collection.find_one({"mobile_number": mobile_number})
    district=user_data.get("district","")
    state=user_data.get("state","")
    country=user_data.get("country","")

    return render_template("chatbot_response.html",
                           landMeasurements=landMeasurements,
                           budget=budget,
                           machinery=machinery,
                           labours=labours,
                           soilType=soilType,
                           irrigationMethod=irrigationMethod,
                           storageFacilities=storageFacilities,
                           waterAvailability=waterAvailability,
                           waterQuantity=waterQuantity,
                           farmingType=farmingType,
                           current_month=current_month,
                           district=district,
                           state=state,
                           country=country)

@app.route("/stream_plan")
def stream_plan():
    landMeasurements = request.args.get("landMeasurements")
    budget = request.args.get("budget")
    machinery = request.args.get("machinery")
    labours = request.args.get("labours")
    soilType = request.args.get("soilType")
    irrigationMethod = request.args.get("irrigationMethod")
    storageFacilities = request.args.get("storageFacilities")
    waterAvailability = request.args.get("waterAvailability")
    waterQuantity = request.args.get("waterQuantity")
    farmingType = request.args.get("farmingType")
    current_month = request.args.get("current_month")
    district = request.args.get("district")
    state = request.args.get("state")
    country = request.args.get("country")

    def stream_response():
        prompt = f"""
        You are an advanced agricultural AI assistant. Generate a detailed agricultural work plan based on the following details:

        - **Current Month:** {current_month}
        - **Location:** {district}, {state}, {country}
        - **Land Measurements:** {landMeasurements} acres
        - **Budget:** {budget} INR
        - **Machinery Available:** {machinery}
        - **Number of Labors:** {labours}
        - **Soil Type:** {soilType}
        - **Irrigation Method:** {irrigationMethod}
        - **Water Availability:** {waterAvailability}
        - **Average Water Quantity Provided:** {waterQuantity} liters
        - **Storage Facilities:** {storageFacilities}
        - **Farming Type:** {farmingType} (Organic/Non-Organic)

        Based on the given details:
        1. Recommend the best **crops** suitable for the season and soil.
        2. Provide a **step-by-step timeline** for sowing, irrigation, fertilization, and harvesting.
        3. Suggest **resource allocation** for optimizing budget and manpower.
        4. Highlight **best agricultural practices** for higher yield.
        5. Offer **market insights** on expected profitability and storage strategies.

        Ensure the plan is **well-structured, practical, and region-specific**.
        """

        stream = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}], stream=True)

        for chunk in stream:
            text_chunk = chunk.get("message", {}).get("content", "")
            if text_chunk:
                yield text_chunk + " "
                time.sleep(0.08)  # Simulate typing delay

    return Response(stream_response(), content_type="text/plain")

@app.route("/sellingpage")
def sellingpage():
    if "number" not in session or "type" not in session:
        return "User not logged in", 401  # Unauthorized access

    mobile_number = str(session["number"])  # Ensure it's a string
    user_type = session["type"]  


    # Determine the correct collection
    collection = db["farmer_details"] if user_type == "farmer" else db["buyer_details"]

    # Fetch user details from MongoDB
    user_data = collection.find_one({"mobile_number": mobile_number})

    if not user_data:
        return "User details not found", 404  # Handle case where user doesn't exist

    # Extract relevant details
    user_details = {
        "name": user_data.get("name", ""),
        "email": user_data.get("email", ""),
        "contact": user_data.get("mobile_number", ""),  # Stored as string
        "address": user_data.get("address", "")
    }

    # Render template with user details pre-filled
    return render_template("selling_page.html", **user_details)
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
    
    image_paths = []  # Store multiple image paths

    if "productImages" in request.files:
        files = request.files.getlist("productImages")  # Get multiple images
        for file in files:
            if file.filename != "":
                filename = file.filename
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                image_paths.append(f"/static/uploads/{filename}")  # Store file path

    # Call MongoDB insertion function (ensure it supports image_paths as a list)
    if selling_injection_in_mongo(name, email, contact, address, product_name, 
                                  product_type, quantity, price, description, image_paths):
        return render_template("confirmation_post.html", name=name, email=email, 
                               contact=contact, address=address, product_name=product_name, 
                               product_type=product_type, quantity=quantity, 
                               price=price, description=description, image_paths=image_paths)
    

@app.route("/update_product", methods=["POST"])
def update_product():
    updated_data = {
        "name": request.form["name"],
        "email": request.form["email"],
        "contact": request.form["contact"],
        "address": request.form["address"],
        "product_name": request.form["product_name"],
        "product_type": request.form["product_type"],
        "quantity": request.form["quantity"],
        "price": request.form["price"],
        "description": request.form["description"],
    }

    collection = db["store"]
    

    collection.update_one({"email": updated_data["email"], "product_name": updated_data["product_name"]}, {"$set": updated_data})

    return render_template("homepage.html")


@app.route("/cvpage")
def cvpage():
    return render_template("cv.html")

@app.route("/upload", methods=['GET', 'POST'])
def upload_page():
    task = request.args.get("task")
    result = None
    image_path = None

    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
        elif request.form.get("imageData"):
            image_data = request.form["imageData"]
            image_binary = base64.b64decode(image_data.split(",")[1])
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], "captured_photo.png")
            with open(filepath, "wb") as f:
                f.write(image_binary)
        else:
            return "No valid file or camera input", 400

        # Process image and get the result
        if task == "leaf":
            result, image_path = leaf_disease_detection(filepath)
        elif task == "weed":
            result, image_path = weed_detection(filepath)
        elif task == "count":
            result = apple_count(filepath)
        else:
            result = ["Invalid task!"]

        # Debugging: Print the result type
        print(f"DEBUG: Result Type: {type(result)}, Result Value: {result}")

        # Ensure result is a list before joining
        if result is None:
            result = ["No detection result"]
        elif isinstance(result, str):  # Convert a single string to a list
            result = [result]
        elif not isinstance(result, (list, tuple)):  # Ensure it's iterable
            result = [str(result)]

    return render_template("upload_form.html", task=task, result=result, image_path=image_path)


models = {
    "leaf": YOLO("yolo/plantdiseasedetection/best.pt"),
    "weed": YOLO("yolo/weeddetection/last.pt"),
    "count": YOLO("yolo/appledetection/best.pt")
}

@app.route("/video_feed", methods=['POST'])
def video_feed():
    task = request.args.get("task")
    if task not in models:
        return jsonify({"error": "Invalid task"}), 400

    model = models[task]
    
    # Decode the frame
    frame_data = request.json.get("frame")
    if not frame_data:
        return jsonify({"error": "No frame data received"}), 400

    frame_bytes = base64.b64decode(frame_data.split(",")[1])
    np_arr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Run YOLO inference
    results = model(frame)
    
    # Process results
    detections = []
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])  # Class index
            conf = float(box.conf[0])  # Confidence
            detections.append({"class": model.names[cls], "confidence": round(conf, 2)})

    return jsonify({"prediction": detections if detections else "No detection"})




@app.route('/chatprocess', methods=['POST'])
def chatprocess():
    user_input = request.form['user_input'] 
    llm_type = request.form['llm_type'] 
    category = request.form['category']
    response = generate_response(user_input,llm_type,category)
    return render_template('chatbot_response.html', user_input=response)

if __name__ == "__main__":
    app.run(debug=True)
