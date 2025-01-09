- LeadProcessor
I'll need to create a wroker that will:
1) fetch data from leads from CRM each 1 minute
2) check if these leads are contact or not (very similar to rule of appointment-to-contact). If not, register them as a contact, if yes, move forward
3) then create a target list, 
4) instant process targetlist to queue
5) instant procss queue

since i'm gonna be getting a HUGE volume of leads each minute, i need something very consistent to be able to deal with that. 

# Lead Processing Pipeline
fetch_leads.apply_async() \
    .then(process_contacts.s()) \
    .then(create_target_list.s()) \
    .then(process_target_list.s()) \
    .then(process_queue.s())

# Implementation Strategy:
@shared_task(
    name='crm.fetch_leads',
    rate_limit='60/m',
    acks_late=True,
    retry_backoff=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3}
)
def fetch_leads():
    """Fetch leads from CRM in batches"""
    try:
        # Get timestamp of last fetch
        last_fetch = cache.get('last_lead_fetch')
        
        # Fetch new leads in batches of 1000
        leads = fetch_leads_from_crm(last_fetch, batch_size=1000)
        
        # Update last fetch timestamp
        cache.set('last_lead_fetch', timezone.now().isoformat())
        
        # Split leads into chunks for parallel processing
        lead_chunks = chunk_leads(leads, chunk_size=100)
        
        # Create group of tasks for parallel processing
        return group(process_lead_chunk.s(chunk) for chunk in lead_chunks)()
    except Exception as e:
        logger.error(f"Lead fetch failed: {str(e)}", exc_info=True)
        raise

@shared_task(
    name='crm.process_lead_chunk',
    acks_late=True,
    retry_backoff=True
)
def process_lead_chunk(leads):
    """Process a chunk of leads"""
    contacts = []
    for lead in leads:
        if not is_contact(lead):
            contact = register_as_contact(lead)
            contacts.append(contact)
    return contacts

@shared_task(
    name='crm.create_target_list',
    acks_late=True
)
def create_target_list(contacts):
    """Create target list from processed contacts"""
    if not contacts:
        return None
    
    target_list = TargetList.objects.create(
        name=f"Auto Generated {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        source="CRM Lead Import"
    )
    
    # Bulk create target list entries
    TargetListEntry.objects.bulk_create([
        TargetListEntry(target_list=target_list, contact=contact)
        for contact in contacts
    ])
    
    return target_list.id

@shared_task(
    name='crm.process_target_list',
    acks_late=True
)
def process_target_list(target_list_id):
    """Process target list to queue"""
    if not target_list_id:
        return None
        
    target_list = TargetList.objects.get(id=target_list_id)
    queue = Queue.objects.create(
        name=f"Queue from {target_list.name}",
        source=target_list
    )
    
    return queue.id

@shared_task(
    name='crm.process_queue',
    acks_late=True
)
def process_queue(queue_id):
    """Process queue entries"""
    if not queue_id:
        return
        
    # Your queue processing logic here

# Celery Configuration Updates:
## Add to celery.py
app.conf.update(
    # Existing configs...
    
    # Task routing
    task_routes={
        'crm.fetch_leads': {'queue': 'leads'},
        'crm.process_lead_chunk': {'queue': 'leads_processing'},
        'crm.create_target_list': {'queue': 'target_lists'},
        'crm.process_*': {'queue': 'processing'},
    },
    
    # Optimization settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Prevent worker overload
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    result_expires=3600,  # Results expire in 1 hour
    
    # Add scheduled task
    beat_schedule={
        'fetch-leads': {
            'task': 'crm.fetch_leads',
            'schedule': 60.0,  # Every minute
        }
    }
)

# Docker Worker
  celery_lead_worker:
    build: .
    command: >
      celery -A konquist worker 
      -Q leads,leads_processing
      --concurrency=4
      --loglevel=INFO
      --max-tasks-per-child=1000
      --max-memory-per-child=512000
    environment:
      - CELERY_ACKS_LATE=1
      - CELERY_PREFETCH_MULTIPLIER=1
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

  celery_processing_worker:
    build: .
    command: >
      celery -A konquist worker 
      -Q target_lists,processing
      --concurrency=8
      --loglevel=INFO
      --max-tasks-per-child=1000
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G