import re
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama

from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_huggingface.llms import HuggingFacePipeline
from langchain.chains import LLMChain
from transformers import AutoModelForCausalLM , AutoTokenizer , pipeline , BitsAndBytesConfig
import torch
import time
from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import ollama
import faiss
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os




client = MongoClient('mongodb://localhost:27017/') 
db = client['agribot']

def login_validation_check(number, password, type):
    if type == "farmer":
        collection = db['farmer_details']  
        user_data = collection.find_one({"mobile_number": number})

    else:
        collection = db['buyer_details'] 
        user_data = collection.find_one({"mobile_number": number})
    if user_data:
        if user_data['password'] == password:
            return True
        else:
            return False
    else:
        return False 
        
def selling_injection_in_mongo(name, email, contact, address, product_name, product_type, quantity, price, description, image_paths): 
    collection = db['store']  
    selling_data = {
        "name": name,
        "email": email,
        "contact_number": contact,
        "locality_address": address,
        "product_name": product_name,
        "product_quantity": quantity,
        "image_path": image_paths,
        "price": price,
        "description": description,
        "product_category": product_type
    }
    try:
        collection.insert_one(selling_data)  
        print("Selling data inserted successfully!")
        return True
    except Exception as e:
        print(f"Error during insertion: {e}")
        return False

def generate_response(user_input,type_of_llm,category):
    if type_of_llm == '1':  # Agriculture RAG
        llm = ChatOllama(model="llama3")
        PROMPT_TEMPLATE = '''
        With the information provided, try to answer the question. 
        If you cannot answer based on the information, say you are unable to find an answer.
        Try to understand the context deeply and answer **only based on the given information**.
        Do not generate irrelevant answers.

        Context: {context}
        Question: {question}

        Helpful answer:
        '''
        INP_VARS = ['context', 'question']
        custom_prompt_template = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=INP_VARS
        )

        # Load FAISS embeddings
        hfembeddings = HuggingFaceEmbeddings(
            model_name="thenlper/gte-large",
            model_kwargs={'device': 'cpu'}
        )
        vector_db = FAISS.load_local(
            r"P:/college stuffs/mini project/Agri-Hub - Copy/datas/faiss/agri_data/",
            hfembeddings,
            allow_dangerous_deserialization=True
        )

        # Retrieval Chain using Ollama
        retrieval_qa_chain = RetrievalQA.from_chain_type(
            llm=llm,  # Pass the ChatOllama instance instead of a lambda function
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={'k': 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": custom_prompt_template}
        )

        prompt = {'query': user_input}
        model_out = retrieval_qa_chain(prompt)
        answer = model_out['result']
        return answer

    elif type_of_llm == '2':
        llm = ChatOllama(model="llama3")  # Web Scraper RAG
        PROMPT_TEMPLATE = '''
        With the information provided, try to answer the question. 
        If you cannot answer based on the information, say you are unable to find an answer.
        Try to understand the context deeply and answer **only based on the given information**.
        Do not generate irrelevant answers.

        Context: {context}
        Question: {question}

        Helpful answer:
        '''
        INP_VARS = ['context', 'question']
        custom_prompt_template = PromptTemplate(
            template=PROMPT_TEMPLATE,
            input_variables=INP_VARS
        )

        # Load FAISS embeddings
        hfembeddings = HuggingFaceEmbeddings(
            model_name="thenlper/gte-large",
            model_kwargs={'device': 'cuda'}
        )
        vector_db = FAISS.load_local(
            r"P:/college stuffs/mini project/Agri-Hub - Copy/datas/faiss/newweb-data/",
            hfembeddings,
            allow_dangerous_deserialization=True
        )

        # Retrieval Chain using Ollama
        retrieval_qa_chain = RetrievalQA.from_chain_type(
            llm=llm,  # Pass the ChatOllama instance instead of a lambda function
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={'k': 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": custom_prompt_template}
        )

        prompt = {'query': user_input}
        model_out = retrieval_qa_chain(prompt)
        answer = model_out['result']
        return answer
    

    elif type_of_llm=='3':
        # database administrator
        if category == "animals_details":
            context = "create table animals_details(cattlename varchar(30), quantity integer(5));"
        elif category == "cattle":
            context = "create table cattle(name varchar(50), sellername varchar(50), price integer(10), quantity integer(10), locality varchar(100));"
        elif category == "details":
            context = "create table details(acre integer(30), current_crop varchar(30), soil_type varchar(30), fertilizer_name varchar(100), fertilizer_company varchar(100), equipments_name varchar(100), equipments_quantity integer(5), fertilizer_type varchar(100), labour_used integer(5), seed varchar(30));"
        elif category == "fertilizer":
            context = "create table fertilizer(name varchar(50), sellername varchar(50), usedfor varchar(60), quantity integer(10), price integer(10));"
        elif category == "financial":
            context = "create table financial(loanid varchar(20), userid varchar(20), loantype varchar(30), loanamount integer(10), interestrate varchar(10), loanterm varchar(30), applicationdate varchar(20), approvaldate varchar(20), loanstatus varchar(30), repaymentschedule varchar(20), expirationdate varchar(20), policystatus varchar(30), insurancetype varchar(60), coverageamount integer(10), policyterm varchar(30), policyid varchar(20), issuancedate varchar(20), coveragedetails varchar(60));"
        elif category == "insurance":
            context = "create table insurance(insurancetype varchar(60), insurancepolicyname varchar(100), duration varchar(30), companyname varchar(50), amount varchar(30));"
        elif category == "loan":
            context = "create table loan(loanname varchar(50), loantype varchar(50), interestrate varchar(30), bankname varchar(50), duration varchar(30));"
        elif category == "machinery":
            context = "create table machinery(name varchar(50), sellername varchar(50), price integer(10), quantity integer(10));"
        elif category == "manufacturer":
            context = "create table manufacturer(name varchar(100), manufacturer_id varchar(10), mobile_number integer(10), company_name varchar(100), email varchar(30), password varchar(20), type varchar(30));"
        elif category == "personal_details":
            context = "create table personal_details(name varchar(50), email varchar(20), address varchar(60), age integer(5), state varchar(20), pincode integer(10), mobilenumber integer(20));"
        elif category == "purchase_history":
            context = "create table purchase_history(product varchar(30), price integer(10), quantity integer(5), dateofpurchase varchar(20), insurancepolicyname varchar(60), insuranceduration varchar(20), insuranceissuancedate varchar(20), insuranceamount integer(10), loanname varchar(60), loanamount integer(10), loanduration varchar(20), loanissuancedate varchar(20));"
        elif category == "rental":
            context = "create table rental(name varchar(50), price integer(10), sellername varchar(50));"
        elif category == "seed":
            context = "create table seed(name varchar(50), type varchar(20), sellername varchar(50), quantity integer(10), price integer(10));"
        elif category == "selling":
            context = "create table selling(name varchar(50), EmailID varchar(20), contact_number integer(20), locality_address varchar(100), product_name varchar(50), product_quantity integer(20), unique_id varchar(20), price integer(10), password varchar(20), prodcut_type varchar(30));"
        else:
            pass


        model_id = "siddharth-magesh/Tiny_Lllama-AgriDB"
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            device_map = "cpu"
        )
        tokenizer = AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        tokenizer.pad_token = tokenizer.eos_token
        pipe = pipeline(
            "text-generation",
            model = model,
            tokenizer = tokenizer,
        )
        llm = HuggingFacePipeline(
            pipeline = pipe,
            pipeline_kwargs={
                "temperature": 0.3,
                "max_new_tokens": 16,
                "min_length": 8,  # Ensure a minimum length
                "do_sample": True,
                "num_beams": 5,
                "repetition_penalty": 2.0,  # Penalize repetition
                "no_repeat_ngram_size": 3,   # Use beam search for better long outputs
            }
        )
        PROMPT_TEMPLATE = """\
        <|im_start|>user
        Given the context, generate an SQL query for the following question
        context:{context}
        question:{question}
        <|im_end|>
        <|im_start|>assistant
        """
        prompt = PromptTemplate(template=PROMPT_TEMPLATE,input_variables=["context","question"])
        llm_chain = LLMChain(prompt=prompt, llm=llm)

        answer = llm_chain.run(context=context,question=user_input)
        return answer
        

    elif type_of_llm=='4':
        #general chatbot

        llm = HuggingFacePipeline.from_model_id(
    model_id="siddharth-magesh/Tiny-Llama-Agri-Bot",
    task="text-generation",
    pipeline_kwargs={
                "temperature": 0.3,
                "max_new_tokens": 256,
                "min_length": 32,  # Ensure a minimum length
                "do_sample": True,
                "num_beams": 5,
                "repetition_penalty": 2.0,  # Penalize repetition
                "no_repeat_ngram_size": 3,   # Use beam search for better long outputs
            },
            device = 0,
        )
        template = """Question: {question} ###Answer: """
        prompt = PromptTemplate(template=template, input_variables=["question"])
        llm_chain = LLMChain(prompt=prompt, llm=llm)
        x = llm_chain.run({"question": user_input})


        if "###Answer:" in x:
            x = x.split("###Answer:")[1].strip()

# Keep only the first complete sentence
        answer = x.split(".")[0] + "."

        return answer


def signup_mongo(name, mobile_number, password, address, gender, age, dateofbirth, email, blood_group, unique_id, state, country, type):
    if type=="farmer":
        collection = db['farmer_details'] 
    else:
        collection=db["buyer_details"]

    existing_user = collection.find_one({"mobile_number": mobile_number})
    
    if existing_user:
        return {"status": "error", "message": "Mobile number already registered!"}
    
    user_data = {
        "name": name,
        "mobile_number": mobile_number,
        "password": password,
        "address": address,
        "gender": gender,
        "age": age,
        "dateofbirth": dateofbirth,
        "email": email,
        "blood_group": blood_group,
        "unique_id": unique_id,
        "state": state,
        "country": country
    }
    try:
        collection.insert_one(user_data)  
        print("Signup successful!")
    except Exception as e:
        print(f"Error during signup: {e}")



def compute_plan_agri(landMeasurements, budget, machinery, labours, soilType, irrigationMethod, storageFacilities):
    prompt = f"""
    You are an agricultural AI assistant. Based on the following details, generate a detailed agricultural work plan:

    - **Land Measurements:** {landMeasurements} in acres
    - **Budget:** {budget} in ruppees
    - **Machinery Available:** {machinery}
    - **Number of Labours:** {labours}
    - **Soil Type:** {soilType}
    - **Irrigation Method:** {irrigationMethod}
    - **Storage Facilities:** {storageFacilities}

    Provide a structured work plan, including crop selection, timeline, resource allocation, and best practices.
    """

    response = ollama.chat(model="llama3", messages=[{"role": "user", "content": prompt}])

    text= response["message"]["content"]
    cleaned_text = re.sub(r'\*+', '', text)  # Remove all occurrences of "*"
    return cleaned_text.strip()

def apple_count(video_path):
    model = YOLO(r'yolo\appledetection\best.pt')

    class_name=['Apple']
    video_path_out = '{}_out.mp4'.format(video_path)
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    H, W, _ = frame.shape
    out = cv2.VideoWriter(video_path_out, cv2.VideoWriter_fourcc(*'MP4V'), int(cap.get(cv2.CAP_PROP_FPS)), (W, H))

    threshold = 0.5
    max_apple_count = 0

    while ret:
        results = model(frame)[0]
        apple_count = 0

        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result

            if score > threshold:
                if int(class_id) == 0:  
                    apple_count += 1
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                cv2.putText(frame, results.names[int(class_id)].upper(), (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)

        if apple_count > max_apple_count:
            max_apple_count = apple_count

        # Display apple count on the frame (optional)
        cv2.putText(frame, f'Apples: {apple_count}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3, cv2.LINE_AA)

        # Write the frame with bounding boxes and apple count
        out.write(frame)
        ret, frame = cap.read()
    
    out.release()
    cv2.destroyAllWindows()
    return(max_apple_count)


UPLOAD_FOLDER = "static/uploads"
# Perform inference
def leaf_disease_detection(image_path):
    class_names = [
        'Hawar_Daun', 'Virus_Kuning_Keriting', 'Hangus_Daun',
        'Defisiensi_Kalsium', 'Bercak_Daun', 'Yellow_Vein_Mosaic_Virus'
    ]

    model = YOLO(r"yolo\plantdiseasedetection\best.pt")
    img = cv2.imread(image_path)
    
    if img is None:
        return None, None  # Handle case where image is not read properly

    results = model(img)
    detected_diseases = []  # Store all detected diseases

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy() if result.boxes is not None else []
        class_ids = result.boxes.cls.cpu().numpy().astype(int) if result.boxes is not None else []
        confidences = result.boxes.conf.cpu().numpy() if result.boxes is not None else []

        for box, class_id, confidence in zip(boxes, class_ids, confidences):
            label = f"{class_names[class_id]} {confidence:.2f}"
            detected_diseases.append(label)

            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    output_path = os.path.join(UPLOAD_FOLDER, "result_leaf.png")
    cv2.imwrite(output_path, img)

    return detected_diseases if detected_diseases else ["No disease detected"], output_path


def weed_detection(image_path):
    class_names = [
        "Carpetweeds", "Crabgrass", "Eclipta", "Goosegrass", "Morningglory",
        "Nutsedge", "Palmeramaranth", "Pricklysida", "Purslane", "Ragweed",
        "Sicklepod", "Spottedspurge", "Spurredanoda", "Swinecress", "Waterhemp"
    ]

    model = YOLO(r"yolo\weeddetection\last.pt")
    img = cv2.imread(image_path)
    results = model(img)

    if not results:
        return None, None

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)
        confidences = result.boxes.conf.cpu().numpy()

        for box, class_id, confidence in zip(boxes, class_ids, confidences):
            label = f"{class_names[class_id]} {confidence:.2f}"
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Save the processed image
    output_path = os.path.join(UPLOAD_FOLDER, "result_weed.png")
    cv2.imwrite(output_path, img)

    return class_names[class_id], output_path

def fetch_store_documents():
    collection = db['store']
    documents = collection.find()
    return list(documents)


def scrape_agriculture_news( ):
    # MongoDB Connection
    max_pages=5
    url="https://economictimes.indiatimes.com/news/economy/agriculture?from=mdr"
    client = MongoClient("mongodb://localhost:27017/")  # Update if needed
    db = client.agribot  # Database: agribot
    collection = db.news  # Collection: news

    # Delete existing news collection before inserting fresh data
    collection.drop()
    print("Old news collection deleted. Starting fresh scrape...")

    page = 1
    while page <= max_pages:
        print(f"Fetching page {page}...")

        # Fetch the webpage content
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("Failed to fetch the webpage")
            break

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all news articles in "eachStory" divs
        articles = soup.find_all('div', class_='eachStory')

        for article in articles:
            # Extract Article URL (from any <a> tag inside "eachStory")
            anchor_tag = article.find('a')
            article_url = anchor_tag['href'] if anchor_tag and anchor_tag.has_attr('href') else None
            if article_url and not article_url.startswith("http"):
                article_url = "https://economictimes.indiatimes.com" + article_url

            # Extract Image URL (from <span class="imgContainer"> > <img>)
            img_tag = article.find('span', class_='imgContainer')
            img_url = img_tag.find('img')['src'] if img_tag and img_tag.find('img') else None

            # Extract Title (from <h3> tag)
            title_tag = article.find('h3')
            title = title_tag.text.strip() if title_tag else None

            # Extract Published Date (from <time> tag)
            time_tag = article.find('time')
            published_date = time_tag.text.strip() if time_tag else None

            # Extract Description (from <p> tag)
            description_tag = article.find('p')
            description = description_tag.text.strip() if description_tag else None

            # Create a document for MongoDB
            news_document = {
                "Article URL": article_url,
                "Image URL": img_url,
                "Title": title,
                "Published Date": published_date,
                "Description": description
            }

            # Insert into MongoDB
            collection.insert_one(news_document)
            print(f"Inserted: {title}")

        # Check for pagination (Modify if there's a "Load More" button)
        next_page_link = soup.find('a', class_='next')  # Adjust class name if different
        if next_page_link and next_page_link.has_attr('href'):
            url = "https://economictimes.indiatimes.com" + next_page_link['href']
        else:
            break  # Stop if no more pages

        page += 1  # Increment page count



def get_weather(city):
    API_KEY = "sk-live-cBqopiU5Z6xpwEFdYmz60fRzfqGong7ZKfevGYHp"
    BASE_URL = "https://weather.indianapi.in/india/weather"
    url = f"{BASE_URL}?city={city}"
    headers = {"x-api-key": API_KEY}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None