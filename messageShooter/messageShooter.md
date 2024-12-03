# Goal
Process messages from core>message into queue and send using social hub API according to Campaign Rules

# Details of usage:
- core
-- to get contacts, messages, phone_token
- apiCrm
-- to check if these contacts are leads, appointments or buyers
- apiSocialHub
-- to send messages to contacts
- messageShooter
-- to glue it all together via Scheduler, TargetList and Queue

# What it will serve back to the app
- core
-- message logs with status and sent_at

# Step by step
1. Have contacts, messages, phone_token using setup_test_data
2. Run_scheduler to generate target lists out of campaigns
3. Check it target lists are created and sent to Queue
4. Monitore Queue processing to send messsages
5. Verify that messages are sent on the console log and saved at Core > Message Logs

# Future ideas
- Machine learnign to understand patterns: more messages = more contacts that are appointment or that buy?
- AB testing of message templates, time and frequency
- Allow users to schedule messages like offering Indique Multiplique to clients that were appointments in certain status or interval
- Allow users to create a monthly campaign to send _PROMO_ message to certain types of billcharges, like who bought more than R$ 1000 in a month