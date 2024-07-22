from fastapi import FastAPI, File, UploadFile, Request,Form
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse
import boto3
from botocore.exceptions import NoCredentialsError
from fastapi.templating import Jinja2Templates
import mysql.connector 
import os
from dotenv import load_dotenv
app = FastAPI()

load_dotenv()
# AWS S3 配置
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_BUCKET_NAME = 'myotiss3demo'

# RDS 配置
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_PORT = os.getenv('MYSQL_PORT')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')


connection = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)

templates = Jinja2Templates(directory=".")
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...),message: str = Form(...)):
    try:
        s3_client.upload_fileobj(file.file, AWS_BUCKET_NAME, file.filename)
        cloudfront_url = f"https://d2h11xp6qwlofm.cloudfront.net/{file.filename}"
        file_url = f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
        cursor = connection.cursor()
        query = "INSERT INTO messages (message, image_url) VALUES (%s, %s)"
        cursor.execute(query, (message, cloudfront_url))
        connection.commit()
        cursor.close()
        return RedirectResponse(url="/", status_code=303)
    except NoCredentialsError:
        return {"error": "Credentials not available"}
    
@app.get("/data")
async def get_data():
    try:
        with connection.cursor(dictionary=True) as cursor:
            query = "SELECT message,image_url FROM messages"
            cursor.execute(query)
            result = cursor.fetchall()
        return JSONResponse(content={"data": result})
    except mysql.connector.Error as err:
        return JSONResponse(content={"error": str(err)}, status_code=500)
# @app.get("/images")
# async def get_images():
#     image_urls = get_image_urls_from_s3(AWS_BUCKET_NAME)
#     return JSONResponse(content=image_urls)

# def get_image_urls_from_s3(bucket_name):
#     """獲取S3存儲桶中的所有圖片URL"""
#     response = s3_client.list_objects_v2(Bucket=bucket_name)
#     print(response)
#     image_urls = []
#     for obj in response.get('Contents', []):
#         file_url = f"https://{bucket_name}.s3.amazonaws.com/{obj['Key']}"
#         image_urls.append(file_url)
#     return image_urls