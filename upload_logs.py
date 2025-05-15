import redis

# Connect to Redis Client
hostname = 'redis-18916.c83.us-east-1-2.ec2.redns.redis-cloud.com'
portnumber = 18916
password = 'vTig9W0x2XtLCyR3MDFQFyZjSMSId6Gr'

r = redis.StrictRedis(host=hostname,
                      port=portnumber,
                      password=password)

# Simulated Logs
with open('simulated_logs.txt', 'r') as f:
    logs_text = f.read()

encoded_logs = logs_text.split('\n')

# Push into Redis database
r.lpush('attendance:logs', *encoded_logs)
