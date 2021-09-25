import json
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
import logging

# NOTE: Set up Dynamo Client
dynamodb = boto3.resource('dynamodb')
offer_whitelist_table_name = 'SET ME'
offer_whitelist_table = dynamodb.Table(offer_whitelist_table_name)

# NOTE: Set up S3 Client
s3 = boto3.resource('s3')
configs_bucket_name = 'SET ME'

## NOTE: Set logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# NOTE: Configs
load_from_s3 = True # NOTE: hardcoded switch

# Default configs below, to be overwritten by config.json if load_from_s3 == TRUE
configs = {
  "offer_exclusion": {
    "views_recency_window": {
      "enabled": True,
      "num_hours": 48,
      "max_views": 6
    },
    "views_all_time": {
      "enabled": True,
      "max_views": 10
    },
    "expired_offers": {
      "enabled": True,
      "max_age_days": 50
    }
  },
  "default_offer": {
      "offer_id": "DefaultOffer"
  }
}

def load_configs():
    global configs
    if load_from_s3 == True:
      config_file = s3.Object(configs_bucket_name, 'config.json')
      configs = json.loads(config_file.get()['Body'].read())

def lambda_handler(event, context):
  username = get_username(event)
  logger.info("USERNAME = " + username) 

  load_configs()
  logger.info("CONFIGS LOADED FROM S3")
  logger.info(configs)

  offers = get_offers(username)
  best_offer = determine_best_offer(offers)
  logger.info("BEST OFFER = " + best_offer.id)

  if best_offer.is_default == False:
    logger.info("LOG CONTACT FOR BEST OFFER")  
    log_best_offer_view(username, best_offer) # NOTE: Only log view for non-default best offer

  offer_json = json.dumps(json_response(best_offer)) # NOTE: Needs to be stringified for Lambda Proxy

  return {
      "statusCode": 200,
      'headers': {
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,GET'
      },
      "body": offer_json
  }

def get_username(event):
  username = event.get("requestContext").get("authorizer").get("claims").get("cognito:username")
  return username

def get_offers(username):
  offers_response = query_dynamo_for_offers(username)

  offers_data = offers_response["Items"]

  final_offers = []
  
  expiration_limit = None
  exclude_expired_offers = configs["offer_exclusion"]["expired_offers"]["enabled"]
  if exclude_expired_offers == True:
    num_days_back = configs["offer_exclusion"]["expired_offers"]["max_age_days"]
    expiration_limit = datetime.now() - timedelta(hours=(num_days_back * 24), minutes=0)

  for offer_data in offers_data:
    filter_out = False
    if exclude_expired_offers == True:
      filter_out = is_offer_expired(offer_data, expiration_limit)
    
    if filter_out == False:
      offer = create_offer_from_data(offer_data)
      if offer != None:
        final_offers.append(offer)

  return final_offers

def is_offer_expired(offer_data, expiration_limit):
  loaded_at_parsed = datetime.strptime(offer_data["LoadedAt"], "%m/%d/%Y, %H:%M:%S")
  return expiration_limit > loaded_at_parsed

def create_offer_from_data(offer_data):
  offerId = offer_data["OfferId"]
  offerScore = offer_data["OfferScore"]
  views = offer_data["OfferViews"]
  rank = 1 # NOTE: hardcode for now, gets set during offer selection after sort by score
  loaded_at = offer_data["LoadedAt"]

  offer = Offer(offerId, int(offerScore), rank, views, loaded_at)

  return offer


def query_dynamo_for_offers(username):
  offers_response = None
  offers_response = offer_whitelist_table.query(
    KeyConditionExpression=Key('CustomerId').eq(username)
  )
  return offers_response


def determine_best_offer(offers_list):
  default_offer_id = configs["default_offer"]["offer_id"]

  if len(offers_list) == 0:
    return generate_default_offer(default_offer_id)

  offers_list.sort(key=lambda x: x.score, reverse=True) # NOTE: sorts in place

  search_for_best_offer = True
  curr_offer_index = -1 # NOTE: increased to 0 for first loop iteration
  max_index = len(offers_list) - 1
  best_offer = None

  while (search_for_best_offer == True and curr_offer_index != max_index):
    curr_offer_index += 1
    best_offer = offers_list[curr_offer_index]

    offer_passed_all_rules = True

    # NOTE: Check views from all time
    all_time_views_exclusion_enabled = configs["offer_exclusion"]["views_all_time"]["enabled"]
    if all_time_views_exclusion_enabled == True:
      max_num_views = configs["offer_exclusion"]["views_all_time"]["max_views"]
      if best_offer.num_views >= max_num_views:
        offer_passed_all_rules = False

    # NOTE: Check Views in time window
    time_window_views_exclusion_enabled = configs["offer_exclusion"]["views_recency_window"]["enabled"]
    if time_window_views_exclusion_enabled == True:
      num_hours = configs["offer_exclusion"]["views_recency_window"]["num_hours"]
      max_num_views = configs["offer_exclusion"]["views_recency_window"]["max_views"]
      curr_datetime = datetime.now()
      time_limit = curr_datetime - timedelta(hours=num_hours, minutes=0)

      offer_num_views_in_window = best_offer.num_views_in_time_window(time_limit)
      if offer_num_views_in_window >= max_num_views:
        offer_passed_all_rules = False

    if offer_passed_all_rules == True:
      search_for_best_offer = False
    else:
      best_offer = None # NOTE: matters in case this iteration is last

  if best_offer == None:
    return generate_default_offer(default_offer_id)
  else:
    # NOTE: Set rank based on index in sorted array
    best_offer.rank = (curr_offer_index + 1)
    # NOTE: increase view count
    best_offer.num_views +=1 # NOTE: We dont query for new value after updating with new view

  return best_offer

def json_response(best_offer):
  # NOTE: follows json api spec
  return {
    "data": [ # NOTE: array of 1 for now
      {
        "id": best_offer.id,
        "type": "Offer",
        "attributes": {
          "score": best_offer.score,
          "rank": best_offer.rank,
          "num_views": best_offer.num_views,
          "is_default_offer": best_offer.is_default
        }
      }
    ]
  }

def log_best_offer_view(username, best_offer):
  view_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
  result = offer_whitelist_table.update_item(
      Key={
          'CustomerId': username,
          'OfferId': best_offer.id
      },
      UpdateExpression="SET OfferViews = list_append(OfferViews, :i)",
      ExpressionAttributeValues={
          ':i': [view_time],
      },
      ReturnValues="UPDATED_NEW"
  )
  return

def generate_default_offer(offer_id):
  offer = Offer(offer_id, None, None, [], None)
  offer.is_default = True
  return offer

class Offer:
  def __init__(self, id, score, rank, views, loaded_at):
    self.id = id
    self.score = score
    self.rank = rank
    self.views = views
    self.num_views = len(views)
    self.loaded_at = loaded_at
    self.is_default = False

  def num_views_in_time_window(self, time_limit):
    num_views_in_window = 0
    for curr_view_time in self.views:
      curr_view_time_parsed = datetime.strptime(curr_view_time, "%m/%d/%Y, %H:%M:%S")
      if curr_view_time_parsed > time_limit:
        num_views_in_window += 1

    return num_views_in_window
