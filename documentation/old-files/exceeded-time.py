# Check with Samir:
# 1 solução mais força bruta - 1gb de memória
# 2 solução brute force - várias tasks, uma pra cada campanha
# 3 deixar elegante
# travo a fila por causa dos leads. create_leads != send_message_to_lead

"""
WARNING 2025-01-28 14:45:00,036 request 9 138182160583552 Soft time limit (27000s) exceeded for messageShooter.tasks.process_queues[f55f82ee-5367-4327-8aec-3182915bc58c]
WARNING 2025-01-28 14:45:00,038 base 13 138182160583552 f55f82ee-5367-4327-8aec-3182915bc58c has an expiration date in the past (19800.008219s ago).
We assume this is intended and so we have set the expiration date to 0 instead.
According to RabbitMQ's documentation:
"Setting the TTL to 0 causes messages to be expired upon reaching a queue unless they can be delivered to a consumer immediately."
If this was unintended, please check the code which published this task.
Task failed: messageShooter.tasks.process_queues[f55f82ee-5367-4327-8aec-3182915bc58c] - TimeLimitExceeded: TimeLimitExceeded(1800,)
ERROR 2025-01-28 14:45:00,039 request 9 138182160583552 Task handler raised error: TimeLimitExceeded(1800)
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/site-packages/billiard/pool.py", line 684, in on_hard_timeout
    raise TimeLimitExceeded(job._timeout)
billiard.einfo.ExceptionWithTraceback: 
"""

"""
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/site-packages/billiard/pool.py", line 684, in on_hard_timeout
    raise TimeLimitExceeded(job._timeout)
billiard.exceptions.TimeLimitExceeded: TimeLimitExceeded(1800,)
"""

# If we have enough time, talk about VIP client list

# VIP
# 1. Outubro: Reengaged | Separar quem é o alvo
# 2. Appointment -> Contact
# 3. Message1 - contador 