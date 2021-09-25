
// LOGIN USING AWS CLI TO COGNITO
// REQUEST
aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id <client id> --auth-parameters USERNAME=tom@spadinabus.com,PASSWORD=<password>--region us-east-1

// RESULT (USE IDTOKEN FOR COGNITO AUTH, NOT ACCESS TOKEN, NEED COGNITO RESOURCE SERVER FOR THAT)
{
    "AuthenticationResult": {
        "ExpiresIn": 3600, 
        "IdToken": "abcd1234", 
        "RefreshToken": "abcd1234", 
        "TokenType": "Bearer", 
        "AccessToken": "abcd1234"
    }, 
    "ChallengeParameters": {}
}

// RESPOND TO AUTH CHALLENGE (UPDATE EMAIL FROM DEFAULT PROVIDED)
// REQUEST
aws cognito-idp respond-to-auth-challenge --client-id <client id> --challenge-name NEW_PASSWORD_REQUIRED --challenge-responses USERNAME=tom@spadinabus.com,NEW_PASSWORD=<password> --region us-east-1 --session <session id

//RESPONSE
SAME AS WITH LOGIN USING AWS CLI TO COGNITO

// UPDATE PASSWORD (DIDNT USE)
aws cognito-idp change-password --previous-password <previous password> --proposed-password <new password> --access-token <token>
