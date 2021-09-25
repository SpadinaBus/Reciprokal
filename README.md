# SpadinaBus Reciprokal

The purpose of this project is to construct a cloud-oriented offer serving engine that is highly available, scalable, configurable and maintainable. An endpoint must be exposed for applications and websites to integrate with to retrieve offers for logged-in customers.

* Offers are assigned to customers using other marketing software that produces an offer-customer allowlist CSV file. This allowlist maps an offer_id to a customer_id along with a score used to prioritize the best offers for each customer. This CSV is loaded into a highly available datastore (AWS DynamoDB) for querying.
* Offers are selected based on score and various configurations defining limits on viewing of offers by a customer. When a best offer is selected, a view is logged for it to the offer datastore.
* The offer data is then returned to the client who will present the best offer based on the offer_id.

For full project documentation, see: `INSERT LINK TO DOCS PDF HERE`

## Contents of Repository
* 2 python lambda functions
  * `get_offer_lambda.py` endpoint handler to retrieve offers for a logged-in customer.
  * `upload_offer_lambda.py` s3 bucket update handler to upload new offer allowlist CSVs to Dynamo.
* Config files used in deploying this app (IAM policies, sample offers allowlist CSV, sample get_offer_lambda config)
* Notes such as helpful CLI commands and examples responses/structures returned by Dynamo and Lambda
* UML source diagrams (in `.uxf` format for [UMLet](https://www.umlet.com/))
* Code for an example demo website that integrates with Reciprokal and AWS Cognito
