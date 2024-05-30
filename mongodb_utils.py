from pymongo import MongoClient 

# Define MongoDB connection parameters
MongoDB_HOST = 'localhost'
MongoDB_DB_NAME = 'academicworld'


# Function to fetch data from the MongoDB localhost
def mongodb_aggregate(collection, pipeline):
    """
    Attempts to return MongoDB aggregate query and return list of dicts corresponding to documents

    Parameters:
    collection (str)        : Name of collection to query
    pipeline (list of dicts): List of MongodB operations

    Returns:
    list of dicts: Document list

    Example:
    #>>> MongoDB_aggregate("publications", [{"$match": {"year": {"$gte": 2012}}}, {"$project":
    #{ "_id": 0, "keywords.name": 1}}])
    
    Returns:
    {'keywords': [
    {'name': 'wavelet'}, 
    {'name': 'convex program'}, 
    ...
    ]},
    """

    client = MongoClient(MongoDB_HOST, 27017) # 22943
    db = client[MongoDB_DB_NAME] 
    col = db[collection]
    result = list(col.aggregate(pipeline))
    client.close()
    return result
