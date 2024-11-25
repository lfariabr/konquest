# Campaign model
start_time = models.DateTimeField(null=True, blank=True) # I believe this one is not being used, as "Execution time" took its place
execution_time = models.TimeField(default='08:00')  # Default to 8 AM, later we can add time | later we can also allow users to set this
active_days = models.JSONField(default=list, help_text="List of active days (0-6, Monday to Sunday)") # We need to improve it to be a multi select field

Add field  sequential_order
This should be linked to core > models > message > field "counter" (this will feed the 'message' field at TargetList model)
# Example: sequential_order = [0] // this should link to message ID X
# Campaigns should be able to have multiple sequential orders
# sequential_order = models.JSONField(default=list, help_text="List of sequential orders")
Important to note that if:
campaign_type = whatsapp, sequential order = counter (automatic true and number input required)
campaign_type = appointment, sequential order = counter (true/false and number input) and days_interval 

# Core data
userphone = models.ForeignKey(UserPhone, on_delete=models.CASCADE, related_name='campaigns')
user = models.ForeignKey(kUser, on_delete=models.CASCADE)

# TargetList model
No changes, just pointing out that message field will be set up on Campaign model which contains rules

# Queue model
1 - do we really need "contact" field?
2 - I want to be able to ACCESS each target list and see the priority list within them, to see each contact and message that is going to be sent

# OUTPUT:
python setup_target_list_generation.py

Go to the Django admin panel: http://127.0.0.1:8000/admin/messageShooter/queue/
You should see the Queue model with entries showing:
- Target List reference
- Contact information
- Message content
- Status (pending/processing/sent/failed)
- Priority
- Scheduled time

The queue entries are ordered by:
- Priority (highest first)
- Scheduled time
- Creation time

python setup_queue.py
We have successfully moved the target lists to the queue and optimized the admin views to check everything

# Next steps:
1 - Test the queue system to shoot messages validating if counter is going up for Whatsapp campaign. 
Steps should be:
a. create test data
b. run target list generation
c. run queue processing
d. check if messages are being sent, saved on logs and incrementing the counter
e. check if message counter = 1 is being sent
f. check if message counter = 2 is being sent