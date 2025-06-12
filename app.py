from flask import Flask, jsonify,send_file
import pandas as pd
from flask import Flask, request, Response
import csv
import io
from flask_cors import CORS
import requests
import csv
import os
from dotenv import load_dotenv
import json
import base64
import logging
import time
from werkzeug.utils import secure_filename
from pathlib import Path

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
CORS(app) 

load_dotenv(dotenv_path=Path('.') / '.env')

SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
API_VERSION  = os.getenv('API_VERSION')

PRODUCTS_FILE_PATH = "products.json" 
def get_headers():
    return {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
@app.route('/generate-csv', methods=['GET'])
def generate_csv():
    phone_numbers= [ "9214822829",
        "7439436150",
        "9993175757",
        "9541778723",
        "8949465007",
        "8630360267",
        "9987465997",
        "8287867067",
        "9513092752",
        "9443739089",
        "8107912345",
        "7888372617",
        "8112206203",
        "7416938968",
        "9451296645",
        "9680867274",
        "9311470360",
        "6290521364",
        "9037197133",
        "7404716683",
        "9477932897",
        "8179639063",
        "6381739458",
        "6289248224",
        "6352798608",
        "6376530371",
        "7003013732",
        "7006412289",
        "7017882190",
        "7218583867",
        "7221988145",
        "7278494145",
        "7424872880",
        "7428577347",
        "7477347872",
        "7507303081",
        "7585893871",
        "7723009768",
        "7837775944",
        "7852090414",
        "7887674100",
        "7899602018",
        "7907386654",
        "7982720185",
        "8004045932",
        "8053099890",
        "8086161857",
        "8113043956",
        "8124459864",
        "8155921922",
        "8169494269",
        "8310469542",
        "8696368767",
        "8716821440",
        "8828044444",
        "8839520123",
        "8860663661",
        "8866336145",
        "8871740752",
        "8928468529",
        "9088396994",
        "9136866636",
        "9157808878",
        "9318404334",
        "9339124545",
        "9359419256",
        "9428995557",
        "9431016239",
        "9439653055",
        "9496597304",
        "9536873737",
        "9539173092",
        "9543082248",
        "9603563863",
        "9631510164",
        "9664470918",
        "9668145575",
        "9685682619",
        "9696595558",
        "9700608928",
        "9711184067",
        "9755750867",
        "9764573557",
        "9829186893",
        "9830968510",
        "9834375178",
        "9849792562",
        "9871279504",
        "9873046266",
        "9873688986",
        "9877047443",
        "9881162375",
        "9892521953",
        "9901207984",
        "9912636666",
        "9946180113",
        "9997906607"
    ]

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Writing the headers
    writer.writerow(["Name", "Phone"])

    # Writing phone numbers with "Customer X" names
    for i, phone in enumerate(phone_numbers, start=1):
        writer.writerow([f"Customer {i}", phone])

    output.seek(0)

    # Return as a downloadable CSV file
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=customers.csv"}
    )
# @app.route("/get_all_product_ids", methods=["GET"])
# def get_all_product_ids():
#     all_products = []
#     headers = {"X-Shopify-Access-Token": ACCESS_TOKEN}
#     api_url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2025-01/products.json?fields=id,handle&limit=1"
#     response = requests.get(api_url, headers=headers, timeout=10)

#     if response.status_code != 200:
#         return []
#     else:
#         response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
#         data = response.json()
#         products = data.get("products", [])
#         all_products.extend(products)
#     return jsonify({"products": all_products}), 200


# --- MODIFIED: get_product_ids to handle pagination and fetch all products ---
@app.route("/get_all_product_ids", methods=["GET"])
def get_all_product_ids():
    all_products = []
    next_page_info = None # For cursor-based pagination

    while True:
        url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{API_VERSION}/products.json?fields=id,handle&limit=250" # Fetch max limit
        if next_page_info:
            url += f"&page_info={next_page_info}"

        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": ACCESS_TOKEN
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()
            products = data.get("products", [])
            all_products.extend(products)

            # Check for the 'Link' header to find the next page
            link_header = response.headers.get("Link")
            next_page_info = None # Reset for current iteration
            if link_header:
                links = link_header.split(', ')
                for link in links:
                    if 'rel="next"' in link:
                        # Extract page_info from the URL in the link header
                        # Example: <https://myshop.myshopify.com/admin/api/.../products.json?page_info=abcdef&limit=250>; rel="next"
                        import re
                        match = re.search(r'page_info=([^&>]+)', link)
                        if match:
                            next_page_info = match.group(1)
                            break # Found the next page_info, exit inner loop

            if not next_page_info or not products: # No more pages or no products returned
                break

            # Add a small delay to respect Shopify API rate limits (e.g., 0.5 seconds)
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching product IDs: {e}")
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

    return jsonify({"products": all_products}), 200
@app.route("/", methods=["GET"])
def get_home():
    return "<h1>Growth Studioz</h1>", 200 
@app.route("/get_variant_ids/<product_id>", methods=["GET"])
def get_variant_ids(product_id):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{API_VERSION}/products/{product_id}/variants.json?fields=id,title,option1,option2,option3,"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# --- Existing: get_variant_metafields ---
@app.route("/get_variant_metafields/<variant_id>", methods=["GET"])
def get_variant_metafields(variant_id):
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{API_VERSION}/variants/{variant_id}/metafields.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate_shopify_data_excel", methods=["GET"])
def generate_shopify_data_excel():
    excel_file_path = "shopify_product_data_incremental-8-variants.xlsx" # New file name for clarity
    all_new_product_data = [] # To store data for new products

    # Define which metafield keys should be split by newline
    MULTI_VALUE_METAFIELD_KEYS = ["diamond_count", "diamond_shape","diamond_weight"] # Customize this list

    existing_df = pd.DataFrame()
    existing_product_ids = set()

    # 1. Check if the Excel file already exists and load it
    if os.path.exists(excel_file_path):
        try:
            existing_df = pd.read_excel(excel_file_path)
            # Ensure 'product_id' column exists before creating the set
            if 'product_id' in existing_df.columns:
                existing_product_ids = set(existing_df['product_id'].astype(str).tolist()) # Convert to string for consistent comparison
            print(f"Loaded existing data from {excel_file_path}. Found {len(existing_product_ids)} existing product IDs.")
        except Exception as e:
            print(f"Warning: Could not read existing Excel file {excel_file_path}. Starting fresh. Error: {e}")
            existing_df = pd.DataFrame() # Reset in case of error

    # 2. Get all product IDs and handles (using the new paginated endpoint)
    # IMPORTANT: Ensure your Shopify API key has permissions for product read access
    product_ids_response = requests.get(f"http://127.0.0.1:5000/get_all_product_ids")
    if product_ids_response.status_code != 200:
        return jsonify({"error": f"Failed to fetch product IDs and handles: {product_ids_response.json().get('error', 'Unknown error')}"}), 500
    products_info = product_ids_response.json().get("products", [])
    print(f"Fetched {len(products_info)} products from Shopify.")

    # 3. Iterate through product info, skipping existing products
    products_processed_count = 0
    products_skipped_count = 0

    for product_info in products_info:
        product_id = product_info["id"]
        product_handle = product_info.get("handle", "")

        # Skip if product_id already exists in the sheet
        if str(product_id) in existing_product_ids: # Convert product_id to string for consistent comparison
            products_skipped_count += 1
            continue

        print(f"Processing new product: {product_id} ({product_handle})")
        products_processed_count += 1

        variant_ids_response = requests.get(f"http://127.0.0.1:5000/get_variant_ids/{product_id}")
        if variant_ids_response.status_code != 200:
            print(f"Warning: Failed to fetch variant IDs for product {product_id}: {variant_ids_response.json().get('error', 'Unknown error')}")
            continue
        variant_ids_data = variant_ids_response.json()
        variants = variant_ids_data.get("variants", [])

        # Filter for first and last variants to fetch metafields
        processed_combinations = set()
        variants_to_process = []

        # Assuming 'variants' contains all 24 of your variant combinations
        for variant in variants:
            # Create a tuple of the option values to use as a unique key
            # This key represents a unique combination of Option1 and Option3
            combination_key = (variant.get("option1"), variant.get("option2"), variant.get("option3"))

            # If we haven't seen this combination before, process it
            if combination_key not in processed_combinations:
                variants_to_process.append(variant)
                # Add the key to our set so we don't process this combination again
                processed_combinations.add(combination_key)

            # Since you expect 8 unique combinations (2 Option1 * 4 Option3),
            # we can stop once we've found them all.

        # Now, you can proceed with your existing logic
        for variant in variants_to_process:
            variant_id = variant["id"]
            variant_title = variant["title"]
            variant_option = variant["option1"]
            variant_option2 = variant["option2"]
            variant_option3 = variant["option3"]

            metafields_response = requests.get(f"http://127.0.0.1:5000/get_variant_metafields/{variant_id}")
            if metafields_response.status_code != 200:
                print(f"Warning: Failed to fetch metafields for variant {variant_id}: {metafields_response.json().get('error', 'Unknown error')}")
                continue
            metafields_data = metafields_response.json()
            metafields = metafields_data.get("metafields", [])

            row_data = {
                "product_id": product_id,
                "product_handle": product_handle,
                "variant_id": variant_id,
                "variant_title": variant_title,
                "variant_option": variant_option,
                "variant_option2": variant_option2,
                "variant_option3": variant_option3 # You may want to include Option3 as well
            }

            # Process metafields, splitting multi-value ones
# --- MODIFIED LOGIC FOR SPLITTING METAFIELDS ---
            for metafield in metafields:
                key = metafield["key"]
                value = metafield["value"]

                # Check if it's a multi-value key and the value is a string
                if key in MULTI_VALUE_METAFIELD_KEYS and isinstance(value, str):
                    # 1. Replace all newlines with single spaces
                    normalized_value = value.replace('\n', ' ')
                    
                    # 2. Split by space and filter out any empty strings (from multiple spaces)
                    split_values = [s.strip() for s in normalized_value.split(' ') if s.strip()]

                    if split_values: # If there are actual values after splitting
                        for i, split_val in enumerate(split_values):
                            row_data[f"{key}_{i+1}"] = split_val # Add to row_data with indexed column name
                    else: # If the original value was just spaces or empty, add an empty string
                        row_data[key] = ""
                else:
                    # For regular metafields or non-string values, just assign directly
                    row_data[key] = value
            # --- END MODIFIED LOGIC ---

            all_new_product_data.append(row_data)

            # Optional: Add a small delay to respect Shopify API rate limits (e.g., 0.1 seconds per variant metafield call)
            # time.sleep(0.1)

    print(f"Finished processing. Processed {products_processed_count} new products, skipped {products_skipped_count} existing products.")

    if not all_new_product_data and existing_df.empty:
        return jsonify({"message": "No new data found to add to Excel, and no existing file."}), 200
    elif not all_new_product_data and not existing_df.empty:
        return jsonify({"message": "No new data found to add. Excel file remains unchanged."}), 200


    # 4. Create a DataFrame for new data and combine with existing
    new_df = pd.DataFrame(all_new_product_data)

    if not existing_df.empty:
        # Concatenate existing data with new data
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    # 5. Reorder columns for better readability (only if new data was added or existing was loaded)
    if not combined_df.empty:
        desired_order = ["product_id", "product_handle", "variant_id", "variant_title", "variant_option"]
        existing_cols = combined_df.columns.tolist()

        new_cols = []
        for col in desired_order:
            if col in existing_cols:
                new_cols.append(col)
                existing_cols.remove(col)

        new_cols.extend(sorted(existing_cols)) # Add remaining metafield columns sorted
        combined_df = combined_df[new_cols]

    # 6. Save to Excel (overwriting the existing file or creating a new one)
    try:
        if not combined_df.empty:
            combined_df.to_excel(excel_file_path, index=False)
            print(f"Successfully saved updated data to {excel_file_path}")
            return send_file(excel_file_path, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            return jsonify({"message": "No data to save to Excel."}), 200 # Should not happen if previous checks work
    except Exception as e:
        return jsonify({"error": f"Failed to generate Excel file: {str(e)}"}), 500


@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        data = read_csv(file_path)
        return jsonify(data)
@app.route("/update_variant/<variant_id>", methods=["PUT"])
def update_variant(variant_id):
    data = request.json
    variant_data = data.get("variant")
    
    if not variant_data or "id" not in variant_data or "price" not in variant_data:
        return jsonify({"error": "Invalid request body"}), 400
    
    url = f"{SHOPIFY_STORE_URL}{variant_id}.json"
    response = requests.put(url, json={"variant": variant_data}, headers=get_headers())
    
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to update variant", "details": response.text}), response.status_code

@app.route("/upload-products", methods=["POST"])
def upload_products():
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }

    api_url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2025-01/products.json"

    # Check if file exists
    if not os.path.exists(PRODUCTS_FILE_PATH):
        return jsonify({"error": "File 'products.json' not found."}), 400

    # Read the JSON file
    try:
        with open(PRODUCTS_FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format in 'products.json'."}), 400

    if not data or "products" not in data:
        return jsonify({"error": "'products' key missing in JSON file."}), 400

    products = data["products"]
    responses = []

    for product in products:
        # Create product in Shopify
        payload = {"product": product}
        resp = requests.post(api_url, headers=headers, json=payload, timeout=10)

        if resp.status_code != 201:
            responses.append({
                "title": product["title"],
                "status": "failed",
                "error": resp.text
            })
            continue

        product_data = resp.json().get("product", {})
        print(resp.json())
        product_id = product_data.get("id")
        
        # Extract variant IDs
        variant_map = {v["option1"]: v["id"] for v in product_data.get("variants", [])}

        # Upload images for variants that have an 'img' field
        for variant in product["variants"]:
            if "img" in variant:
                image_path = variant["img"]  # Path of the image file
                encoded_image = encode_image(image_path)

                if encoded_image:
                    variant_id = variant_map.get(variant["option1"])
                    
                    image_payload = {
                        "image": {
                            "variant_ids": [variant_id],
                            "attachment": encoded_image,
                            "filename": os.path.basename(image_path)
                        }
                    }
                    print(variant_id)
                    image_api_url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2025-01/products/{product_id}/images.json"
                    img_resp = requests.post(image_api_url, headers=headers, json=image_payload, timeout=10)

                    if img_resp.status_code != 200:
                        responses.append({
                            "title": product["title"],
                            "variant": variant["option1"],
                            "image_status": "failed",
                            "error": img_resp.text
                        })
                    else:
                        responses.append({
                            "title": product["title"],
                            "variant": variant["option1"],
                            "image_status": "success"
                        })

    return jsonify({"message": "Bulk product upload completed", "results": responses}), 200


CSV_FILE_PATH = "processed_products.csv"
IMAGE_PATHS = ["1.png","2.png","3.png","4.png"]
def encode_image(image_path):
    """Encodes an image in base64 format for Shopify API."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
    except FileNotFoundError:
        return None

def get_existing_product_ids():
    if not os.path.exists(CSV_FILE_PATH):
        return set()
    with open(CSV_FILE_PATH, "r", newline="", encoding="utf-8") as file:
        return {row[0] for row in csv.reader(file)}

def save_product_id(product_id):
    with open(CSV_FILE_PATH, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([product_id])

def get_all_products():
    headers = {"X-Shopify-Access-Token": ACCESS_TOKEN}
    api_url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2025-01/products.json?limit=250"
    response = requests.get(api_url, headers=headers, timeout=10)
    if response.status_code != 200:
        return []
    return response.json().get("products", [])

# def encode_image(image_path):
#     if not os.path.exists(image_path):
#         return None
#     with open(image_path, "rb") as img_file:
#         return img_file.read().encode("base64").decode("utf-8")
    
def upload_images_to_product(product_id):
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }
    api_url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/2025-01/products/{product_id}/images.json"
    
    for image_path in IMAGE_PATHS:
        encoded_image = encode_image(image_path)
        if not encoded_image:
            continue
        
        payload = {
            "image": {
                "attachment": encoded_image,
                "filename": os.path.basename(image_path)
            }
        }
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        if response.status_code != 201:
            print(f"Failed to upload image for product {product_id}: {response.text}")
CATEGORIES_MAPPING = ["Earrings", "Necklaces", "Rings", "Bracelets", "Dubai Diaries"]

@app.route("/upload-images", methods=["POST"])
def product_add_images():
    existing_product_ids = get_existing_product_ids()
    processed_products = []

    products = get_all_products()  # Fetch all products

    for product in products:
        product_type = product.get("product_type", "").strip().lower()  # Normalize to lowercase
        product_id = str(product.get("id"))

        # Determine category dynamically
        category = next((cat for cat in CATEGORIES_MAPPING if cat.lower() in product_type), None)

        if not category:
            continue  # Skip if no matching category found

        if product_id in existing_product_ids:
            print(f"Skipping product {product_id}, already processed.")
            continue

        upload_images_to_product(product_id)
        save_product_id(product_id)
        print(f"Uploaded images for product ID: {product_id} in category {category}")
        processed_products.append({"product_id": product_id, "category": category})

    return jsonify({"message": "Image upload completed", "processed_products": processed_products}), 200

if __name__ == '__main__':
    app.run(debug=False)
