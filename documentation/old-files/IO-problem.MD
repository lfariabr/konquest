Your Disk IO Budget has been used up
Your workload has used up all your Disk IO Budget and is now running at the baseline performance. If you need consistent disk performance, consider upgrading to a larger compute add-on.

Disk IO Bandwidth
The disk performance of your workload is determined by the Disk IO bandwidth.

Smaller compute instances (below 4XL) can burst above their baseline disk throughput and IOPS for short periods of time. Beyond that, the performance reverts to the baseline.

1. https://supabase.com/docs/guides/platform/compute-and-disk#disk-throughput-and-iops
2. https://supabase.com/docs/guides/troubleshooting/exhaust-disk-io
3. https://supabase.com/docs/guides/telemetry/metrics

Help diagnose the problem, understand what could be happening and how to improve/fix it without the need to upgrade the project
Is there anything we can do with the queries?

### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
# SUGGESTED SOLUTION
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

### Solution Plan
1. Fix Query Patterns in Django Code
The extremely high sequential scan counts indicate poorly optimized queries. Focus on:

# In your Django models/views, look for these patterns:

# PROBLEM: Using filter without proper index
Lead.objects.filter(some_condition)

# SOLUTION: Ensure the fields in filter conditions are indexed
# Check models.py files for fields without db_index=True

# PROBLEM: N+1 query patterns
for contact in Contact.objects.all():
    do_something_with(contact.related_data)

# SOLUTION: Use select_related and prefetch_related
contacts = Contact.objects.select_related('user').prefetch_related('messages')
2. Create Missing Indexes
For apiCrm_billcharge specifically:

# Run this to identify commonly filtered fields not using indexes
SELECT
  pg_get_indexdef(indexrelid)
FROM pg_stat_user_indexes
WHERE relname = 'apiCrm_billcharge';

# Then create appropriate indexes for frequently queried fields
CREATE INDEX idx_apiCrm_billcharge_frequent_field ON apiCrm_billcharge(field_name);
3. Implement Proper Caching
Since you're using Django with Redis:

python
CopyInsert
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}

# In your view or service layer
from django.core.cache import cache

def get_expensive_data():
    cache_key = 'expensive_data_key'
    result = cache.get(cache_key)
    if not result:
        # Your expensive query here, e.g.:
        result = ApiCrmBillcharge.objects.filter(...).select_related(...)
        cache.set(cache_key, result, 3600)  # Cache for 1 hour
    return result

Where to Start?
1. Begin with the worst offender: apiCrm_billcharge - look in your codebase for queries against this table
2. Review your Django ORM usage: Find places where you're not using select_related or prefetch_related
3. Implement caching: Start caching expensive queries, especially for read-heavy operations


### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###
# Next Steps After Creating Indexes

1. Verify & Monitor Performance
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'apiCrm_billcharge';

2. Monitor Supabase dashboard over the next few days to verify disk I/O consumption has decreased.
3. Look for query improvements in app logs - operations on the BillCharge table should be faster.