@monitor.py:
The changes I made:

Added proper JSON handling:
Now we check if the input is a string and parse it using json.loads()
Added error handling for JSON parsing failures
Added more logging:
Log the actual response we're monitoring
Added error logging for JSON parsing and general errors
Made the code more robust:
Handles both string and dictionary inputs
Better error handling to prevent crashes
Now when you run the application and get an invalid token response, you should see proper logging in the console showing:

The actual response being monitored
The updated list of stores with invalid tokens (if any are found)

ok, nice, it is working!
INFO 2025-01-25 17:51:26,508 get_message 94915 6126186496 Getting message for type=Whatsapp, tag=Botox, counter=0
INFO 2025-01-25 17:51:26,510 get_message 94915 6126186496 Found message id=3254 for Botox
INFO 2025-01-25 17:51:26,510 contact 94915 6126186496 Basic variables for contact 58632: {'[nome]': '💕', '[unidade]': 'Central'}
INFO 2025-01-25 17:51:26,511 queue_processor 94915 6159839232 Attempt 1 of 3
INFO 2025-01-25 17:51:26,512 send_file_message 94915 6176665600 Payload: {
  "api_token": "11988446710",
  "phone": "9999936700",
  "message": "Hello 0 message Botox",
  "preview_url": true
}
INFO 2025-01-25 17:51:26,512 send_file_message 94915 6176665600 ...
/Users/luisfaria/Desktop/sEngineer/konquest/venv/lib/python3.10/site-packages/urllib3/connectionpool.py:1099: InsecureRequestWarning: Unverified HTTPS request is being made to host 'apinew.socialhub.pro'. Adding certificate verification is strongly advised. See: https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings
  warnings.warn(
INFO 2025-01-25 17:51:29,527 monitor 94915 6176665600 Monitoring response for phone 9999936700: {'success': False, 'message': 'invalid api_token!'}
INFO 2025-01-25 17:51:29,527 monitor 94915 6176665600 Stores with invalid token: [{'phone': '9999936702', 'token': '11988446710'}, {'phone': '9999936701', 'token': '11988446710'}, {'phone': '9999936700', 'token': '11988446710'}]
ERROR 2025-01-25 17:51:29,527 queue_processor 94915 6159839232 Failed to send message to 9999936700: HTTP 400: {"success":false,"message":"invalid api_token!"}

# Next Steps:
Great! Now we can see the monitoring is working correctly and tracking the invalid tokens. I notice a few things from the logs:

We're successfully detecting invalid tokens
We're maintaining a list of all affected stores
The list is persisting between requests (we can see 3 different phone numbers)
Now that we have this working, would you like to:

1. Adjust the email notification to include all the invalid tokens in a single email rather than sending one per occurrence?
2. Add more details to the logging (like timestamps or which service detected the invalid token)?
3. Add a way to clear the stores_with_invalid_token list after sending notifications?
4. Handle that InsecureRequestWarning that's showing up in the logs?

Update 27/01:
yes, now that we're storing the info from the invalid token stores into a list "stores_with_invalid_token", what if we create a new function to be called and shoot the emai