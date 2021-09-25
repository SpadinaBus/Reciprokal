import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
import logging
import csv

# Set up Dynamo Client
dynamodb = boto3.resource('dynamodb')
offer_whitelist_table_name = 'SET ME'
offer_whitelist_table = dynamodb.Table(offer_whitelist_table_name)

# Set up S3 Client
s3 = boto3.resource('s3')
whitelist_bucket_name = 'SET ME'

# Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    sourceKey = event['Records'][0]['s3']['object']['key'] # NOTE: Example: "Customer-Offer-Whitelist-aug-11-2020.csv"
    whitelist_file = s3.Object(whitelist_bucket_name, sourceKey)
    whitelist = whitelist_file.get()['Body'].read().decode('utf-8').splitlines()

    lines = csv.reader(whitelist)
    headers = next(lines)
    for line in lines:
        customer_id = line[0]
        offer_id = line[1]
        score = line[2]
        add_item_to_table(customer_id, offer_id, score)
        
def add_item_to_table(customer_id, offer_id, score):
    item = {
        "CustomerId": customer_id,
        "LoadedAt": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        "OfferId": offer_id,
        "OfferScore": score,
        "OfferViews": [] # NOTE: init as empty
    }
    offer_whitelist_table.put_item(Item=item)
